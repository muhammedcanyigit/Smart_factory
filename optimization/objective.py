"""Amaç fonksiyonu — bkz. docs/mathematical-model.md Bölüm 6.

stage değerleri:
    "makespan"  -> Stage 1: min C_max
    "energy"    -> Stage 2: min EnergyCost
    "tardiness" -> Stage 3: min Σ T[j]
    "final"     -> Stage 4: min α·C_max + EnergyCost + γ·Σ T[j]  (Bölüm 6.3)
"""

from __future__ import annotations

import pyomo.environ as pyo


def energy_cost_expr(model: pyo.ConcreteModel, data: dict):
    return sum(
        data["e"][o] * sum(model.w[o, t] * data["price_by_hour"].get(t, 0.0) for t in range(data["horizon_hours"]))
        for o in data["O"]
    )


def add_objective(model: pyo.ConcreteModel, data: dict, stage: str, weights: dict | None = None) -> None:
    if stage == "makespan":
        model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)
    elif stage == "energy":
        model.obj = pyo.Objective(expr=energy_cost_expr(model, data), sense=pyo.minimize)
    elif stage == "tardiness":
        model.obj = pyo.Objective(expr=sum(model.T[j] for j in data["J"]), sense=pyo.minimize)
    elif stage == "final":
        w = weights or {}
        c_time = w.get("production_time", 50)
        c_energy = w.get("energy_cost", 1)
        c_tardy = w.get("tardiness", 100)
        expr = (
            c_time * model.Cmax
            + c_energy * energy_cost_expr(model, data)
            + c_tardy * sum(model.T[j] for j in data["J"])
        )
        model.obj = pyo.Objective(expr=expr, sense=pyo.minimize)
    else:
        raise ValueError(f"Bilinmeyen stage: {stage!r}")
