"""Sentetik fabrika verisi üretici.

Bkz. docs/dataset.md (veri modeli) ve docs/project-plan.md Bölüm E (dataset stratejisi).

Tasarım notu (önemli modelleme kararı):
    Operation.processing_time ve Operation.energy_consumption, o operasyonun
    "nominal" (referans) değerleridir — belirli bir makineye değil, o
    required_machine_type'ın tipik/ortalama makinesine göre üretilir. Çünkü
    üretim anında (bu aşamada) hangi operasyonun hangi SPESİFİK makineye
    atanacağı henüz belli değil; buna Phase 4-9'daki optimizasyon modeli
    karar verecek. Gerçek süre, atanan makinenin `efficiency` değerine göre
    optimizasyon/simülasyon aşamasında ölçeklenir (processing_time / efficiency).

Deterministik: aynı `random_seed` (config/config.yaml) her zaman aynı
dataseti üretir — bilimsel tekrarlanabilirlik (reproducibility) için.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from data_generator.schemas import (
    EnergyPrice,
    Job,
    Machine,
    MachineStatus,
    Maintenance,
    MaintenanceType,
    Operation,
)

# --- Sabit tanımlar ---
# Şimdilik kod içinde sabit tutuluyor (Development Principle: önce basit).
# İleride gerekirse (ör. ürün çeşitliliğini deneylerde artırmak için) config.yaml'a taşınabilir.

MACHINE_TYPES = ["CNC", "Press", "Assembly", "Welding", "Packaging"]

# Her ürün tipinin hangi makine tiplerinden, hangi sırayla geçtiği (routing / rota)
PRODUCT_TEMPLATES = {
    "PRODUCT_A": ["CNC", "Welding", "Packaging"],
    "PRODUCT_B": ["Press", "Assembly", "Packaging"],
    "PRODUCT_C": ["CNC", "Assembly", "Packaging"],
    "PRODUCT_D": ["Press", "Welding", "Assembly", "Packaging"],
}

# Makine tipine göre nominal işlem süresi aralığı (saat, efficiency=1.0 referanslı)
BASE_PROCESSING_TIME_RANGE = {
    "CNC": (0.5, 2.0),
    "Press": (0.3, 1.2),
    "Assembly": (0.4, 1.5),
    "Welding": (0.6, 1.8),
    "Packaging": (0.1, 0.5),
}

# Makine tipine göre nominal enerji tüketim oranı (kWh / saat)
BASE_ENERGY_RATE_RANGE = {
    "CNC": (8, 20),
    "Press": (10, 25),
    "Assembly": (3, 8),
    "Welding": (12, 30),
    "Packaging": (2, 5),
}

# Sabit referans başlangıç tarihi — datetime.now() KULLANILMAZ, çünkü o zaman
# her çalıştırmada farklı bir tarih üretilir ve reproducibility bozulur.
HORIZON_START = datetime(2026, 1, 5, 0, 0)


def load_config(config_path: str = "config/config.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def generate_machines(rng: np.random.Generator, n_machines: int, horizon_hours: int) -> list[Machine]:
    horizon_end = HORIZON_START + timedelta(hours=horizon_hours)
    machines = []
    for i in range(n_machines):
        # ilk len(MACHINE_TYPES) makine her tipten en az bir tane garanti eder
        # (yoksa bazı required_machine_type'lar için hiç uygun makine kalmayabilir)
        if i < len(MACHINE_TYPES):
            machine_type = MACHINE_TYPES[i]
        else:
            machine_type = rng.choice(MACHINE_TYPES)

        machines.append(
            Machine(
                machine_id=f"M{i + 1:03d}",
                machine_type=machine_type,
                capacity=round(float(rng.uniform(1.0, 5.0)), 2),
                status=MachineStatus.IDLE,
                efficiency=round(float(rng.uniform(0.75, 1.0)), 3),
                energy_rate=round(float(rng.uniform(*BASE_ENERGY_RATE_RANGE[machine_type])), 2),
                age=int(rng.integers(0, 16)),
                available_from=HORIZON_START,
                available_until=horizon_end,
            )
        )
    return machines


def generate_energy_prices(rng: np.random.Generator, horizon_hours: int) -> list[EnergyPrice]:
    """Basit time-of-use (TOU) fiyat eğrisi: gece ucuz, akşam saatleri (peak) pahalı."""
    prices = []
    for h in range(horizon_hours):
        ts = HORIZON_START + timedelta(hours=h)
        hour_of_day = ts.hour
        if 17 <= hour_of_day < 22:
            base = 3.2  # peak
        elif 0 <= hour_of_day < 6:
            base = 1.4  # off-peak
        else:
            base = 2.2  # normal
        noise = rng.normal(0, 0.15)
        price = max(0.5, base + noise)
        prices.append(EnergyPrice(timestamp=ts, price_per_kwh=round(float(price), 3)))
    return prices


def generate_maintenance(rng: np.random.Generator, machines: list[Machine], horizon_hours: int) -> list[Maintenance]:
    """Yaş arttıkça bakım olasılığı artar (basit doğrusal ilişki, Phase 0'daki kural)."""
    records = []
    counter = 1
    for m in machines:
        p_maintenance = 0.15 + (m.age / 15) * 0.35  # 0.15 (yeni makine) .. 0.50 (15 yaş) arası
        if rng.random() < p_maintenance:
            start_hour = int(rng.integers(0, max(1, horizon_hours - 8)))
            duration = int(rng.integers(2, 7))
            start_time = HORIZON_START + timedelta(hours=start_hour)
            end_time = start_time + timedelta(hours=duration)
            m_type = MaintenanceType.EMERGENCY if rng.random() < 0.2 else MaintenanceType.SCHEDULED
            records.append(
                Maintenance(
                    maintenance_id=f"MT{counter:03d}",
                    machine_id=m.machine_id,
                    start_time=start_time,
                    end_time=end_time,
                    maintenance_type=m_type,
                )
            )
            counter += 1
    return records


def generate_jobs(rng: np.random.Generator, n_jobs: int, horizon_hours: int) -> list[Job]:
    jobs = []
    product_types = list(PRODUCT_TEMPLATES.keys())
    for i in range(n_jobs):
        product_type = rng.choice(product_types)
        quantity = int(rng.integers(1, 51))
        priority = int(rng.integers(1, 4))  # 1 (düşük) .. 3 (yüksek)
        release_hour = int(rng.integers(0, max(1, horizon_hours - 24)))
        release_time = HORIZON_START + timedelta(hours=release_hour)

        # nominal toplam operasyon süresine göre gevşek bir deadline
        # (bazı işler kasıtlı sıkı kalabilir — bu, Phase 3'te baseline'ın
        # bazı işleri kaçırmasını sağlayacak, yoksa karşılaştırma anlamsız olur)
        template_len = len(PRODUCT_TEMPLATES[product_type])
        estimated_hours = template_len * 1.2 * (1 + quantity / 50)
        slack_factor = rng.uniform(1.2, 3.0)
        deadline = release_time + timedelta(hours=estimated_hours * slack_factor)

        jobs.append(
            Job(
                job_id=f"J{i + 1:04d}",
                product_type=product_type,
                quantity=quantity,
                priority=priority,
                release_time=release_time,
                deadline=deadline,
            )
        )
    return jobs


def generate_operations(rng: np.random.Generator, jobs: list[Job]) -> list[Operation]:
    operations = []
    counter = 1
    for job in jobs:
        template = PRODUCT_TEMPLATES[job.product_type]
        for seq_no, machine_type in enumerate(template, start=1):
            base_low, base_high = BASE_PROCESSING_TIME_RANGE[machine_type]
            base_time = rng.uniform(base_low, base_high)
            quantity_factor = 1 + (job.quantity / 100)  # miktar arttıkça süre biraz artar
            noise = rng.normal(1.0, 0.05)
            processing_time = max(0.05, base_time * quantity_factor * noise)

            energy_low, energy_high = BASE_ENERGY_RATE_RANGE[machine_type]
            reference_energy_rate = (energy_low + energy_high) / 2
            energy_noise = rng.normal(1.0, 0.08)
            # kural: süre uzadıkça enerji de artar (processing_time'a doğrudan bağlı)
            energy_consumption = max(0.01, processing_time * reference_energy_rate * energy_noise)

            operations.append(
                Operation(
                    operation_id=f"OP{counter:05d}",
                    job_id=job.job_id,
                    sequence_no=seq_no,
                    required_machine_type=machine_type,
                    processing_time=round(float(processing_time), 3),
                    energy_consumption=round(float(energy_consumption), 3),
                )
            )
            counter += 1
    return operations


def _records_to_df(records: list) -> pd.DataFrame:
    """Dataclass listesini pandas DataFrame'e çevirir; Enum alanları .value'ya indirger."""
    rows = []
    for r in records:
        row = asdict(r)
        for k, v in row.items():
            if isinstance(v, Enum):
                row[k] = v.value
        rows.append(row)
    return pd.DataFrame(rows)


def generate_dataset(size: str = "small", config_path: str = "config/config.yaml") -> dict[str, pd.DataFrame]:
    config = load_config(config_path)
    seed = config["random_seed"]
    preset = config["dataset"]["presets"][size]
    horizon_hours = config["dataset"]["horizon_hours"]

    rng = _rng(seed)

    machines = generate_machines(rng, preset["machines"], horizon_hours)
    energy_prices = generate_energy_prices(rng, horizon_hours)
    maintenance = generate_maintenance(rng, machines, horizon_hours)
    jobs = generate_jobs(rng, preset["jobs"], horizon_hours)
    operations = generate_operations(rng, jobs)

    return {
        "machines": _records_to_df(machines),
        "jobs": _records_to_df(jobs),
        "operations": _records_to_df(operations),
        "energy_prices": _records_to_df(energy_prices),
        "maintenance": _records_to_df(maintenance),
    }


def save_dataset(dataset: dict[str, pd.DataFrame], size: str, output_dir: str = "data/synthetic") -> None:
    out_path = Path(output_dir) / size
    out_path.mkdir(parents=True, exist_ok=True)
    for name, df in dataset.items():
        df.to_csv(out_path / f"{name}.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentetik fabrika verisi üretici")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small")
    args = parser.parse_args()

    dataset = generate_dataset(size=args.size)
    save_dataset(dataset, size=args.size)
    for name, df in dataset.items():
        print(f"{name}: {len(df)} kayıt üretildi")
