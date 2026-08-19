"""What-If senaryo motoru — bkz. docs/decision-log.md Phase 15.

Her senaryo fonksiyonu, verilen dataset'in DEĞİŞTİRİLMİŞ bir kopyasını döner
(orijinal dataset'e dokunmaz). Böylece "senaryosuz" ve "senaryolu" sonuçlar
aynı `optimization/comparison.py::run_comparison` altyapısıyla üretilip
karşılaştırılabilir.

Kapsam dışı bırakılanlar (dürüstçe belirtiliyor, bkz. docs/decision-log.md):
- "Orders +X%" (orijinal projedeki Senaryo C): quantity'nin processing_time'a
  etkisi sadece VERİ ÜRETİMİ anında (Phase 2) hesaba katılıyor; üretim sonrası
  quantity'yi değiştirmek processing_time'ı otomatik güncellemiyor. Anlamlı bir
  versiyonu farklı bir mekanizma (yeniden üretim) gerektiriyor, kapsam dışı.
- "Capacity -X%" (Senaryo F): Phase 5'te capacity'nin aktif bir MILP kısıtı
  olmadığına karar verilmişti — bu senaryonun mevcut modelde hiçbir
  gözlemlenebilir etkisi olmaz, bu yüzden eklenmedi.
"""

from __future__ import annotations

import pandas as pd

from data_generator.generator import HORIZON_START


def _copy_dataset(dataset: dict) -> dict:
    return {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in dataset.items()}


def scenario_machine_failure(dataset: dict, machine_id: str, horizon_hours: int) -> dict:
    """Senaryo A: belirtilen makine, planlama ufkunun tamamında kullanılamaz
    hale gelir (acil/uzun bakım olarak modellenir)."""
    new_dataset = _copy_dataset(dataset)
    failure_row = pd.DataFrame(
        [
            {
                "maintenance_id": f"FAILURE_{machine_id}",
                "machine_id": machine_id,
                "start_time": HORIZON_START,
                "end_time": HORIZON_START + pd.Timedelta(hours=horizon_hours),
                "maintenance_type": "emergency",
            }
        ]
    )
    new_dataset["maintenance"] = pd.concat([new_dataset["maintenance"], failure_row], ignore_index=True)
    return new_dataset


def scenario_energy_price_change(dataset: dict, pct_change: float) -> dict:
    """Senaryo B: tüm enerji fiyatları yüzdesel değişir (ör. 0.20 = %20 artış)."""
    new_dataset = _copy_dataset(dataset)
    new_dataset["energy_prices"] = new_dataset["energy_prices"].copy()
    new_dataset["energy_prices"]["price_per_kwh"] = new_dataset["energy_prices"]["price_per_kwh"] * (1 + pct_change)
    return new_dataset


def scenario_deadline_shift(dataset: dict, hours: float) -> dict:
    """Senaryo D: tüm job deadline'ları kaydırılır (negatif = daha sıkı teslim)."""
    new_dataset = _copy_dataset(dataset)
    new_dataset["jobs"] = new_dataset["jobs"].copy()
    new_dataset["jobs"]["deadline"] = new_dataset["jobs"]["deadline"] + pd.Timedelta(hours=hours)
    return new_dataset


def scenario_maintenance_duration_change(dataset: dict, pct_change: float) -> dict:
    """Senaryo E: mevcut bakım pencerelerinin süresi yüzdesel değişir (başlangıç
    zamanı sabit kalır, bitiş kayar)."""
    new_dataset = _copy_dataset(dataset)
    maint = new_dataset["maintenance"].copy()
    if not maint.empty:
        duration = maint["end_time"] - maint["start_time"]
        maint["end_time"] = maint["start_time"] + duration * (1 + pct_change)
    new_dataset["maintenance"] = maint
    return new_dataset


SCENARIOS = {
    "machine_failure": scenario_machine_failure,
    "energy_price_change": scenario_energy_price_change,
    "deadline_shift": scenario_deadline_shift,
    "maintenance_duration_change": scenario_maintenance_duration_change,
}


