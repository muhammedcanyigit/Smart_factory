"""Solver çıktısını, baseline/scheduler.py ile aynı formatta (operation_id, job_id,
machine_id, sequence_no, start_time, end_time, energy_consumption) bir DataFrame'e
çevirir — böylece baseline/metrics.py fonksiyonları optimize edilmiş plan için de
aynen kullanılabilir (Phase 9'da baseline vs optimized karşılaştırması).
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pyomo.environ as pyo

from data_generator.generator import HORIZON_START


def extract_schedule(model: pyo.ConcreteModel, data: dict) -> pd.DataFrame:
    rows = []
    for o in data["O"]:
        assigned_machine = None
        for m in data["eligible_om"][o]:
            if pyo.value(model.x[o, m]) > 0.5:
                assigned_machine = m
                break
        if assigned_machine is None:
            raise ValueError(f"Operasyon {o} hiçbir makineye atanmamış — çözüm tutarsız")

        start_hours = pyo.value(model.S[o])
        end_hours = pyo.value(model.C[o])

        rows.append(
            {
                "operation_id": o,
                "job_id": data["op_job"][o],
                "machine_id": assigned_machine,
                "sequence_no": data["op_seq"][o],
                "start_time": HORIZON_START + timedelta(hours=start_hours),
                "end_time": HORIZON_START + timedelta(hours=end_hours),
                "energy_consumption": data["e"][o],
            }
        )

    return pd.DataFrame(rows).sort_values(["job_id", "sequence_no"]).reset_index(drop=True)
