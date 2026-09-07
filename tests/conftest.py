"""Ortak pytest fixture'ları — bkz. docs/decision-log.md Phase 21.

`tiny_dataset`: Phase 7-8'de modelin doğruluğunu kanıtlamak için kullanılan,
elle hesaplanabilir minik örnek (2 makine, 2 job). Cmax=2.5 olduğu elle
doğrulanmıştı — testlerde referans olarak kullanılıyor.
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from data_generator.generator import HORIZON_START


@pytest.fixture
def tiny_dataset() -> dict[str, pd.DataFrame]:
    machines = pd.DataFrame(
        [
            {
                "machine_id": "M1",
                "machine_type": "CNC",
                "capacity": 2.0,
                "status": "idle",
                "efficiency": 1.0,
                "energy_rate": 10.0,
                "age": 1,
                "available_from": HORIZON_START,
                "available_until": HORIZON_START + timedelta(hours=24),
            },
            {
                "machine_id": "M2",
                "machine_type": "Packaging",
                "capacity": 2.0,
                "status": "idle",
                "efficiency": 1.0,
                "energy_rate": 5.0,
                "age": 1,
                "available_from": HORIZON_START,
                "available_until": HORIZON_START + timedelta(hours=24),
            },
        ]
    )
    jobs = pd.DataFrame(
        [
            {
                "job_id": "J1",
                "product_type": "P",
                "quantity": 1,
                "priority": 1,
                "release_time": HORIZON_START,
                "deadline": HORIZON_START + timedelta(hours=10),
            },
            {
                "job_id": "J2",
                "product_type": "P",
                "quantity": 1,
                "priority": 1,
                "release_time": HORIZON_START,
                "deadline": HORIZON_START + timedelta(hours=10),
            },
        ]
    )
    operations = pd.DataFrame(
        [
            {"operation_id": "O1", "job_id": "J1", "sequence_no": 1, "required_machine_type": "CNC", "processing_time": 1.0, "energy_consumption": 10.0},
            {"operation_id": "O2", "job_id": "J1", "sequence_no": 2, "required_machine_type": "Packaging", "processing_time": 0.5, "energy_consumption": 2.5},
            {"operation_id": "O3", "job_id": "J2", "sequence_no": 1, "required_machine_type": "CNC", "processing_time": 1.0, "energy_consumption": 10.0},
            {"operation_id": "O4", "job_id": "J2", "sequence_no": 2, "required_machine_type": "Packaging", "processing_time": 0.5, "energy_consumption": 2.5},
        ]
    )
    maintenance = pd.DataFrame(columns=["maintenance_id", "machine_id", "start_time", "end_time", "maintenance_type"])
    energy_prices = pd.DataFrame(
        [{"timestamp": HORIZON_START + timedelta(hours=h), "price_per_kwh": 2.0} for h in range(24)]
    )
    return {
        "machines": machines,
        "jobs": jobs,
        "operations": operations,
        "maintenance": maintenance,
        "energy_prices": energy_prices,
    }


@pytest.fixture
def tiny_config() -> dict:
    return {
        "dataset": {"horizon_hours": 24},
        "optimization": {
            "big_m": 24,
            "objective_weights": {"production_time": 50, "energy_cost": 1, "tardiness": 100},
        },
    }
