"""Sabit bir (makine ataması, sıra) kararını, verilen süre kaynağıyla zamanlayan
ortak yardımcı fonksiyon. Hem warm-start (Phase 8, optimization/warmstart.py)
hem Predict→Optimize replay'i (Phase 11, ml/predict_optimize.py) bunu kullanır.

Neden ortak: iki kullanım da aynı mantığı gerektiriyor — "hangi operasyon hangi
makineye, hangi sırayla" kararı sabitken, süre değerleri (tahmini ya da gerçek)
değişince zamanlamanın (start/end) yeniden, TUTARLI şekilde hesaplanması.

ÖNEMLİ (bir hata düzeltmesi): İlk sürümde bakım pencereleri hesaba katılmıyordu
— bu, warm-start'ın yeniden hesaplanan zamanlamasının bazen bir bakım
penceresine denk gelip solver tarafından "infeasible" sayılıp reddedilmesine
yol açtı (bkz. docs/decision-log.md Phase 11). `baseline/scheduler.py`'deki
bakımdan-kaçınma mantığı (start'ı bakım bitimine iterek itme) buraya da
taşındı.
"""

from __future__ import annotations

from collections import defaultdict


def build_maintenance_lookup(maint_list: list[dict]) -> dict[str, list[tuple[float, float]]]:
    lookup: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for m in maint_list:
        lookup[m["machine_id"]].append((m["start"], m["end"]))
    return lookup


def replay_schedule(
    assigned_machine: dict[str, str],
    order: list[str],
    op_job: dict[str, str],
    release: dict[str, float],
    durations: dict[str, float],
    eff: dict[str, float],
    maintenance_by_machine: dict[str, list[tuple[float, float]]] | None = None,
) -> tuple[dict[str, float], dict[str, float]]:
    """`order` sırasıyla işlenir (bu sıra hem job-içi öncelik hem makine
    uygunluğuyla tutarlı olmalı — ör. bir MILP çözümünün S[o] değerlerine göre
    sıralanmış operasyon listesi, ya da bir greedy planın işlem sırası).

    Dönüş: (S, C) — saat cinsinden başlama/bitiş zamanı sözlükleri.
    """
    maintenance_by_machine = maintenance_by_machine or {}
    machine_next_free: dict[str, float] = {}
    job_ready: dict[str, float] = dict(release)
    S: dict[str, float] = {}
    C: dict[str, float] = {}

    for o in order:
        m = assigned_machine[o]
        job = op_job[o]
        duration = durations[o] / eff[m]
        start = max(machine_next_free.get(m, 0.0), job_ready[job])

        changed = True
        while changed:
            changed = False
            prospective_end = start + duration
            for ms, me in maintenance_by_machine.get(m, []):
                if start < me and prospective_end > ms:
                    start = me
                    prospective_end = start + duration
                    changed = True

        end = start + duration
        S[o] = start
        C[o] = end
        machine_next_free[m] = end
        job_ready[job] = end

    return S, C
