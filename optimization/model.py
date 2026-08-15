"""MILP modelini kurar: veri hazırlığı + değişkenler + kısıtlar + amaç fonksiyonu.

Kullanım:
    from optimization.model import build_model
    model, data = build_model(dataset, config, stage="makespan")

`stage` değerleri için bkz. optimization/objective.py. Her formülün
docs/mathematical-model.md'deki karşılığı ilgili modülün docstring'inde belirtilir.
"""

from __future__ import annotations

import pandas as pd
import pyomo.environ as pyo

from data_generator.generator import HORIZON_START
from optimization.constraints import add_constraints
from optimization.objective import add_objective
from optimization.variables import add_variables


def _to_hours(ts: pd.Timestamp) -> float:
    return (ts - HORIZON_START).total_seconds() / 3600


def prepare_data(dataset: dict[str, pd.DataFrame], config: dict) -> dict:
    machines = dataset["machines"].copy()
    jobs = dataset["jobs"].copy()
    operations = dataset["operations"].copy()
    maintenance = dataset["maintenance"].copy()
    energy_prices = dataset["energy_prices"].copy()

    horizon_hours = config["dataset"]["horizon_hours"]

    jobs["release_time"] = pd.to_datetime(jobs["release_time"])
    jobs["deadline"] = pd.to_datetime(jobs["deadline"])
    machines["available_from"] = pd.to_datetime(machines["available_from"])
    machines["available_until"] = pd.to_datetime(machines["available_until"])
    if not maintenance.empty:
        maintenance["start_time"] = pd.to_datetime(maintenance["start_time"])
        maintenance["end_time"] = pd.to_datetime(maintenance["end_time"])
    energy_prices["timestamp"] = pd.to_datetime(energy_prices["timestamp"])

    O = operations["operation_id"].tolist()
    J = jobs["job_id"].tolist()

    eff = dict(zip(machines["machine_id"], machines["efficiency"]))
    avail_from = {m: _to_hours(t) for m, t in zip(machines["machine_id"], machines["available_from"])}
    avail_until = {m: _to_hours(t) for m, t in zip(machines["machine_id"], machines["available_until"])}

    type_to_machines = machines.groupby("machine_type")["machine_id"].apply(list).to_dict()

    eligible_om: dict[str, list[str]] = {}
    p: dict[str, float] = {}
    e: dict[str, float] = {}
    op_job: dict[str, str] = {}
    op_seq: dict[str, int] = {}
    for _, row in operations.iterrows():
        o = row["operation_id"]
        candidates = list(type_to_machines.get(row["required_machine_type"], []))
        if not candidates:
            raise ValueError(f"'{row['required_machine_type']}' tipinde hiç makine yok — dataset tutarsız")
        # C5 notu (bkz. optimization/constraints.py docstring): kapasite şu an
        # ayrı bir filtre uygulamıyor, machine_type eşleşmesi yeterli sayılıyor.
        eligible_om[o] = candidates
        p[o] = row["processing_time"]
        e[o] = row["energy_consumption"]
        op_job[o] = row["job_id"]
        op_seq[o] = row["sequence_no"]

    job_ops: dict[str, list[str]] = {}
    for j in J:
        subset = operations[operations["job_id"] == j].sort_values("sequence_no")
        job_ops[j] = subset["operation_id"].tolist()

    release = {j: _to_hours(r) for j, r in zip(jobs["job_id"], jobs["release_time"])}
    deadline = {j: _to_hours(d) for j, d in zip(jobs["job_id"], jobs["deadline"])}

    # y_pairs: farklı job'lara ait, aynı required_machine_type'ı paylaşan operasyon çiftleri
    # (bkz. mathematical-model.md Bölüm 1 "Yapısal gözlem")
    y_pairs = []
    by_type = operations.groupby("required_machine_type")["operation_id"].apply(list).to_dict()
    for ops in by_type.values():
        for i in range(len(ops)):
            for k in range(i + 1, len(ops)):
                o1, o2 = ops[i], ops[k]
                if op_job[o1] != op_job[o2]:
                    y_pairs.append((o1, o2))

    maint_list = [
        {
            "machine_id": row["machine_id"],
            "start": _to_hours(row["start_time"]),
            "end": _to_hours(row["end_time"]),
        }
        for _, row in maintenance.iterrows()
    ]
    maint_pairs = [
        (o, k) for o in O for k, mrec in enumerate(maint_list) if mrec["machine_id"] in eligible_om[o]
    ]

    price_by_hour: dict[int, float] = {}
    for _, row in energy_prices.iterrows():
        h = int(_to_hours(row["timestamp"]))
        price_by_hour[h] = row["price_per_kwh"]

    big_m = config["optimization"].get("big_m", 2 * horizon_hours)

    return {
        "O": O,
        "J": J,
        "eligible_om": eligible_om,
        "p": p,
        "e": e,
        "eff": eff,
        "job_ops": job_ops,
        "op_job": op_job,
        "op_seq": op_seq,
        "release": release,
        "deadline": deadline,
        "y_pairs": y_pairs,
        "maint_list": maint_list,
        "maint_pairs": maint_pairs,
        "avail_from": avail_from,
        "avail_until": avail_until,
        "price_by_hour": price_by_hour,
        "horizon_hours": horizon_hours,
        "big_m": big_m,
    }


def build_model(dataset: dict[str, pd.DataFrame], config: dict, stage: str = "final"):
    data = prepare_data(dataset, config)
    include_energy = stage in ("energy", "final")

    model = pyo.ConcreteModel(name=f"smart_factory_{stage}")
    add_variables(model, data, include_energy=include_energy)
    add_constraints(model, data, include_energy=include_energy)
    add_objective(model, data, stage=stage, weights=config["optimization"].get("objective_weights"))

    return model, data
