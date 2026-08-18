"""Fabrikanın tüm durumunu (tüm makineler + tüm işler + genel metrikler) bir
arada tutan ana state nesnesi — bkz. docs/decision-log.md Phase 13.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from digital_twin.job import JobState, JobStatus
from digital_twin.machine import MachineState, MachineStatus


@dataclass
class FactoryState:
    horizon_hours: int
    current_time: float = 0.0  # saat cinsinden, HORIZON_START'tan itibaren
    machines: dict[str, MachineState] = field(default_factory=dict)
    jobs: dict[str, JobState] = field(default_factory=dict)
    total_energy_kwh: float = 0.0
    total_energy_cost: float = 0.0

    def machine_utilization(self) -> dict[str, float]:
        """Her makine için: şimdiye kadar geçen sürenin ne kadarı meşgul geçti."""
        if self.current_time <= 0:
            return {m: 0.0 for m in self.machines}
        return {
            m_id: min(1.0, m.total_busy_hours / self.current_time) for m_id, m in self.machines.items()
        }

    def completed_jobs(self) -> list[str]:
        return [j.job_id for j in self.jobs.values() if j.status == JobStatus.COMPLETED]

    def delayed_jobs(self) -> list[str]:
        return [j.job_id for j in self.jobs.values() if j.status == JobStatus.DELAYED]

    def running_jobs(self) -> list[str]:
        return [j.job_id for j in self.jobs.values() if j.status == JobStatus.RUNNING]

    def queued_jobs(self) -> list[str]:
        return [j.job_id for j in self.jobs.values() if j.status == JobStatus.QUEUED]

    def machines_by_status(self, status: MachineStatus) -> list[str]:
        return [m.machine_id for m in self.machines.values() if m.status == status]

    def snapshot(self) -> dict:
        """Anlık durumun sözlük (JSON-serileştirilebilir) hali — dashboard/loglama için."""
        return {
            "current_time_hours": round(self.current_time, 2),
            "total_machines": len(self.machines),
            "running_machines": len(self.machines_by_status(MachineStatus.RUNNING)),
            "idle_machines": len(self.machines_by_status(MachineStatus.IDLE)),
            "maintenance_machines": len(self.machines_by_status(MachineStatus.MAINTENANCE)),
            "total_jobs": len(self.jobs),
            "queued_jobs": len(self.queued_jobs()),
            "running_jobs": len(self.running_jobs()),
            "completed_jobs": len(self.completed_jobs()),
            "delayed_jobs": len(self.delayed_jobs()),
            "total_energy_kwh": round(self.total_energy_kwh, 2),
            "total_energy_cost": round(self.total_energy_cost, 2),
            "avg_machine_utilization": round(
                sum(self.machine_utilization().values()) / len(self.machines), 3
            )
            if self.machines
            else 0.0,
        }
