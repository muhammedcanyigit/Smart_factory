"""Native gurobipy tabanlı çözücü.

2026-09-18: Kullanıcı Gurobi lisansı edindiği için HiGHS devre dışı bırakıldı,
bu modül `highspy` yerine `gurobipy`'a taşındı (bkz. docs/decision-log.md
"Solver Değişikliği: HiGHS -> Gurobi"). Mimari aynı kaldı — Pyomo modeli
SADECE kurmak için kullanılıyor, çözüm doğrudan native kütüphaneye devrediliyor
(Pyomo'nun genel amaçlı solver arayüzlerindeki ek soyutlama katmanını, ve
geçmişte HiGHS'te yaşanan appsi_highs donma hatasını, bypass etmek için —
bkz. Phase 7-8 tarihi, docs/decision-log.md).

Akış (HiGHS versiyonuyla birebir aynı desen):
    1. Pyomo modeli MPS'e sembolik etiketlerle, İSTEK BAŞINA benzersiz bir
       geçici dosyaya yazılır (`tempfile` — sabit/paylaşılan bir yol
       kullanılmıyor; aksi halde eşzamanlı iki istek [ör. dashboard'da iki
       eşzamanlı /optimize çağrısı] aynı dosyayı okuyup/yazıp birbirinin
       modelini bozabilirdi).
    2. Pyomo'nun SymbolMap'i ile her Pyomo değişkeninin MPS'teki tam adı bulunur.
    3. (Varsa) warm-start değerleri, bu isim eşlemesiyle gurobipy değişkenlerinin
       `.Start` alanına MIP start olarak yazılır.
    4. gurobipy çözer (`Params.TimeLimit` ile).
    5. Çözüm, aynı isim eşlemesiyle Pyomo model değişkenlerine geri yüklenir —
       böylece optimization/results.py::extract_schedule değişmeden çalışır.
"""

from __future__ import annotations

import os
import tempfile

import gurobipy as gp
import pyomo.environ as pyo

# Gurobi'nin durum kodlarını okunabilir string'e çevirir (HiGHS'in
# `modelStatusToString`'ine karşılık gelen, elle tutulan bir eşleme —
# gurobipy'de hazır bir "status to string" fonksiyonu yok).
_GRB_STATUS_NAMES = {
    gp.GRB.LOADED: "loaded",
    gp.GRB.OPTIMAL: "optimal",
    gp.GRB.INFEASIBLE: "infeasible",
    gp.GRB.INF_OR_UNBD: "infeasible_or_unbounded",
    gp.GRB.UNBOUNDED: "unbounded",
    gp.GRB.CUTOFF: "cutoff",
    gp.GRB.ITERATION_LIMIT: "iteration_limit",
    gp.GRB.NODE_LIMIT: "node_limit",
    gp.GRB.TIME_LIMIT: "time_limit",
    gp.GRB.SOLUTION_LIMIT: "solution_limit",
    gp.GRB.INTERRUPTED: "interrupted",
    gp.GRB.NUMERIC: "numeric_error",
    gp.GRB.SUBOPTIMAL: "suboptimal",
    gp.GRB.INPROGRESS: "in_progress",
    gp.GRB.USER_OBJ_LIMIT: "user_obj_limit",
}


def _safe_attr(gmodel, name: str):
    """Bazı Gurobi öznitelikleri (ör. MIPGap) yalnızca gerçek bir MIP çözümü
    sonrası tanımlıdır — saf LP olarak çözülen modellerde (ör. hiç binary/
    integer değişken kalmayan boş bir örnek) AttributeError fırlatır. Bu
    durumda None dönmek, HiGHS'in `getattr(info, ..., None)` davranışıyla
    tutarlı."""
    try:
        return getattr(gmodel, name)
    except (AttributeError, gp.GurobiError):
        return None


def _build_symbol_map(model: pyo.ConcreteModel, mps_path: str):
    _, smap_id = model.write(mps_path, io_options={"symbolic_solver_labels": True})
    return model.solutions.symbol_map[smap_id]


def solve_native(
    model: pyo.ConcreteModel,
    data: dict,
    time_limit_seconds: int = 300,
    warm_start_values: dict | None = None,
    tee: bool = False,
) -> dict:
    """warm_start_values: gerçek değerler değil, sadece bir bayrak — True ise
    (genelde optimization/warmstart.py::apply_warm_start çağrıldıktan sonra)
    model değişkenlerinin mevcut `.value`'ları otomatik toplanıp Gurobi'ye
    MIP start olarak verilir.
    """
    fd, mps_path = tempfile.mkstemp(suffix=".mps", prefix="smart_factory_")
    os.close(fd)
    env = None
    try:
        smap = _build_symbol_map(model, mps_path)

        env = gp.Env(params={"OutputFlag": 1 if tee else 0})
        gmodel = gp.read(mps_path, env=env)
        gmodel.Params.TimeLimit = float(time_limit_seconds)

        name_to_var = {v.VarName: v for v in gmodel.getVars()}

        if warm_start_values:
            n_set = 0
            for var in model.component_data_objects(pyo.Var, active=True):
                if var.value is None:
                    continue
                name = smap.byObject.get(id(var))
                gvar = name_to_var.get(name) if name is not None else None
                if gvar is None:
                    continue
                gvar.Start = float(var.value)
                n_set += 1

        gmodel.optimize()

        has_solution = gmodel.SolCount > 0
        for var in model.component_data_objects(pyo.Var, active=True):
            name = smap.byObject.get(id(var))
            gvar = name_to_var.get(name) if name is not None else None
            if gvar is None or not has_solution:
                continue
            val = gvar.X
            # Gurobi'nin ham çözümü ikili/tamsayı değişkenler için 0.999999...
            # gibi sayısal gürültü içerebilir; yuvarlanmazsa Pyomo domain
            # uyarısı verir. Alt sınırın hafif altına düşen sürekli değişkenler
            # (ör. T[j] = -1e-15) de sınıra kırpılıyor.
            if var.is_binary() or var.is_integer():
                val = round(val)
            elif var.lb is not None and val < var.lb:
                val = var.lb
            var.value = val

        status = gmodel.Status
        return {
            "model_status": status,
            "model_status_str": _GRB_STATUS_NAMES.get(status, f"status_{status}"),
            "has_solution": has_solution,
            "primal_bound": gmodel.ObjVal if has_solution else None,
            "dual_bound": _safe_attr(gmodel, "ObjBound"),
            "mip_gap": _safe_attr(gmodel, "MIPGap") if has_solution else None,
            "num_nodes": _safe_attr(gmodel, "NodeCount"),
        }
    finally:
        if env is not None:
            env.dispose()
        if os.path.exists(mps_path):
            os.remove(mps_path)


def has_feasible_solution_native(result: dict) -> bool:
    """Gurobi'de "zaman doldu ama hiç çözüm yok" (SolCount=0) ile "kanıtlanmış
    infeasible" farklı durumlar — ikisi de burada `False` sayılır (kullanılabilir
    bir plan yok anlamına geldikleri için ikisi de aynı şekilde ele alınmalı).
    `has_solution` alanı bu ayrımı SolCount üzerinden doğrudan yapıyor (HiGHS
    versiyonundaki gibi durum string'ine bakıp tahmin etmiyor)."""
    return bool(result.get("has_solution", False))
