"""data_generator testleri — bkz. docs/decision-log.md Phase 21.

Phase 2'de elle doğrulanan şeylerin (reproducibility, gerçekçi ilişkiler,
tip kapsamı) kalıcı testleri.
"""

from __future__ import annotations

import pandas as pd
import pytest

from data_generator.generator import generate_dataset


def test_reproducibility():
    """Aynı seed (config'teki sabit SEED=42), iki ayrı çalıştırmada birebir
    aynı veriyi üretmeli — Phase 2'nin temel garantisi."""
    d1 = generate_dataset(size="small")
    d2 = generate_dataset(size="small")
    for key in ["machines", "jobs", "operations", "energy_prices", "maintenance"]:
        pd.testing.assert_frame_equal(d1[key], d2[key])


def test_every_required_machine_type_has_a_machine():
    """Hiçbir operasyon, karşılığı olmayan bir makine tipi istememeli — aksi
    halde optimizasyon modeli o operasyon için baştan çözümsüz olur."""
    dataset = generate_dataset(size="small")
    required_types = set(dataset["operations"]["required_machine_type"].unique())
    available_types = set(dataset["machines"]["machine_type"].unique())
    assert required_types <= available_types


def test_no_deadline_before_release():
    dataset = generate_dataset(size="small")
    jobs = dataset["jobs"]
    assert (jobs["deadline"] >= jobs["release_time"]).all()


def test_processing_time_energy_correlation_positive():
    """Phase 2'nin temel kuralı: uzun süren operasyon daha çok enerji harcar."""
    dataset = generate_dataset(size="small")
    ops = dataset["operations"]
    corr = ops["processing_time"].corr(ops["energy_consumption"])
    assert corr > 0.5


def test_older_machines_have_more_maintenance_on_average():
    dataset = generate_dataset(size="small")
    machines = dataset["machines"]
    maint_machine_ids = set(dataset["maintenance"]["machine_id"])
    with_maint = machines[machines["machine_id"].isin(maint_machine_ids)]
    without_maint = machines[~machines["machine_id"].isin(maint_machine_ids)]
    if len(with_maint) and len(without_maint):
        assert with_maint["age"].mean() >= without_maint["age"].mean()


@pytest.mark.parametrize("size,expected_machines,expected_jobs", [
    ("small", 10, 50),
    ("medium", 20, 250),
    ("large", 50, 1000),
])
def test_dataset_sizes_match_config(size, expected_machines, expected_jobs):
    dataset = generate_dataset(size=size)
    assert len(dataset["machines"]) == expected_machines
    assert len(dataset["jobs"]) == expected_jobs
