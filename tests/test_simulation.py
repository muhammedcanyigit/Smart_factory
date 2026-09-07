"""Simülasyon motoru testleri — bkz. docs/decision-log.md Phase 21.

Phase 14'teki çapraz doğrulamanın (simülasyon sonucu == bağımsız metrik
hesaplaması) kalıcı testi.
"""

from __future__ import annotations

from data_generator.generator import generate_dataset
from baseline.metrics import summarize
from baseline.scheduler import run_baseline
from digital_twin.factory import DigitalTwin
from simulation.engine import SimulationEngine

HORIZON_HOURS = 168


def test_simulation_matches_independent_baseline_metrics():
    dataset = generate_dataset(size="small")
    schedule = run_baseline(dataset, strategy="fcfs")
    baseline_metrics = summarize(schedule, dataset, HORIZON_HOURS)

    twin = DigitalTwin(dataset, HORIZON_HOURS)
    engine = SimulationEngine(twin, schedule, dataset)
    engine.run_all()
    snapshot = twin.snapshot()

    assert snapshot["delayed_jobs"] == baseline_metrics["late_jobs"]
    assert snapshot["total_energy_cost"] == baseline_metrics["energy_cost"]


def test_all_jobs_finish_after_run_all():
    dataset = generate_dataset(size="small")
    schedule = run_baseline(dataset, strategy="fcfs")

    twin = DigitalTwin(dataset, HORIZON_HOURS)
    engine = SimulationEngine(twin, schedule, dataset)
    engine.run_all()
    snapshot = twin.snapshot()

    assert snapshot["queued_jobs"] == 0
    assert snapshot["running_jobs"] == 0
    assert snapshot["completed_jobs"] + snapshot["delayed_jobs"] == snapshot["total_jobs"]
