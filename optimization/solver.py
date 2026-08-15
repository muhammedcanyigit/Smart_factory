"""Solver seçimi ve çalıştırma — bkz. docs/project-plan.md Phase 8.

Şimdilik HiGHS destekleniyor; Gurobi kurulu değilse hata vermeden, config'de
"gurobi" seçilmedikçe hiç devreye girmez.

ÖNEMLİ HATA NOTU (bkz. docs/decision-log.md Phase 7): Pyomo'nun `appsi_highs`
arayüzü, solver zaman sınırına ulaşıp HİÇBİR uygun (feasible) çözüm
bulamadığında sessizce sonsuza kadar takılı kalıyor (gerçek bir Pyomo/APPSI
hatası — native highspy ve Pyomo'nun yeni `highs` arayüzü bu durumda düzgün
davranıyor). Bu yüzden burada bilinçli olarak `appsi_highs` DEĞİL, Pyomo'nun
yeni `pyomo.contrib.solver` tabanlı `highs` arayüzü kullanılıyor;
`load_solutions=False` ile çözüm bulunamama durumu istisna fırlatmadan,
kontrollü şekilde ele alınıyor.
"""

from __future__ import annotations

import pyomo.environ as pyo


def solve(model: pyo.ConcreteModel, solver_name: str = "highs", time_limit_seconds: int = 300):
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
