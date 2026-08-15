"""Pyomo kısıtları — bkz. docs/mathematical-model.md Bölüm 5 ve 6.1.

Fonksiyon adları dokümandaki kısıt numaralarıyla birebir eşleşir (C1..C8 + Cmax
tanımı + w linking). C5 (kapasite) burada gerçek bir eşitsizlik DEĞİL — bkz.
docs/mathematical-model.md Bölüm 5, C5 notu: eligible_om zaten machine_type
eşleşmesiyle filtrelenmiş durumda geliyor (model.py::prepare_data).

Önemli sınırlama (bkz. docs/decision-log.md Phase 7 notu): Machine.capacity
şu an hiçbir kısıta bağlı değil — Phase 2'de capacity, quantity/processing_time
ile hiç ilişkilendirilmeden bağımsız üretildi. Yapay bir formülle bağlamak
(ör. capacity >= quantity/processing_time) ya hep ya hiç davranırdı (verideki
değer aralıkları tutarsız). Bu yüzden C5 aktif olarak uygulanmıyor; bu açık bir
sınırlama olarak belgelendi, uydurulmuş bir kısıt eklenmedi.
"""

from __future__ import annotations

import pyomo.environ as pyo


def add_c1_assignment(model: pyo.ConcreteModel, data: dict) -> None:
    def rule(mdl, o):
        return sum(mdl.x[o, m] for m in data["eligible_om"][o]) == 1

    model.c1_assignment = pyo.Constraint(model.O_SET, rule=rule)


def add_completion_time_definition(model: pyo.ConcreteModel, data: dict) -> None:
    """C[o] = S[o] + sum_m x[o,m] * (p_o / eff_m) — bkz. Bölüm 3.2."""

    def rule(mdl, o):
        duration = sum(mdl.x[o, m] * (data["p"][o] / data["eff"][m]) for m in data["eligible_om"][o])
        return mdl.C[o] == mdl.S[o] + duration

    model.c_completion_def = pyo.Constraint(model.O_SET, rule=rule)


def add_c2_job_sequence(model: pyo.ConcreteModel, data: dict) -> None:
    pairs = []
    for j, ops in data["job_ops"].items():
        for k in range(len(ops) - 1):
            pairs.append((ops[k], ops[k + 1]))

    model.C2Pairs = pyo.Set(initialize=pairs, dimen=2)

    def rule(mdl, o_prev, o_next):
        return mdl.S[o_next] >= mdl.C[o_prev]

    model.c2_job_sequence = pyo.Constraint(model.C2Pairs, rule=rule)


def add_c3_machine_conflict(model: pyo.ConcreteModel, data: dict) -> None:
    big_m = data["big_m"]
    triples = [(o, o2, m) for (o, o2) in data["y_pairs"] for m in data["eligible_om"][o]]
    model.C3Triples = pyo.Set(initialize=triples, dimen=3)

    def rule_forward(mdl, o, o2, m):
        return mdl.S[o2] >= mdl.C[o] - big_m * (1 - mdl.y[o, o2]) - big_m * (2 - mdl.x[o, m] - mdl.x[o2, m])

    def rule_backward(mdl, o, o2, m):
        return mdl.S[o] >= mdl.C[o2] - big_m * mdl.y[o, o2] - big_m * (2 - mdl.x[o, m] - mdl.x[o2, m])

    model.c3_machine_conflict_fwd = pyo.Constraint(model.C3Triples, rule=rule_forward)
    model.c3_machine_conflict_bwd = pyo.Constraint(model.C3Triples, rule=rule_backward)


def add_c4_maintenance(model: pyo.ConcreteModel, data: dict) -> None:
    big_m = data["big_m"]
    maint_list = data["maint_list"]

    def rule_before(mdl, o, k):
        m = maint_list[k]["machine_id"]
        ms = maint_list[k]["start"]
        return mdl.C[o] <= ms + big_m * (1 - mdl.z[o, k]) + big_m * (1 - mdl.x[o, m])

    def rule_after(mdl, o, k):
        m = maint_list[k]["machine_id"]
        me = maint_list[k]["end"]
        return mdl.S[o] >= me - big_m * mdl.z[o, k] - big_m * (1 - mdl.x[o, m])

    model.c4_maintenance_before = pyo.Constraint(model.ZPairs, rule=rule_before)
    model.c4_maintenance_after = pyo.Constraint(model.ZPairs, rule=rule_after)


def add_c6_release_time(model: pyo.ConcreteModel, data: dict) -> None:
    first_ops = {j: ops[0] for j, ops in data["job_ops"].items() if ops}

    def rule(mdl, j):
        return mdl.S[first_ops[j]] >= data["release"][j]

    model.c6_release_time = pyo.Constraint(model.J_SET, rule=rule)


def add_c7_tardiness(model: pyo.ConcreteModel, data: dict) -> None:
    last_ops = {j: ops[-1] for j, ops in data["job_ops"].items() if ops}

    def rule(mdl, j):
        return mdl.T[j] >= mdl.C[last_ops[j]] - data["deadline"][j]

    model.c7_tardiness = pyo.Constraint(model.J_SET, rule=rule)
    # T[j] >= 0 zaten değişken tanımında (NonNegativeReals) sağlanıyor.


def add_c8_availability_window(model: pyo.ConcreteModel, data: dict) -> None:
    big_m = data["big_m"]

    def rule_start(mdl, o, m):
        return mdl.S[o] >= data["avail_from"][m] - big_m * (1 - mdl.x[o, m])

    def rule_end(mdl, o, m):
        return mdl.C[o] <= data["avail_until"][m] + big_m * (1 - mdl.x[o, m])

    model.c8_availability_start = pyo.Constraint(model.OM, rule=rule_start)
    model.c8_availability_end = pyo.Constraint(model.OM, rule=rule_end)


def add_cmax_definition(model: pyo.ConcreteModel, data: dict) -> None:
    def rule(mdl, o):
        return mdl.Cmax >= mdl.C[o]

    model.cmax_def = pyo.Constraint(model.O_SET, rule=rule)


def add_w_linking(model: pyo.ConcreteModel, data: dict) -> None:
    """w[o,t] linking — bkz. Bölüm 6.1. Sadece include_energy=True iken çağrılır."""
    big_m = data["big_m"]

    def rule_sum(mdl, o):
        return sum(mdl.w[o, t] for t in range(data["horizon_hours"])) == 1

    def rule_lower(mdl, o, t):
        return mdl.S[o] >= t - big_m * (1 - mdl.w[o, t])

    def rule_upper(mdl, o, t):
        return mdl.S[o] <= (t + 1) + big_m * (1 - mdl.w[o, t])

    model.w_sum_to_one = pyo.Constraint(model.O_SET, rule=rule_sum)
    model.w_link_lower = pyo.Constraint(model.OT, rule=rule_lower)
    model.w_link_upper = pyo.Constraint(model.OT, rule=rule_upper)


def add_constraints(model: pyo.ConcreteModel, data: dict, include_energy: bool) -> None:
    add_c1_assignment(model, data)
    add_completion_time_definition(model, data)
    add_c2_job_sequence(model, data)
    add_c3_machine_conflict(model, data)
    add_c4_maintenance(model, data)
    # C5: bkz. modül docstring'i — eligible_om filtresine gömülü, ayrı kısıt yok.
    add_c6_release_time(model, data)
    add_c7_tardiness(model, data)
    add_c8_availability_window(model, data)
    add_cmax_definition(model, data)
    if include_energy:
        add_w_linking(model, data)
