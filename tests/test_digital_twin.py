"""Digital Twin testleri — bkz. docs/decision-log.md Phase 21 (Phase 13'ün
manuel doğrulamalarının kalıcı hali)."""

from __future__ import annotations

from data_generator.generator import generate_dataset
from digital_twin.factory import DigitalTwin

HORIZON_HOURS = 168


def test_initial_state_matches_dataset():
    dataset = generate_dataset(size="small")
    twin = DigitalTwin(dataset, HORIZON_HOURS)
    snapshot = twin.snapshot()

    assert snapshot["total_machines"] == len(dataset["machines"])
    assert snapshot["total_jobs"] == len(dataset["jobs"])
    assert snapshot["idle_machines"] == len(dataset["machines"])
    assert snapshot["queued_jobs"] == len(dataset["jobs"])
    assert snapshot["completed_jobs"] == 0
    assert snapshot["running_jobs"] == 0
    assert snapshot["total_energy_kwh"] == 0.0


def test_reset_returns_to_initial_state():
    dataset = generate_dataset(size="small")
    twin = DigitalTwin(dataset, HORIZON_HOURS)
    initial_snapshot = twin.snapshot()

    twin.state.current_time = 42.0
    twin.state.total_energy_kwh = 999.0

    twin.reset()
    assert twin.snapshot() == initial_snapshot
