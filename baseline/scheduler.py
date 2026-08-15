"""Baseline üretim planlayıcı — optimizasyon kullanmaz, FCFS/EDF kuralıyla çalışır.

Amaç: Phase 4+ optimizasyon modelinin gerçekten fayda sağladığını gösterebilmek
için bir referans (kıyas) noktası oluşturmak. Bkz. docs/project-plan.md Phase 3.

Algoritma: her job için, sırayla operasyonlarını uygun makine tiplerinden birine
greedy (açgözlü) şekilde atar — o operasyon için en erken başlayabilecek uygun
makineyi seçer, geleceği hesaba katmaz. Bakım (maintenance) çakışmasına saygı
gösterir; machine.available_from/until penceresi şimdilik zorlanmıyor (mevcut
sentetik veride tüm makinelerde aynı ve bilgi taşımıyor — Phase 5'te gerçek bir
kısıt olarak ele alınacak).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from data_generator.generator import HORIZON_START, generate_dataset


def _prepare(dataset: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Tarih/saat sütunlarını datetime tipine çevirir (CSV'den okunduğunda string kalırlar)."""
    ds = {k: v.copy() for k, v in dataset.items()}
    ds["jobs"]["release_time"] = pd.to_datetime(ds["jobs"]["release_time"])
    ds["jobs"]["deadline"] = pd.to_datetime(ds["jobs"]["deadline"])
    ds["machines"]["available_from"] = pd.to_datetime(ds["machines"]["available_from"])
    ds["machines"]["available_until"] = pd.to_datetime(ds["machines"]["available_until"])
    if not ds["maintenance"].empty:
        ds["maintenance"]["start_time"] = pd.to_datetime(ds["maintenance"]["start_time"])
        ds["maintenance"]["end_time"] = pd.to_datetime(ds["maintenance"]["end_time"])
    return ds


def run_baseline(dataset: dict[str, pd.DataFrame], strategy: str = "fcfs") -> pd.DataFrame:
    """FCFS veya EDF stratejisiyle bir üretim planı (schedule) üretir.

    Dönüş: operation_id, job_id, machine_id, sequence_no, start_time, end_time,
    energy_consumption kolonlarını içeren bir DataFrame.
    """
    ds = _prepare(dataset)
    machines = ds["machines"]
    jobs = ds["jobs"]
    operations = ds["operations"]
    maintenance = ds["maintenance"]

    if strategy == "fcfs":
        job_order = jobs.sort_values(["release_time", "job_id"])["job_id"].tolist()
    elif strategy == "edf":
        job_order = jobs.sort_values(["deadline", "job_id"])["job_id"].tolist()
    else:
        raise ValueError(f"Bilinmeyen strateji: {strategy!r} (fcfs veya edf olmalı)")

    jobs_by_id = jobs.set_index("job_id")
    machine_type_map = machines.groupby("machine_type")["machine_id"].apply(list).to_dict()
    machine_efficiency = dict(zip(machines["machine_id"], machines["efficiency"]))
    machine_next_free = dict(zip(machines["machine_id"], machines["available_from"]))

    maint_by_machine: dict[str, list[tuple[pd.Timestamp, pd.Timestamp]]] = {m: [] for m in machines["machine_id"]}
    for _, row in maintenance.iterrows():
        maint_by_machine[row["machine_id"]].append((row["start_time"], row["end_time"]))

    schedule_rows = []

    for job_id in job_order:
        job = jobs_by_id.loc[job_id]
        job_ready = job["release_time"]
        job_ops = operations[operations["job_id"] == job_id].sort_values("sequence_no")

        for _, op in job_ops.iterrows():
            candidates = machine_type_map.get(op["required_machine_type"], [])
            if not candidates:
                raise ValueError(f"'{op['required_machine_type']}' tipinde hiç makine yok — dataset tutarsız")

            best_machine = None
            best_start = None
            for m in sorted(candidates):
                earliest = max(job_ready, machine_next_free[m])
                duration = op["processing_time"] / machine_efficiency[m]
                # bakım penceresiyle çakışıyorsa, bakım bitene kadar it (birden fazla çakışma olabilir)
                changed = True
                while changed:
                    changed = False
                    prospective_end = earliest + pd.Timedelta(hours=duration)
                    for ms, me in maint_by_machine[m]:
                        if earliest < me and prospective_end > ms:
                            earliest = me
                            prospective_end = earliest + pd.Timedelta(hours=duration)
                            changed = True
                if best_start is None or earliest < best_start:
                    best_start = earliest
                    best_machine = m

            duration = op["processing_time"] / machine_efficiency[best_machine]
            end_time = best_start + pd.Timedelta(hours=duration)

            schedule_rows.append(
                {
                    "operation_id": op["operation_id"],
                    "job_id": job_id,
                    "machine_id": best_machine,
                    "sequence_no": op["sequence_no"],
                    "start_time": best_start,
                    "end_time": end_time,
                    "energy_consumption": op["energy_consumption"],
                }
            )

            machine_next_free[best_machine] = end_time
            job_ready = end_time

    return pd.DataFrame(schedule_rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline üretim planlayıcı (FCFS/EDF)")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small")
    parser.add_argument("--strategy", choices=["fcfs", "edf"], default="fcfs")
    args = parser.parse_args()

    from baseline.metrics import summarize

    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)
    horizon_hours = config["dataset"]["horizon_hours"]

    dataset = generate_dataset(size=args.size)
    schedule = run_baseline(dataset, strategy=args.strategy)
    metrics = summarize(schedule, dataset, horizon_hours)

    print(f"--- Baseline ({args.strategy.upper()}, {args.size}) ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    out_dir = Path("experiments/baseline")
    out_dir.mkdir(parents=True, exist_ok=True)
    schedule.to_csv(out_dir / f"schedule_{args.strategy}_{args.size}.csv", index=False)
