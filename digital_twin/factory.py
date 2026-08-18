"""Digital Twin — üst düzey arayüz. Bir dataset'ten başlangıç durumunu kurar ve
durumu sorgulama fonksiyonları sağlar — bkz. docs/decision-log.md Phase 13.

Bu fazda ZAMANI İLERLETME mantığı YOK (bu, Faz 14 — Simulation'ın işi). Burada
sadece: "fabrika t=0 anında nasıl görünür" sorusunun cevabı var — tüm makineler
boşta, tüm işler kuyrukta.
"""

from __future__ import annotations

import pandas as pd

from digital_twin.job import JobState
from digital_twin.machine import MachineState
from digital_twin.state import FactoryState


class DigitalTwin:
    def __init__(self, dataset: dict[str, pd.DataFrame], horizon_hours: int):
        self.dataset = dataset
        self.horizon_hours = horizon_hours
        self.state = self._build_initial_state()

    def _build_initial_state(self) -> FactoryState:
        machines = {
            row["machine_id"]: MachineState(machine_id=row["machine_id"], machine_type=row["machine_type"])
            for _, row in self.dataset["machines"].iterrows()
        }

        ops_per_job = self.dataset["operations"].groupby("job_id").size().to_dict()
        jobs = {
            row["job_id"]: JobState(job_id=row["job_id"], total_operations=ops_per_job.get(row["job_id"], 0))
            for _, row in self.dataset["jobs"].iterrows()
        }

        return FactoryState(horizon_hours=self.horizon_hours, machines=machines, jobs=jobs)

    def reset(self) -> None:
        """Durumu t=0'a döndürür (yeni bir simülasyon/senaryo koşusu için)."""
        self.state = self._build_initial_state()

    def snapshot(self) -> dict:
        return self.state.snapshot()
