"""Simülasyon olayları — bkz. docs/decision-log.md Phase 14."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EventType(str, Enum):
    OPERATION_START = "operation_start"
    OPERATION_END = "operation_end"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_END = "maintenance_end"


@dataclass
class Event:
    time: float  # saat cinsinden, HORIZON_START'tan itibaren
    event_type: EventType
    machine_id: str
    operation_id: str | None = None
    job_id: str | None = None
    energy_consumption: float | None = None
