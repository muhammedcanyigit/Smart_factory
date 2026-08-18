"""Phase 10 orkestratörü: veri üret → feature tablosu kur → eğit → değerlendir.

Ayrıca eğitilmiş en iyi modeli diske kaydeder/yükler (Phase 11'de optimizasyona
tahmin beslemek için kullanılacak).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import yaml

from data_generator.generator import generate_dataset
from ml.evaluation import evaluate_all
from ml.training import split_features_target, train_all_models
from preprocessing.features import build_feature_table


def run_training_pipeline(size: str = "small", config_path: str = "config/config.yaml"):
    config = yaml.safe_load(open(config_path))
    dataset = generate_dataset(size=size, config_path=config_path)

    feature_table = build_feature_table(dataset)
    X_train, X_test, y_train, y_test = split_features_target(feature_table)

    models = train_all_models(X_train, y_train)
    results = evaluate_all(models, X_test, y_test)

    return models, results, feature_table


def save_model(model, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str):
    return joblib.load(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="İşlem süresi tahmin modeli eğitimi")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small")
    args = parser.parse_args()

    models, results, feature_table = run_training_pipeline(size=args.size)

    print(f"--- İşlem Süresi Tahmini — {args.size.upper()} ({len(feature_table)} operasyon) ---")
    print(results)

    best_model_name = results["rmse"].idxmin()
    print(f"\nEn iyi model (RMSE'ye göre): {best_model_name}")

    save_model(models[best_model_name], f"ml/models/processing_time_{args.size}.joblib")
    print(f"Kaydedildi: ml/models/processing_time_{args.size}.joblib")
