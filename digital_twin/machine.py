"""Tek bir makinenin anlık durumu — bkz. docs/decision-log.md Phase 13.

MachineStatus, data_generator/schemas.py'deki enum'un aynısı — burada yeniden
tanımlamak yerine yeniden kullanılıyor (tek gerçek kaynak, tutarlılık için).
"""

from __future__ import annotations

from dataclasses import dataclass

from data_generator.schemas import MachineStatus

__all__ = ["MachineStatus", "MachineState"]


@dataclass
class MachineState:
    machine_id: str
    machine_type: str
    status: MachineStatus = MachineStatus.IDLE
    current_operation_id: str | None = None
    busy_until: float | None = None  # saat cinsinden (HORIZON_START'tan itibaren), None = boşta
    total_busy_hours: float = 0.0
    total_energy_kwh: float = 0.0
