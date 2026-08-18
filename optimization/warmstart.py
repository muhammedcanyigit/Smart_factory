"""Baseline planından (bkz. baseline/scheduler.py) MILP için warm-start (başlangıç
çözümü) üretir — bkz. docs/decision-log.md Phase 8, Phase 11.

Neden: Phase 8'deki Big-M sıkılaştırması, "hiç feasible çözüm bulunamama" sorununu
çözdü ama solver'ın sıfırdan aradığı en iyi çözüm (165.70h) hâlâ baseline'dan
(144.31h) kötüydü. Elimizde zaten geçerli bir çözüm (baseline) varken bunu
solver'a başlangıç noktası olarak vermemek matematiksel israf.

ÖNEMLİ (Phase 11'de düzeltildi): S/C warm-start değerleri artık baseline
schedule'ın HAM zamanlarından değil, modelin KENDİ süre parametresinden
(`data["p"]`) — `optimization/replay.py::replay_schedule` ile — yeniden
hesaplanıyor. Sebep: Phase 11'den itibaren model bazen GERÇEK süre yerine ML
TAHMİNİ süre kullanacak; baseline'ın (gerçek sürelerle üretilmiş) ham
zamanlarını doğrudan vermek, `C[o] = S[o] + p_o/eff[m]` eşitliğini ihlal edip
warm-start'ın "infeasible" sayılıp atlanmasına yol açabilirdi. Baseline artık
sadece "hangi operasyon hangi makineye, hangi sırayla" bilgisini (yapısal
karar) veriyor; zamanlama, modelin kendi süre kaynağıyla tutarlı yeniden
kuruluyor.
"""

from __future__ import annotations

import pandas as pd
import pyomo.environ as pyo

from optimization.replay import build_maintenance_lookup, replay_schedule


def apply_warm_start(model: pyo.ConcreteModel, data: dict, baseline_schedule: pd.DataFrame) -> None:
    horizon_hours = data["horizon_hours"]
    bs = baseline_schedule.sort_values("start_time")

    assigned_machine = bs.set_index("operation_id")["machine_id"].to_dict()
    order = bs["operation_id"].tolist()

    start_hours, end_hours = replay_schedule(
        assigned_machine=assigned_machine,
        order=order,
        op_job=data["op_job"],
        release=data["release"],
        durations=data["p"],
        eff=data["eff"],
        maintenance_by_machine=build_maintenance_lookup(data["maint_list"]),
    )

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
