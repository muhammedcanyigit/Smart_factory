"""Discrete-event simülasyon motoru — bir üretim planını (baseline veya
optimize edilmiş) Digital Twin üzerinde zaman içinde "oynatır".
Bkz. docs/decision-log.md Phase 14.

Enerji maliyeti, operasyonun BAŞLANGIÇ saatindeki fiyatla hesaplanır — bu,
baseline/metrics.py::compute_energy_cost ve optimization'daki w[o,t]
mekanizmasıyla aynı kural, tutarlılık için (bkz. Phase 6 kararı).
"""

from __future__ import annotations

import pandas as pd

from data_generator.generator import HORIZON_START
from digital_twin.factory import DigitalTwin
from digital_twin.job import JobStatus
from digital_twin.machine import MachineStatus
from simulation.events import Event, EventType


def _to_hours(ts) -> float:
    return (pd.Timestamp(ts) - HORIZON_START).total_seconds() / 3600


class SimulationEngine:
    def __init__(self, twin: DigitalTwin, schedule: pd.DataFrame, dataset: dict):
        self.twin = twin
        self.dataset = dataset
        self.schedule = schedule
        self.deadlines = {row["job_id"]: _to_hours(row["deadline"]) for _, row in dataset["jobs"].iterrows()}
        self.price_by_hour = self._build_price_lookup()
        self.events = self._build_event_queue()
        self._cursor = 0
        self._op_start_time: dict[str, float] = {}

    def _build_price_lookup(self) -> dict[int, float]:
        prices = self.dataset["energy_prices"]
        return {int(_to_hours(row["timestamp"])): row["price_per_kwh"] for _, row in prices.iterrows()}

    def _build_event_queue(self) -> list[Event]:
        events: list[Event] = []
        for _, row in self.schedule.iterrows():
            events.append(
                Event(
                    time=_to_hours(row["start_time"]),
                    event_type=EventType.OPERATION_START,
                    machine_id=row["machine_id"],
                    operation_id=row["operation_id"],
                    job_id=row["job_id"],
                )
            )
            events.append(
                Event(
                    time=_to_hours(row["end_time"]),
                    event_type=EventType.OPERATION_END,
                    machine_id=row["machine_id"],
                    operation_id=row["operation_id"],
                    job_id=row["job_id"],
                    energy_consumption=row["energy_consumption"],
                )
            )

        maintenance = self.dataset.get("maintenance")
        if maintenance is not None and not maintenance.empty:
            for _, row in maintenance.iterrows():
                events.append(
                    Event(time=_to_hours(row["start_time"]), event_type=EventType.MAINTENANCE_START, machine_id=row["machine_id"])
                )
                events.append(
                    Event(time=_to_hours(row["end_time"]), event_type=EventType.MAINTENANCE_END, machine_id=row["machine_id"])
                )

        # Aynı anda gerçekleşen olaylarda END'ler START'lardan önce işlenir —
        # bir makine biter bitmez aynı anda yeni işe başlayabilsin diye.
        order = {
            EventType.OPERATION_END: 0,
            EventType.MAINTENANCE_END: 0,
            EventType.OPERATION_START: 1,
            EventType.MAINTENANCE_START: 1,
        }
        events.sort(key=lambda e: (e.time, order[e.event_type]))
        return events

    def _apply(self, event: Event) -> None:
        state = self.twin.state
        state.current_time = event.time
        machine = state.machines[event.machine_id]

        if event.event_type == EventType.OPERATION_START:
            machine.status = MachineStatus.RUNNING
            machine.current_operation_id = event.operation_id
            self._op_start_time[event.operation_id] = event.time

            job = state.jobs[event.job_id]
            if job.status == JobStatus.QUEUED:
                job.status = JobStatus.RUNNING
            job.current_operation_id = event.operation_id

        elif event.event_type == EventType.OPERATION_END:
            start_t = self._op_start_time.pop(event.operation_id, event.time)
            duration = event.time - start_t
            energy = event.energy_consumption or 0.0

            machine.status = MachineStatus.IDLE
            machine.current_operation_id = None
            machine.total_busy_hours += duration
            machine.total_energy_kwh += energy

            state.total_energy_kwh += energy
            price = self.price_by_hour.get(int(start_t), 0.0)
            state.total_energy_cost += energy * price

            job = state.jobs[event.job_id]
            job.completed_operations += 1
            job.current_operation_id = None
            if job.completed_operations >= job.total_operations:
                job.completion_time = event.time
                deadline = self.deadlines.get(event.job_id, float("inf"))
                job.status = JobStatus.COMPLETED if event.time <= deadline else JobStatus.DELAYED

        elif event.event_type == EventType.MAINTENANCE_START:
            machine.status = MachineStatus.MAINTENANCE

        elif event.event_type == EventType.MAINTENANCE_END:
            machine.status = MachineStatus.IDLE

    def step(self) -> Event | None:
        """Sıradaki tek olayı işler. Kalan olay yoksa None döner."""
        if self._cursor >= len(self.events):
            return None
        event = self.events[self._cursor]
        self._apply(event)
        self._cursor += 1
        return event

    def run_to(self, time: float) -> None:
        while self._cursor < len(self.events) and self.events[self._cursor].time <= time:
            self.step()
        self.twin.state.current_time = max(self.twin.state.current_time, time)

    def run_all(self) -> None:
        while self.step() is not None:
            pass
