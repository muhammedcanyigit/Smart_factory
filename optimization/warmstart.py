"""Baseline planından (bkz. baseline/scheduler.py) MILP için warm-start (başlangıç
çözümü) üretir — bkz. docs/decision-log.md Phase 8.

Neden: Phase 8'deki Big-M sıkılaştırması, "hiç feasible çözüm bulunamama" sorununu
çözdü ama solver'ın sıfırdan aradığı en iyi çözüm (165.70h) hâlâ baseline'dan
(144.31h) kötüydü. Elimizde zaten geçerli bir çözüm (baseline) varken bunu
solver'a başlangıç noktası olarak vermemek matematiksel israf.

Baseline'ın MILP'in TÜM kısıtlarını (C1-C8) sağladığı Phase 3'te doğrulanmıştı
(makine çakışması yok, sıra ihlali yok, bakım çakışması yok) — bu yüzden warm
start olarak kullanmak güvenli.
"""

from __future__ import annotations

import pandas as pd
import pyomo.environ as pyo

from data_generator.generator import HORIZON_START


def apply_warm_start(model: pyo.ConcreteModel, data: dict, baseline_schedule: pd.DataFrame) -> None:
    horizon_hours = data["horizon_hours"]
    bs = baseline_schedule.set_index("operation_id")

    def to_hours(ts) -> float:
        return (pd.Timestamp(ts) - HORIZON_START).total_seconds() / 3600

    assigned_machine = bs["machine_id"].to_dict()
    start_hours = {o: max(0.0, min(to_hours(bs.loc[o, "start_time"]), horizon_hours)) for o in bs.index}
    end_hours = {o: max(0.0, min(to_hours(bs.loc[o, "end_time"]), horizon_hours)) for o in bs.index}

    for o in data["O"]:
        for m in data["eligible_om"][o]:
            model.x[o, m].value = 1.0 if assigned_machine.get(o) == m else 0.0
        model.S[o].value = start_hours[o]
        model.C[o].value = end_hours[o]

    for o1, o2 in data["y_pairs"]:
        model.y[o1, o2].value = 1.0 if start_hours[o1] <= start_hours[o2] else 0.0

    for o, k in data["maint_pairs"]:
        mrec = data["maint_list"][k]
        model.z[o, k].value = 1.0 if end_hours[o] <= mrec["start"] else 0.0

    if hasattr(model, "w"):
        for o in data["O"]:
            t0 = int(start_hours[o])
            t0 = max(0, min(t0, horizon_hours - 1))
            for t in range(horizon_hours):
                model.w[o, t].value = 1.0 if t == t0 else 0.0

    for j in data["J"]:
        last_op = data["job_ops"][j][-1]
        tard = max(0.0, end_hours[last_op] - data["deadline"][j])
        model.T[j].value = tard

    model.Cmax.value = max(end_hours.values())
