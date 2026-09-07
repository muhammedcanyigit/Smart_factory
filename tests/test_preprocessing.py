"""preprocessing.cleaning testleri — bkz. docs/decision-log.md Phase 22."""

from __future__ import annotations

import pandas as pd

from data_generator.generator import generate_dataset
from preprocessing.cleaning import clean_dataset, clean_operations


def test_clean_dataset_is_noop_on_already_clean_synthetic_data():
    """Phase 2'nin ürettiği veri zaten temiz olmalı — temizleme hiçbir satırı
    kaldırmamalı, rapor boş olmalı."""
    dataset = generate_dataset(size="small")
    cleaned, report = clean_dataset(dataset)

    assert len(cleaned["operations"]) == len(dataset["operations"])
    assert report == []


def test_clean_operations_removes_duplicates_and_missing_values():
    dirty = pd.DataFrame(
        [
            {"operation_id": "O1", "job_id": "J1", "required_machine_type": "CNC", "processing_time": 1.0, "energy_consumption": 5.0},
            {"operation_id": "O1", "job_id": "J1", "required_machine_type": "CNC", "processing_time": 1.0, "energy_consumption": 5.0},  # yinelenen
            {"operation_id": "O2", "job_id": "J2", "required_machine_type": None, "processing_time": 1.0, "energy_consumption": 5.0},  # eksik
        ]
    )
    cleaned, report = clean_operations(dirty)

    assert len(cleaned) == 1
    assert len(report) == 2


def test_clean_operations_fixes_invalid_values():
    dirty = pd.DataFrame(
        [
            {"operation_id": "O1", "job_id": "J1", "required_machine_type": "CNC", "processing_time": -1.0, "energy_consumption": 5.0},
            {"operation_id": "O2", "job_id": "J2", "required_machine_type": "CNC", "processing_time": 1.0, "energy_consumption": -3.0},
        ]
    )
    cleaned, report = clean_operations(dirty)

    assert len(cleaned) == 1  # negatif süreli satır tamamen kaldırıldı
    assert (cleaned["energy_consumption"] >= 0).all()  # negatif enerji kırpıldı
    assert len(report) == 2