def run_scenario_comparison(
    scenario_dataset: dict,
    original_dataset: dict,
    size: str,
    time_limit_seconds: int,
    config_path: str = "config/config.yaml",
) -> tuple[dict, dict]:
    """Hem orijinal hem senaryolu dataset için optimize edilmiş sonucu üretir."""
    from optimization.comparison import run_comparison

    original_metrics, _ = run_comparison(
        size=size, time_limit_seconds=time_limit_seconds, config_path=config_path, dataset=original_dataset
    )
    scenario_metrics, _ = run_comparison(
        size=size, time_limit_seconds=time_limit_seconds, config_path=config_path, dataset=scenario_dataset
    )
    return original_metrics, scenario_metrics


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    import yaml as _yaml

    from data_generator.generator import generate_dataset as _generate_dataset

    parser = argparse.ArgumentParser(description="What-If senaryo çalıştırıcı")
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()), required=True)
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small")
    parser.add_argument("--time-limit", type=int, default=120)
    parser.add_argument("--machine-id", default="M001", help="machine_failure için")
    parser.add_argument("--pct-change", type=float, default=0.20, help="energy_price_change / maintenance_duration_change için")
    parser.add_argument("--hours", type=float, default=-2.0, help="deadline_shift için (negatif = daha sıkı)")
    args = parser.parse_args()

    config = _yaml.safe_load(open("config/config.yaml"))
    horizon_hours = config["dataset"]["horizon_hours"]
    dataset = _generate_dataset(size=args.size)

    if args.scenario == "machine_failure":
        scenario_dataset = scenario_machine_failure(dataset, args.machine_id, horizon_hours)
        desc = f"Machine {args.machine_id} failure (tüm ufuk boyunca kullanılamaz)"
    elif args.scenario == "energy_price_change":
        scenario_dataset = scenario_energy_price_change(dataset, args.pct_change)
        desc = f"Energy price {'+' if args.pct_change >= 0 else ''}{args.pct_change * 100:.0f}%"
    elif args.scenario == "deadline_shift":
        scenario_dataset = scenario_deadline_shift(dataset, args.hours)
        desc = f"Deadline shift {args.hours:+.1f}h"
    else:
        scenario_dataset = scenario_maintenance_duration_change(dataset, args.pct_change)
        desc = f"Maintenance duration {'+' if args.pct_change >= 0 else ''}{args.pct_change * 100:.0f}%"

    print(f"--- What-If: {desc} ({args.size}) ---")
    print("Orijinal (senaryosuz) plan hesaplanıyor...")
    original_metrics, scenario_metrics = run_scenario_comparison(
        scenario_dataset, dataset, args.size, args.time_limit
    )

    print("\n--- KARŞILAŞTIRMA: Orijinal Optimized vs Senaryo Optimized ---")
    if scenario_metrics["Optimized"].get("feasible") is False:
        print(f"Senaryo altında optimizasyon ÇÖZÜMSÜZ (infeasible) — durum: {scenario_metrics['Optimized']['solver_status']}")
        print("Bu genellikle bir kısıt üstünde ekstra baskı (ör. tek örneği kalan bir makine tipinin tamamen kullanılamaz hale gelmesi) verildiğinde ortaya çıkar. Kendi başına bir hata değil, senaryonun sistemi zorladığının kanıtıdır.")
    elif original_metrics["Optimized"].get("feasible") is False:
        print("Orijinal (senaryosuz) plan bile çözümsüzdü — beklenmedik bir durum, kontrol edilmeli.")
    else:
        rows = [
            ("Production Time (h)", "production_time_hours"),
            ("Energy Cost ($)", "energy_cost"),
            ("Late Jobs", "late_jobs"),
            ("Avg Tardiness (h)", "avg_tardiness_hours"),
            ("Total Cost ($)", "total_cost"),
        ]
        for label, key in rows:
            before = original_metrics["Optimized"][key]
            after = scenario_metrics["Optimized"][key]
            print(f"{label:<26}{before:>12} -> {after:>12}")

    out_dir = Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"scenario_{args.scenario}_{args.size}.json", "w") as f:
        json.dump({"original": original_metrics, "scenario": scenario_metrics, "description": desc}, f, indent=2, default=str)
    print(f"\nKaydedildi: experiments/results/scenario_{args.scenario}_{args.size}.json")
