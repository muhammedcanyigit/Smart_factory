"""İşlem süresi ve enerji tüketimi tahmini için feature tablosu kurar — bkz.
docs/decision-log.md Phase 10, Phase 12.

ÖNEMLİ TASARIM KISITI: Operation'ın hangi SPESİFİK makineye atanacağı henüz
bilinmiyor (o, optimizasyonun kararı — Phase 7-9). Bu yüzden Machine tablosundan
(efficiency, age gibi) doğrudan join YAPILMIYOR; yalnızca operasyon üretilirken
zaten bilinen "gerekli makine TİPİ" kullanılıyor. Bu, Phase 2'deki "nominal süre"
tasarım kararıyla (dataset.md) tutarlı.
"""

from __future__ import annotations

import pandas as pd


def build_feature_table(dataset: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """operations + jobs join edilip, ML için düz bir feature tablosu döner.

    Dönüş kolonları: operation_id, required_machine_type, product_type,
    quantity, priority, sequence_no, processing_time, energy_consumption.
    Hangi kolonların feature/target olarak kullanılacağı ml/training.py::TASKS'ta
    tanımlı (Phase 10: processing_time target; Phase 12: energy_consumption target,
    processing_time ise feature).
    """
    operations = dataset["operations"]
    jobs = dataset["jobs"][["job_id", "product_type", "quantity", "priority"]]

    table = operations.merge(jobs, on="job_id", how="left")

    return table[
        [
            "operation_id",
            "required_machine_type",
            "product_type",
            "quantity",
            "priority",
            "sequence_no",
            "processing_time",
            "energy_consumption",
        ]
    ]
