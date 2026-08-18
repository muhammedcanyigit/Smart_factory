"""Model değerlendirme — bkz. docs/decision-log.md Phase 10.

MAE (Mean Absolute Error / Ortalama Mutlak Hata), RMSE (Root Mean Squared
Error / Kök Ortalama Kare Hata), R² (belirlilik katsayısı) hesaplanır.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error


def evaluate_model(model, X_test, y_test) -> dict:
    predictions = model.predict(X_test)
    return {
        "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
        "rmse": round(float(root_mean_squared_error(y_test, predictions)), 4),
        "r2": round(float(r2_score(y_test, predictions)), 4),
    }


def evaluate_all(models: dict, X_test, y_test) -> pd.DataFrame:
    rows = []
    for name, model in models.items():
        metrics = evaluate_model(model, X_test, y_test)
        metrics["model"] = name
        rows.append(metrics)
    return pd.DataFrame(rows).set_index("model")[["mae", "rmse", "r2"]]
