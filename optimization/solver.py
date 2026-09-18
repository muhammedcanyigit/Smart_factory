"""Solver seçimi ve çalıştırma — bkz. docs/project-plan.md Phase 8.

2026-09-18: Aktif solver Gurobi'ye geçirildi (kullanıcı akademik Gurobi
lisansı edindi) — bkz. docs/decision-log.md "Solver Değişikliği: HiGHS ->
Gurobi". Gerçekte kullanılan yol her zaman `solve_with_warm_start` (aşağıya
bakınız); bu fonksiyon (`solve`) hâlâ hem "highs" hem "gurobi" adını kabul
eden basit, warm-start'sız bir alternatif olarak duruyor ama pipeline'ın
hiçbir yerinden çağrılmıyor.

TARİHSEL NOT (bkz. docs/decision-log.md Phase 7, artık HiGHS aktif değilken
de geçerliliğini koruyan bir hata ayıklama kaydı): Pyomo'nun `appsi_highs`
arayüzü, solver zaman sınırına ulaşıp HİÇBİR uygun (feasible) çözüm
bulamadığında sessizce sonsuza kadar takılı kalıyordu (gerçek bir Pyomo/APPSI
hatası). Bu yüzden HiGHS aktifken burada bilinçli olarak `appsi_highs` DEĞİL,
Pyomo'nun `pyomo.contrib.solver` tabanlı `highs` arayüzü kullanılmıştı;
`load_solutions=False` ile çözüm bulunamama durumu istisna fırlatmadan
ele alınıyordu. Gurobi'nin Pyomo arayüzünde bu sınıfta bilinen bir hata yok.
"""

from __future__ import annotations

import pyomo.environ as pyo


def solve(model: pyo.ConcreteModel, solver_name: str = "gurobi", time_limit_seconds: int = 300):
    if solver_name == "highs":
        opt = pyo.SolverFactory("highs")
        results = opt.solve(
            model,
            load_solutions=False,
            raise_exception_on_nonoptimal_result=False,
            options={"time_limit": time_limit_seconds},
        )
    elif solver_name == "gurobi":
        opt = pyo.SolverFactory("gurobi")
        results = opt.solve(model, options={"TimeLimit": time_limit_seconds})
    else:
        raise ValueError(f"Bilinmeyen solver: {solver_name!r} (highs veya gurobi olmalı)")
    return results


def has_feasible_solution(results) -> bool:
    tc = str(results.solver.termination_condition).lower()
    return tc in ("optimal", "maxtimelimit", "feasible", "locallyoptimal")


def load_solution(model: pyo.ConcreteModel, results) -> None:
    """solve() çağrısı load_solutions=False ile yapıldığı için, feasible bir
    çözüm varsa (has_feasible_solution ile önce kontrol edilmeli) bunu model
    değişkenlerine yükler."""
    model.solutions.load_from(results)


def solve_with_warm_start(model: pyo.ConcreteModel, data: dict, baseline_schedule, time_limit_seconds: int = 300):
    """TEK gerçekten kullanılan yol — bkz. docs/decision-log.md Phase 8 (mimari)
    ve "Solver Değişikliği: HiGHS -> Gurobi" (2026-09-18, aktif motor). Baseline
    planını warm-start olarak verip `optimization/native_solver.py::solve_native`
    ile (bugün: gurobipy) çözer.
    """
    from optimization.native_solver import solve_native
    from optimization.warmstart import apply_warm_start

    apply_warm_start(model, data, baseline_schedule)
    return solve_native(model, data, time_limit_seconds=time_limit_seconds, warm_start_values=True)
