"""Native highspy tabanlı çözücü — appsi_highs'ın bu ortamda güvenilmez çıkması
üzerine (bkz. docs/decision-log.md Phase 8) Pyomo'yu SADECE model kurmak için
kullanıp, çözümü doğrudan highspy'a devrediyoruz. Bu yol, Phase 7-8'de defalarca
doğrulandı: time_limit'e tam uyuyor, donmuyor, warm-start destekliyor.

Akış:
    1. Pyomo modeli MPS'e sembolik etiketlerle yazılır (değişken isimleri korunur).
    2. Pyomo'nun SymbolMap'i ile her Pyomo değişkeninin MPS'teki tam adı bulunur.
    3. (Varsa) warm-start değerleri, bu isim eşlemesiyle highspy'a MIP start olarak verilir.
    4. highspy çözer (time_limit ile).
    5. Çözüm, aynı isim eşlemesiyle Pyomo model değişkenlerine geri yüklenir —
       böylece optimization/results.py::extract_schedule değişmeden çalışır.
"""

from __future__ import annotations

import highspy
import pyomo.environ as pyo


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
    """warm_start_values: {pyomo_var_object_id: value} — genelde
    optimization/warmstart.py::apply_warm_start çağrıldıktan sonra model
    değişkenlerinin .value'sundan otomatik toplanır (aşağıya bakınız).
    """
    mps_path = "/tmp/_native_solve_model.mps"
    smap = _build_symbol_map(model, mps_path)

    h = highspy.Highs()
    if not tee:
        h.setOptionValue("output_flag", False)
    h.readModel(mps_path)
    h.setOptionValue("time_limit", float(time_limit_seconds))

    col_names = list(h.getLp().col_names_)
    name_to_col = {name: idx for idx, name in enumerate(col_names)}

    if warm_start_values:
        col_value = [0.0] * len(col_names)
        n_set = 0
        for var in model.component_data_objects(pyo.Var, active=True):
            if var.value is None:
                continue
            name = smap.byObject.get(id(var))
            if name is None or name not in name_to_col:
                continue
            col_value[name_to_col[name]] = float(var.value)
            n_set += 1
        solution = highspy.HighsSolution()
        solution.col_value = col_value
        solution.value_valid = True
        solution.dual_valid = False
        h.setSolution(solution)

    h.run()

    solution = h.getSolution()
    col_value = list(solution.col_value)

    for var in model.component_data_objects(pyo.Var, active=True):
        name = smap.byObject.get(id(var))
        if name is None or name not in name_to_col:
            continue
        val = col_value[name_to_col[name]]
        # HiGHS'in ham çözümü ikili/tamsayı değişkenler için 0.999999... gibi
        # sayısal gürültü içerebilir (LP toleransı); yuvarlanmazsa Pyomo domain
        # uyarısı verir. Alt sınırın hafif altına düşen sürekli değişkenler
        # (ör. T[j] = -1e-15) de sınıra kırpılıyor.
        if var.is_binary() or var.is_integer():
            val = round(val)
        elif var.lb is not None and val < var.lb:
            val = var.lb
        var.value = val

    info = h.getInfo()
    return {
        "model_status": h.getModelStatus(),
        "model_status_str": h.modelStatusToString(h.getModelStatus()),
        "primal_bound": info.objective_function_value,
        "dual_bound": getattr(info, "mip_dual_bound", None),
        "mip_gap": getattr(info, "mip_gap", None),
        "num_nodes": getattr(info, "mip_node_count", None),
    }


def has_feasible_solution_native(result: dict) -> bool:
    status = result["model_status_str"].lower()
    return "infeasible" not in status and "error" not in status and status != "not set"
