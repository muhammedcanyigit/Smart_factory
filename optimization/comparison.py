"""Phase 9 — Baseline (FCFS/EDF) vs Optimized karşılaştırması.

Phase 8'in bulgusu gereği (bkz. docs/decision-log.md): makespan'de baseline
zaten optimale çok yakın, bu yüzden karşılaştırma "final" (birleşik $) hedefiyle
yapılıyor — yoksa "optimizasyonun faydası yok" gibi yanlış bir sonuca varılır.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from baseline.metrics import compute_energy_cost, compute_makespan, compute_tardiness, summarize
from baseline.scheduler import run_baseline
from data_generator.generator import generate_dataset
from optimization.model import build_model
from optimization.results import extract_schedule
from optimization.solver import solve_with_warm_start


def compute_total_cost(schedule: pd.DataFrame, dataset: dict, horizon_hours: int, weights: dict) -> float:
    """Aynı $ formülü (Bölüm 6.3): Z = c_time*Cmax + EnergyCost + c_tardy*sum(T[j])."""
    makespan = compute_makespan(schedule)
    energy_cost = compute_energy_cost(schedule, dataset["energy_prices"])
    tardiness_df = compute_tardiness(schedule, dataset["jobs"])
    total_tardiness = tardiness_df["tardiness_hours"].sum()
    return (
        weights["production_time"] * makespan
        + weights["energy_cost"] * energy_cost
        + weights["tardiness"] * total_tardiness
    )


def run_comparison(
    size: str = "small",
    time_limit_seconds: int = 120,
    config_path: str = "config/config.yaml",
    dataset: dict | None = None,
):
    """`dataset` verilmezse (normal kullanım) size'a göre yeniden üretilir.
    Verilirse (ör. Phase 15 what-if senaryoları) doğrudan o kullanılır — böylece
    senaryolu bir dataset üzerinde de aynı karşılaştırma altyapısı çalışabilir."""
    config = yaml.safe_load(open(config_path))
    horizon_hours = config["dataset"]["horizon_hours"]
    weights = config["optimization"]["objective_weights"]

    if dataset is None:
        dataset = generate_dataset(size=size, config_path=config_path)

    fcfs_schedule = run_baseline(dataset, strategy="fcfs")
    edf_schedule = run_baseline(dataset, strategy="edf")

    model, data = build_model(dataset, config, stage="final")
    solve_info = solve_with_warm_start(model, data, fcfs_schedule, time_limit_seconds=time_limit_seconds)

    from optimization.native_solver import has_feasible_solution_native

    if not has_feasible_solution_native(solve_info):
        # Gerçek, önemli bir durum — gizlenmiyor: bazı senaryolarda (ör. tek bir
        # makine tipinin tek örneği tüm ufuk boyunca kullanılamaz hale gelirse)
        # model matematiksel olarak çözümsüz (infeasible) olabilir. Bkz.
        # docs/decision-log.md Phase 15.
        metrics = {
            "FCFS": summarize(fcfs_schedule, dataset, horizon_hours),
            "EDF": summarize(edf_schedule, dataset, horizon_hours),
            "Optimized": {"feasible": False, "solver_status": solve_info.get("model_status_str")},
        }
        for name, sched in (("FCFS", fcfs_schedule), ("EDF", edf_schedule)):
            metrics[name]["total_cost"] = round(compute_total_cost(sched, dataset, horizon_hours, weights), 2)
        schedules = {"FCFS": fcfs_schedule, "EDF": edf_schedule, "Optimized": None}
        return metrics, schedules

    opt_schedule = extract_schedule(model, data)

    schedules = {"FCFS": fcfs_schedule, "EDF": edf_schedule, "Optimized": opt_schedule}
    metrics = {name: summarize(sched, dataset, horizon_hours) for name, sched in schedules.items()}
    for name, sched in schedules.items():
        metrics[name]["total_cost"] = round(compute_total_cost(sched, dataset, horizon_hours, weights), 2)

    metrics["Optimized"]["solver_status"] = solve_info.get("model_status_str")
    metrics["Optimized"]["solver_gap_pct"] = round(100 * (solve_info.get("mip_gap") or 0), 2)

    return metrics, schedules


def print_comparison_table(metrics: dict) -> None:
    if metrics["Optimized"].get("feasible") is False:
        print(f"Optimizasyon ÇÖZÜMSÜZ (infeasible) — durum: {metrics['Optimized']['solver_status']}")
        print("Bu, verilen kısıtlar altında hiçbir geçerli plan olmadığı anlamına gelir (ör. bir makine tipinin tek örneği tamamen kullanılamaz hale gelmiş olabilir).")
        return

    fcfs_cost = metrics["FCFS"]["total_cost"]
    opt_cost = metrics["Optimized"]["total_cost"]
    improvement = 100 * (fcfs_cost - opt_cost) / fcfs_cost if fcfs_cost else 0.0

    rows = [
        ("Production Time (h)", "production_time_hours"),
        ("Energy Cost ($)", "energy_cost"),
        ("Late Jobs", "late_jobs"),
        ("Avg Tardiness (h)", "avg_tardiness_hours"),
        ("Avg Machine Utilization", "avg_machine_utilization"),
        ("Total Cost ($, weighted)", "total_cost"),
    ]
    header = f"{'Metric':<28}{'FCFS':>14}{'EDF':>14}{'Optimized':>14}"
    print(header)
    print("-" * len(header))
    for label, key in rows:
        print(f"{label:<28}{metrics['FCFS'][key]:>14}{metrics['EDF'][key]:>14}{metrics['Optimized'][key]:>14}")
    print("-" * len(header))
    print(f"\nOptimized vs FCFS toplam maliyet iyileşmesi: %{improvement:.2f}")
    print(f"Solver durumu: {metrics['Optimized']['solver_status']} (gap: %{metrics['Optimized']['solver_gap_pct']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline vs Optimized karşılaştırması")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small")
    parser.add_argument("--time-limit", type=int, default=120)
    args = parser.parse_args()

    metrics, schedules = run_comparison(size=args.size, time_limit_seconds=args.time_limit)
    print_comparison_table(metrics)

    out_dir = Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"comparison_{args.size}.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    schedules["Optimized"].to_csv(out_dir / f"optimized_schedule_{args.size}.csv", index=False)
