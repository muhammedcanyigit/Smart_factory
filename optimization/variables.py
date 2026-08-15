"""Pyomo karar değişkenleri — bkz. docs/mathematical-model.md Bölüm 3 ve 6.1.

Her değişkenin dokümandaki karşılığı:
    x[o,m]  -> model.x   (Bölüm 3.1)
    S[o]    -> model.S   (Bölüm 3.2)
    C[o]    -> model.C   (Bölüm 3.2)
    y[o,o'] -> model.y   (Bölüm 3.3)
    T[j]    -> model.T   (Bölüm 3.4)
    C_max   -> model.Cmax (Bölüm 3.5)
    w[o,t]  -> model.w   (Bölüm 6.1, sadece include_energy=True iken)
"""

from __future__ import annotations

import pyomo.environ as pyo


def add_variables(model: pyo.ConcreteModel, data: dict, include_energy: bool) -> None:
    om_pairs = [(o, m) for o in data["O"] for m in data["eligible_om"][o]]
    model.OM = pyo.Set(initialize=om_pairs, dimen=2)
    model.x = pyo.Var(model.OM, domain=pyo.Binary)

    model.O_SET = pyo.Set(initialize=data["O"])
    model.S = pyo.Var(model.O_SET, domain=pyo.NonNegativeReals)
    model.C = pyo.Var(model.O_SET, domain=pyo.NonNegativeReals)

    model.YPairs = pyo.Set(initialize=data["y_pairs"], dimen=2)
    model.y = pyo.Var(model.YPairs, domain=pyo.Binary)

    model.J_SET = pyo.Set(initialize=data["J"])
    model.T = pyo.Var(model.J_SET, domain=pyo.NonNegativeReals)

    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    model.ZPairs = pyo.Set(initialize=data["maint_pairs"], dimen=2)
    model.z = pyo.Var(model.ZPairs, domain=pyo.Binary)

    if include_energy:
        hours = list(range(data["horizon_hours"]))
        ot_pairs = [(o, t) for o in data["O"] for t in hours]
        model.OT = pyo.Set(initialize=ot_pairs, dimen=2)
        model.w = pyo.Var(model.OT, domain=pyo.Binary)
