"""Üretim planı (schedule) için metrik hesaplama fonksiyonları.

Bu fonksiyonlar hem baseline (Phase 3) hem de optimize edilmiş plan (Phase 9,
baseline vs optimized karşılaştırması) için aynı şekilde kullanılacak — böylece
iki plan gerçekten aynı ölçütle kıyaslanır.
"""

from __future__ import annotations

import pandas as pd

from data_generator.generator import HORIZON_START


def compute_makespan(schedule: pd.DataFrame) -> float:
    """Toplam üretim süresi (saat): planlama ufkunun başlangıcından, en son biten
    operasyonun bitişine kadar geçen süre."""
    if schedule.empty:
        return 0.0
    return (schedule["end_time"].max() - HORIZON_START).total_seconds() / 3600


def compute_tardiness(schedule: pd.DataFrame, jobs: pd.DataFrame) -> pd.DataFrame:
    """Her job için tardiness (gecikme, saat) hesaplar. Geç değilse 0."""
    jobs = jobs.copy()
    jobs["deadline"] = pd.to_datetime(jobs["deadline"])
    completion = schedule.groupby("job_id")["end_time"].max().rename("completion_time")
    result = jobs.set_index("job_id")[["deadline"]].join(completion)
    result["tardiness_hours"] = (
        (result["completion_time"] - result["deadline"]).dt.total_seconds() / 3600
    ).clip(lower=0)
    return result


def compute_energy_cost(schedule: pd.DataFrame, prices: pd.DataFrame) -> float:
    """Toplam enerji maliyeti: her operasyonun enerjisi × başladığı saatteki birim fiyat.

    Basitleştirme: birkaç saat süren bir operasyon için, sadece başlangıç saatindeki
    fiyat kullanılıyor (saat başına kırılıp ağırlıklandırma yapılmıyor). Bu bilinçli
    bir sadeleştirme — gerekirse ileride (Phase 6 objective'de) hassaslaştırılabilir.
    """
    prices = prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"])
    price_by_hour = prices.set_index(prices["timestamp"].dt.floor("h"))["price_per_kwh"]

    hour_key = schedule["start_time"].dt.floor("h")
    unit_price = hour_key.map(price_by_hour)
    return float((schedule["energy_consumption"] * unit_price).sum())


def compute_utilization(schedule: pd.DataFrame, machines: pd.DataFrame, horizon_hours: int) -> pd.DataFrame:
    """Her makine için kullanım oranı (%): meşgul olduğu süre / toplam planlama ufku."""
    if schedule.empty:
        busy_by_machine = pd.Series(dtype=float)
    else:
        busy_hours = (schedule["end_time"] - schedule["start_time"]).dt.total_seconds() / 3600
        busy_by_machine = schedule.assign(busy_hours=busy_hours).groupby("machine_id")["busy_hours"].sum()

    result = machines[["machine_id"]].set_index("machine_id")
    result["utilization"] = (busy_by_machine / horizon_hours).clip(upper=1.0)
    result["utilization"] = result["utilization"].fillna(0.0)
    return result


def summarize(schedule: pd.DataFrame, dataset: dict[str, pd.DataFrame], horizon_hours: int) -> dict:
    """Phase 9'da baseline-vs-optimized karşılaştırmasında kullanılacak özet metrikler."""
    tardiness_df = compute_tardiness(schedule, dataset["jobs"])
    utilization_df = compute_utilization(schedule, dataset["machines"], horizon_hours)

    return {
        "production_time_hours": round(compute_makespan(schedule), 2),
        "energy_cost": round(compute_energy_cost(schedule, dataset["energy_prices"]), 2),
        "late_jobs": int((tardiness_df["tardiness_hours"] > 0).sum()),
        "total_jobs": int(len(dataset["jobs"])),
        "avg_tardiness_hours": round(float(tardiness_df["tardiness_hours"].mean()), 2),
        "avg_machine_utilization": round(float(utilization_df["utilization"].mean()), 3),
    }
