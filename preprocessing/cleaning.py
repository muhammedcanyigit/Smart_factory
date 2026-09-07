"""Veri temizleme — bkz. docs/decision-log.md Phase 22.

Sentetik veri üreticimiz (Phase 2) zaten "temiz" veri üretiyor — eksik değer,
negatif süre, yinelenen ID gibi sorunlar tasarım gereği oluşmuyor. Bu yüzden
bu dosya proje boyunca (Phase 10'a kadar) fiilen çağrılmadı.

Ama gerçek dünyada (ör. gerçek bir fabrikadan veri gelseydi) bu tarz sorunlar
olağan olur — bu modül, o senaryo için savunmacı bir doğrulama/temizleme
katmanı sağlıyor: hem "veri temizleme" kavramını somut kod olarak göstermek
hem de ileride gerçek veri entegre edilirse hazır bir ilk adım olması için.
"""

from __future__ import annotations

import pandas as pd


def clean_operations(operations: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """operations tablosunu doğrular/temizler. Dönüş: (temiz_tablo, uygulanan_düzeltmeler)."""
    report: list[str] = []
    df = operations.copy()

    before = len(df)
    df = df.drop_duplicates(subset="operation_id", keep="first")
    if len(df) < before:
        report.append(f"{before - len(df)} yinelenen operation_id satırı kaldırıldı")

    before = len(df)
    df = df.dropna(subset=["operation_id", "job_id", "required_machine_type", "processing_time", "energy_consumption"])
    if len(df) < before:
        report.append(f"{before - len(df)} satır zorunlu alanlarda eksik değer nedeniyle kaldırıldı")

    negative_duration = df["processing_time"] <= 0
    if negative_duration.any():
        n = int(negative_duration.sum())
        df = df.loc[~negative_duration].copy()
        report.append(f"{n} satır sıfır/negatif processing_time nedeniyle kaldırıldı")

    negative_energy = df["energy_consumption"] < 0
    if negative_energy.any():
        n = int(negative_energy.sum())
        df.loc[negative_energy, "energy_consumption"] = 0.0
        report.append(f"{n} satırda negatif energy_consumption 0'a kırpıldı")

    return df, report


def clean_dataset(dataset: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Şimdilik yalnızca operations'ı temizliyor — projedeki tek "kirlenmeye açık"
    sayısal tablo bu (machines/jobs/energy_prices sabit, kontrollü şekilde üretiliyor)."""
    cleaned_operations, report = clean_operations(dataset["operations"])
    cleaned = dict(dataset)
    cleaned["operations"] = cleaned_operations
    return cleaned, report
