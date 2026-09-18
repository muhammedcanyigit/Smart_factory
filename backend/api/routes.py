"""Dashboard API uç noktaları — bkz. docs/decision-log.md Phase 17.

Bu dosya yeni bir iş mantığı İÇERMEZ — sadece önceki fazlarda kurulan
fonksiyonları (Digital Twin, baseline, pipeline) HTTP üzerinden erişilebilir
hale getirir.
"""

from __future__ import annotations

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.pipeline import run_pipeline
from baseline.metrics import summarize
from baseline.scheduler import run_baseline
from data_generator.generator import generate_dataset
from digital_twin.factory import DigitalTwin
from simulation.scenarios import SCENARIOS

router = APIRouter()
CONFIG_PATH = "config/config.yaml"
VALID_SIZES = {"small", "medium", "large"}


def _config() -> dict:
    return yaml.safe_load(open(CONFIG_PATH))


def _validate_size(size: str) -> None:
    if size not in VALID_SIZES:
        raise HTTPException(400, f"Bilinmeyen dataset boyutu: {size!r} (seçenekler: {sorted(VALID_SIZES)})")


@router.get("/overview")
def get_overview(size: str = "small"):
    _validate_size(size)
    try:
        config = _config()
        horizon_hours = config["dataset"]["horizon_hours"]
        dataset = generate_dataset(size=size, config_path=CONFIG_PATH)
        twin = DigitalTwin(dataset, horizon_hours)
        return {"size": size, "snapshot": twin.snapshot()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Fabrika durumu okunurken hata oluştu: {exc}") from exc


@router.get("/baseline")
def get_baseline(size: str = "small"):
    _validate_size(size)
    try:
        config = _config()
        horizon_hours = config["dataset"]["horizon_hours"]
        dataset = generate_dataset(size=size, config_path=CONFIG_PATH)
        fcfs_schedule = run_baseline(dataset, strategy="fcfs")
        metrics = summarize(fcfs_schedule, dataset, horizon_hours)

        from optimization.comparison import compute_total_cost

        weights = config["optimization"]["objective_weights"]
        metrics["total_cost"] = round(compute_total_cost(fcfs_schedule, dataset, horizon_hours, weights), 2)
        return metrics
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Baseline hesaplanırken hata oluştu: {exc}") from exc


@router.get("/scenarios")
def get_scenarios():
    return {"scenarios": list(SCENARIOS.keys())}


class OptimizeRequest(BaseModel):
    size: str = "small"
    time_limit_seconds: int = 60
    scenario_name: str | None = None
    scenario_kwargs: dict | None = None


@router.post("/optimize")
def optimize(req: OptimizeRequest):
    _validate_size(req.size)
    if req.scenario_name and req.scenario_name not in SCENARIOS:
        raise HTTPException(400, f"Bilinmeyen senaryo: {req.scenario_name}")

    try:
        result = run_pipeline(
            size=req.size,
            time_limit_seconds=req.time_limit_seconds,
            scenario_name=req.scenario_name,
            scenario_kwargs=req.scenario_kwargs,
        )
    except Exception as exc:
        # Beklenmeyen bir hata (ör. eksik bir bağımlılık, bozuk bir senaryo
        # parametresi) çıplak bir 500/stack trace olarak sızmasın diye burada
        # yakalanıp okunabilir bir mesaja çevriliyor — frontend bunu
        # `detail` alanından okuyup gösterebilir (bkz. docs/decision-log.md).
        raise HTTPException(500, f"Optimizasyon çalıştırılırken hata oluştu: {exc}") from exc

    schedule = result.get("schedule")
    result["schedule"] = schedule.to_dict(orient="records") if schedule is not None else None
    # solve_info içindeki ham durum kodu (Gurobi'de int, ama HiGHS aktifken bir
    # HighsModelStatus enum'uydu ve JSON'a çevrilemiyordu — bkz. Phase 17) burada
    # zaten çıkarılıyor; aynı bilginin okunabilir hali solver_status/
    # model_status_str'de var. Pop işlemi, HiGHS'e geri dönülürse yeniden bir
    # JSON serialization hatası çıkmasın diye kasıtlı olarak korunuyor.
    if result.get("solve_info"):
        result["solve_info"].pop("model_status", None)
    return result
