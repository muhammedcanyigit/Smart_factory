"""Phase 11 — Predict → Optimize entegrasyonu.

Akış:
    1. Phase 10'da eğitilen ML modeli, her operasyonun işlem süresini tahmin eder.
    2. Optimizasyon modeli bu TAHMİNİ sürelerle kurulur ve çözülür — bu bize bir
       makine ataması + sıra kararı verir (ve tahmine göre bir zamanlama).
    3. Bu atama+sıra kararı SABİT tutulup, GERÇEK (ground-truth) sürelerle
       yeniden zamanlanır (`optimization/replay.py`) — "planı gerçek hayatta
       çalıştırsak ne olurdu" sorusunun cevabı budur.

Böylece ML tahmin hatasının, nihai plan kalitesine ne kadar yansıdığı ölçülür.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import pyomo.environ as pyo
import yaml

from baseline.metrics import summarize
from baseline.scheduler import run_baseline
from data_generator.generator import HORIZON_START, generate_dataset
from ml.prediction import load_model
from ml.training import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from optimization.comparison import compute_total_cost
from optimization.model import build_model
from optimization.replay import build_maintenance_lookup, replay_schedule
from optimization.solver import solve_with_warm_start
from preprocessing.features import build_feature_table


def predict_processing_times(ml_model, dataset: dict) -> pd.DataFrame:
    """operations tablosunun bir kopyasını, processing_time yerine ML tahminiyle döner."""
    feature_table = build_feature_table(dataset)
    X = feature_table[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    predicted = ml_model.predict(X).clip(min=0.01)  # negatif/sıfır tahmine karşı güvenlik

    operations_predicted = dataset["operations"].copy()
    operations_predicted["processing_time"] = predicted
    return operations_predicted


def extract_assignment_and_predicted_order(model: pyo.ConcreteModel, data: dict):
    assigned_machine = {}
    for o in data["O"]:
        for m in data["eligible_om"][o]:
            if pyo.value(model.x[o, m]) > 0.5:
                assigned_machine[o] = m
                break
    predicted_start = {o: pyo.value(model.S[o]) for o in data["O"]}
    order = sorted(data["O"], key=lambda o: predicted_start[o])
    return assigned_machine, order


def replay_with_ground_truth(assigned_machine: dict, order: list, dataset: dict, data: dict) -> pd.DataFrame:
    """Bilinen sınırlama: bu replay, bakım pencerelerini yeniden kontrol etmiyor
    (Phase 3'teki ilk baseline'daki gibi bir basitleştirme) — gerçek süre
    tahminden belirgin saparsa teorik olarak bir bakım penceresine denk
    gelebilir. Tam ele alınması Phase 14 (Simulation) kapsamında."""
    ground_truth_p = dict(zip(dataset["operations"]["operation_id"], dataset["operations"]["processing_time"]))
    ground_truth_e = dict(zip(dataset["operations"]["operation_id"], dataset["operations"]["energy_consumption"]))
    op_seq = dict(zip(dataset["operations"]["operation_id"], dataset["operations"]["sequence_no"]))

    S, C = replay_schedule(
        assigned_machine=assigned_machine,
        order=order,
        op_job=data["op_job"],
        release=data["release"],
        durations=ground_truth_p,
        eff=data["eff"],
        maintenance_by_machine=build_maintenance_lookup(data["maint_list"]),
    )

    rows = [
        {
            "operation_id": o,
            "job_id": data["op_job"][o],
            "machine_id": assigned_machine[o],
            "sequence_no": op_seq[o],
            "start_time": HORIZON_START + pd.Timedelta(hours=S[o]),
            "end_time": HORIZON_START + pd.Timedelta(hours=C[o]),
            "energy_consumption": ground_truth_e[o],
        }
        for o in order
    ]
    return pd.DataFrame(rows).sort_values(["job_id", "sequence_no"]).reset_index(drop=True)


def run_predict_optimize(size: str = "small", time_limit_seconds: int = 120, config_path: str = "config/config.yaml"):
    config = yaml.safe_load(open(config_path))
    horizon_hours = config["dataset"]["horizon_hours"]
    weights = config["optimization"]["objective_weights"]

    dataset = generate_dataset(size=size, config_path=config_path)
    ml_model = load_model(f"ml/models/processing_time_{size}.joblib")
    operations_predicted = predict_processing_times(ml_model, dataset)

    dataset_predicted = dict(dataset)
    dataset_predicted["operations"] = operations_predicted

    fcfs_schedule = run_baseline(dataset, strategy="fcfs")  # warm-start için (gerçek veriyle, yapısal)

    model, data = build_model(dataset_predicted, config, stage="final")
    solve_info = solve_with_warm_start(model, data, fcfs_schedule, time_limit_seconds=time_limit_seconds)

    assigned_machine, order = extract_assignment_and_predicted_order(model, data)
    actual_schedule = replay_with_ground_truth(assigned_machine, order, dataset, data)

    actual_metrics = summarize(actual_schedule, dataset, horizon_hours)
    actual_metrics["total_cost"] = round(compute_total_cost(actual_schedule, dataset, horizon_hours, weights), 2)
    actual_metrics["solver_status"] = solve_info.get("model_status_str")
    actual_metrics["solver_gap_pct"] = round(100 * (solve_info.get("mip_gap") or 0), 2)

    return actual_metrics, actual_schedule, solve_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict -> Optimize -> gerçek süreyle yeniden değerlendir")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small")
    parser.add_argument("--time-limit", type=int, default=120)
    args = parser.parse_args()

    metrics, schedule, solve_info = run_predict_optimize(size=args.size, time_limit_seconds=args.time_limit)

    print(f"--- Predict->Optimize, GERÇEK sürelerle değerlendirildi ({args.size}) ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    out_dir = Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"predict_optimize_{args.size}.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    schedule.to_csv(out_dir / f"predict_optimize_schedule_{args.size}.csv", index=False)
