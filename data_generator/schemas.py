"""Phase 1 veri modelinin Python karşılığı — bkz. docs/dataset.md

Bu dosya sadece veri yapısını (hangi alan, hangi tip) tanımlar; üretim
mantığı generator.py içindedir.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MachineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    BROKEN = "broken"


class MaintenanceType(str, Enum):
    SCHEDULED = "scheduled"
    EMERGENCY = "emergency"


@dataclass
class Machine:
    machine_id: str
    machine_type: str
    capacity: float
    status: MachineStatus
    efficiency: float
    energy_rate: float
    age: int
    available_from: datetime
    available_until: datetime


@dataclass
class Job:
    job_id: str
    product_type: str
    quantity: int
    priority: int
    release_time: datetime
    deadline: datetime


@dataclass
class Operation:
    operation_id: str
    job_id: str
    sequence_no: int
    required_machine_type: str
    processing_time: float
    energy_consumption: float


@dataclass
class EnergyPrice:
    timestamp: datetime
    price_per_kwh: float


@dataclass
class Maintenance:
    maintenance_id: str
    machine_id: str
    start_time: datetime
    end_time: datetime
    maintenance_type: MaintenanceType
