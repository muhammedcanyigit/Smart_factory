"""Tek bir işin (job) anlık durumu — bkz. docs/decision-log.md Phase 13."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"  # henüz hiçbir operasyonu başlamadı
    RUNNING = "running"  # en az bir operasyonu başladı, hepsi bitmedi
    COMPLETED = "completed"  # tüm operasyonlar bitti, deadline'a uyuldu
    DELAYED = "delayed"  # tüm operasyonlar bitti ama deadline kaçırıldı


@dataclass
class JobState:
    job_id: str
    total_operations: int
    completed_operations: int = 0
    status: JobStatus = JobStatus.QUEUED
    current_operation_id: str | None = None
    completion_time: float | None = None  # saat cinsinden, tüm operasyonlar bitince set edilir
