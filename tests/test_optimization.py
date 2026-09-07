"""Optimizasyon modeli testleri — bkz. docs/decision-log.md Phase 21.

Minik el-hesabı örneği (tiny_dataset fixture) kullanılıyor ki testler saniyeler
içinde bitsin — SMALL/MEDIUM gibi büyük çözümler bir test suite'i için çok
yavaş (bkz. Phase 19-20 bulguları).
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from data_generator.generator import HORIZON_START
from optimization.model import build_model
from optimization.native_solver import has_feasible_solution_native, solve_native
from optimization.results import extract_schedule


def test_tiny_instance_makespan_is_correct(tiny_dataset, tiny_config):
    """Elle hesap: 2 job, paylaşılan tek CNC + tek Packaging makinesi ->
    optimal Cmax = 2.5 saat (Phase 7'de doğrulanmıştı)."""
    model, data = build_model(tiny_dataset, tiny_config, stage="makespan")
    result = solve_native(model, data, time_limit_seconds=30, warm_start_values=None)

    assert has_feasible_solution_native(result)
    assert model.Cmax.value == pytest.approx(2.5, abs=0.01)


def test_tiny_instance_shifts_to_cheap_energy_hours(tiny_dataset, tiny_config):
    """Fiyat ilk 5 saat pahalı, sonrası ucuzsa; deadline gevşekse, solver
    operasyonları ucuz döneme kaydırmalı (Phase 7'de doğrulanmıştı: 25.0)."""
    dataset = dict(tiny_dataset)
    dataset["jobs"] = tiny_dataset["jobs"].copy()
    dataset["jobs"]["deadline"] = HORIZON_START + timedelta(hours=20)
    dataset["energy_prices"] = pd.DataFrame(
        [{"timestamp": HORIZON_START + timedelta(hours=h), "price_per_kwh": (10.0 if h < 5 else 1.0)} for h in range(24)]
    )

    model, data = build_model(dataset, tiny_config, stage="energy")
    result = solve_native(model, data, time_limit_seconds=30, warm_start_values=None)

    assert has_feasible_solution_native(result)
    assert model.obj() == pytest.approx(25.0, abs=0.1)


def test_extracted_schedule_has_no_machine_overlap(tiny_dataset, tiny_config):
    model, data = build_model(tiny_dataset, tiny_config, stage="makespan")
    result = solve_native(model, data, time_limit_seconds=30, warm_start_values=None)
    assert has_feasible_solution_native(result)

    schedule = extract_schedule(model, data)
    for _, group in schedule.groupby("machine_id"):
        g = group.sort_values("start_time")
        overlaps = (g["start_time"].shift(-1) < g["end_time"]).iloc[:-1]
        assert not overlaps.any()


def test_no_eligible_machine_is_reported_infeasible_not_crashed(tiny_dataset, tiny_config):
    """Edge case (orijinal proje planı): hiçbir uygun makine olmaması.
    Tek CNC makinesini tüm ufuk boyunca bakıma alıyoruz -> CNC gerektiren
    operasyonlar planlanamaz -> model çözümsüz (infeasible) olmalı, ama
    sistem ÇÖKMEMELİ (bkz. Phase 15'teki M003 bulgusu ve düzeltmesi)."""
    dataset = dict(tiny_dataset)
    dataset["maintenance"] = pd.DataFrame(
        [
            {
                "maintenance_id": "MT_ALL",
                "machine_id": "M1",
                "start_time": HORIZON_START,
                "end_time": HORIZON_START + timedelta(hours=24),
                "maintenance_type": "emergency",
            }
        ]
    )

    model, data = build_model(dataset, tiny_config, stage="makespan")
    result = solve_native(model, data, time_limit_seconds=10, warm_start_values=None)

    assert not has_feasible_solution_native(result)


def test_zero_jobs_does_not_crash(tiny_dataset, tiny_config):
    """Edge case (orijinal proje planı): sıfır job. Model boş ama geçerli
    olmalı, hata fırlatmamalı."""
    dataset = dict(tiny_dataset)
    dataset["jobs"] = tiny_dataset["jobs"].iloc[0:0]
    dataset["operations"] = tiny_dataset["operations"].iloc[0:0]

    model, data = build_model(dataset, tiny_config, stage="makespan")
    result = solve_native(model, data, time_limit_seconds=10, warm_start_values=None)

    assert has_feasible_solution_native(result)
    assert model.Cmax.value == pytest.approx(0.0, abs=0.01)
