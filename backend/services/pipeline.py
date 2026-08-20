"""Faz 16 — Uçtan uca döngü: Factory Data → Digital Twin → ML Predictions →
Optimization → Simulation → (opsiyonel) Scenario → Re-Optimization.

Bu modül yeni bir matematik/algoritma İÇERMEZ — önceki fazlarda ayrı ayrı
kurulmuş ve test edilmiş modülleri doğru sırayla birleştirir:

    Phase 2  (generate_dataset)      → Factory Data
    Phase 13 (DigitalTwin)           → Digital Twin State (başlangıç)
    Phase 10 (ml/prediction)         → ML Predictions
    Phase 7-9 (optimization)         → Optimization
    Phase 11 (ml/predict_optimize)   → Predict→Optimize + gerçek süreyle yeniden değerlendirme
    Phase 14 (simulation/engine)     → Simulation (planı Digital Twin üzerinde oynat)
    Phase 15 (simulation/scenarios)  → Scenario (verilirse, dataset'i dönüştürüp Re-Optimization

Bkz. docs/decision-log.md Phase 16.
"""

from __future__ import annotations

import yaml

from data_generator.generator import generate_dataset
from digital_twin.factory import DigitalTwin
from ml.predict_optimize import run_predict_optimize
from simulation.engine import SimulationEngine
from simulation.scenarios import SCENARIOS


def run_pipeline(
    size: str = "small",
    time_limit_seconds: int = 120,
    config_path: str = "config/config.yaml",
    scenario_name: str | None = None,
    scenario_kwargs: dict | None = None,
) -> dict:
    """Tüm döngüyü çalıştırır.

    `scenario_name` verilirse (bkz. `simulation.scenarios.SCENARIOS`), veri
    üretildikten HEMEN SONRA ilgili dönüşüm uygulanır ve tüm akış (ML tahmini,
    optimizasyon, simülasyon) o senaryonun dataset'i üzerinden çalışır — yani
    "re-optimization" gerçekleşir, ayrı bir kod yolu değil.

    Dönüş: {"feasible": bool, "schedule": DataFrame|None, "metrics": dict,
    "twin_snapshot": dict|None, "solve_info": dict, "scenario": str|None}
    """
    config = yaml.safe_load(open(config_path))
    horizon_hours = config["dataset"]["horizon_hours"]

    dataset = generate_dataset(size=size, config_path=config_path)

    if scenario_name is not None:
        if scenario_name not in SCENARIOS:
            raise ValueError(f"Bilinmeyen senaryo: {scenario_name!r} (seçenekler: {list(SCENARIOS)})")
        scenario_kwargs = dict(scenario_kwargs or {})
        transform = SCENARIOS[scenario_name]
        if scenario_name == "machine_failure":
            scenario_kwargs.setdefault("horizon_hours", horizon_hours)
        dataset = transform(dataset, **scenario_kwargs)

    # Digital Twin: fabrikanın senaryo/veri altındaki başlangıç durumu (t=0)
    twin = DigitalTwin(dataset, horizon_hours)

    # ML tahmini + optimizasyon + gerçek sürelerle yeniden değerlendirme (Phase 11 akışı)
    metrics, schedule, solve_info = run_predict_optimize(
        size=size, time_limit_seconds=time_limit_seconds, config_path=config_path, dataset=dataset
    )

    if not metrics.get("feasible", False):
        return {
            "feasible": False,
            "schedule": None,
            "metrics": metrics,
            "twin_snapshot": twin.snapshot(),
            "solve_info": solve_info,
            "scenario": scenario_name,
        }

    # Simulation: planı Digital Twin üzerinde zaman içinde oynat
    engine = SimulationEngine(twin, schedule, dataset)
    engine.run_all()

    return {
        "feasible": True,
        "schedule": schedule,
        "metrics": metrics,
        "twin_snapshot": twin.snapshot(),
        "solve_info": solve_info,
        "scenario": scenario_name,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Uçtan uca pipeline (Faz 16)")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small")
    parser.add_argument("--time-limit", type=int, default=120)
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()), default=None)
    parser.add_argument("--machine-id", default="M001")
    parser.add_argument("--pct-change", type=float, default=0.20)
    parser.add_argument("--hours", type=float, default=-2.0)
    args = parser.parse_args()

    scenario_kwargs = None
    if args.scenario == "machine_failure":
        scenario_kwargs = {"machine_id": args.machine_id}
    elif args.scenario in ("energy_price_change", "maintenance_duration_change"):
        scenario_kwargs = {"pct_change": args.pct_change}
    elif args.scenario == "deadline_shift":
        scenario_kwargs = {"hours": args.hours}

    result = run_pipeline(
        size=args.size,
        time_limit_seconds=args.time_limit,
        scenario_name=args.scenario,
        scenario_kwargs=scenario_kwargs,
    )

    print(f"--- Pipeline ({args.size}, senaryo: {args.scenario or 'yok'}) ---")
    print("feasible:", result["feasible"])
    print("twin_snapshot:", json.dumps(result["twin_snapshot"], indent=2, ensure_ascii=False))
    if result["feasible"]:
        print("\nmetrics:")
        for k, v in result["metrics"].items():
            print(f"  {k}: {v}")
