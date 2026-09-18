"""Backend/API smoke testleri — bkz. docs/decision-log.md.

Diğer testlerin aksine (tiny_dataset fixture, <2sn), bunlar gerçek SMALL
veri setiyle FastAPI TestClient üzerinden uçtan uca çalışır — amaç, Phase 17'de
elle/Playwright ile bulunan sınıftaki hataları (ör. JSON'a çevrilemeyen bir
enum'un response'a sızması) artık otomatik yakalamak. Bu yüzden bu dosya diğer
testlerden gözle görülür şekilde daha yavaş (gerçek bir MILP çözülüyor) —
bilinçli bir ödünleşim, `time_limit_seconds` kısa tutularak süre sınırlanıyor.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from simulation.scenarios import SCENARIOS

client = TestClient(app)


def test_overview_returns_snapshot_matching_small_preset():
    res = client.get("/api/overview?size=small")
    assert res.status_code == 200
    snapshot = res.json()["snapshot"]
    assert snapshot["total_machines"] == 10
    assert snapshot["total_jobs"] == 50
    assert snapshot["queued_jobs"] == 50


def test_baseline_returns_total_cost():
    res = client.get("/api/baseline?size=small")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cost"] > 0


def test_scenarios_lists_known_scenarios():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    assert set(res.json()["scenarios"]) == set(SCENARIOS.keys())


def test_optimize_response_is_json_serializable_and_feasible():
    """Phase 17'de bulunan hatanın regresyon testi: solve_info içindeki ham
    solver durum kodu (o zaman HighsModelStatus enum'u, JSON'a çevrilemiyordu)
    response'a hiç sızmamalı."""
    res = client.post("/api/optimize", json={"size": "small", "time_limit_seconds": 10})
    assert res.status_code == 200
    data = res.json()
    assert data["feasible"] is True
    assert "model_status" not in data["solve_info"]
    assert data["metrics"]["total_cost"] > 0
    assert isinstance(data["schedule"], list) and len(data["schedule"]) > 0


def test_optimize_rejects_unknown_scenario():
    res = client.post("/api/optimize", json={"size": "small", "scenario_name": "not_a_real_scenario"})
    assert res.status_code == 400
