"""Phase 10 (işlem süresi) / Phase 12 (enerji tüketimi) orkestratörü:
veri üret → feature tablosu kur → eğit → değerlendir.

Ayrıca eğitilmiş en iyi modeli diske kaydeder/yükler (Phase 11'de optimizasyona
tahmin beslemek için kullanılan yapı, task="energy_consumption" için de aynı
şekilde çalışır).
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


def run_training_pipeline(size: str = "small", task: str = "processing_time", config_path: str = "config/config.yaml"):
    config = yaml.safe_load(open(config_path))
    dataset = generate_dataset(size=size, config_path=config_path)

    feature_table = build_feature_table(dataset)
    X_train, X_test, y_train, y_test = split_features_target(feature_table, task=task)

    models = train_all_models(X_train, y_train, task=task)
    results = evaluate_all(models, X_test, y_test)

    return models, results, feature_table


def save_model(model, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str):
    return joblib.load(path)


def _model_path(size: str, task: str) -> str:
    return f"ml/models/{task}_{size}.joblib"


def train_and_save_best_model(size: str, task: str = "processing_time", config_path: str = "config/config.yaml"):
    """Modeli eğitir, RMSE'ye göre en iyisini seçip diske kaydeder; (model, results,
    feature_table, best_model_name) döner. `__main__` ve `load_or_train_model` bu
    seçim mantığını paylaşır."""
    models, results, feature_table = run_training_pipeline(size=size, task=task, config_path=config_path)
    best_model_name = results["rmse"].idxmin()
    save_model(models[best_model_name], _model_path(size, task))
    return models[best_model_name], results, feature_table, best_model_name


def load_or_train_model(size: str, task: str = "processing_time", config_path: str = "config/config.yaml"):
    """Kaydedilmiş model dosyası varsa onu yükler. Yoksa (ör. taze bir `git clone`
    sonrası — `.joblib` dosyaları reproducible oldukları için `.gitignore`'da,
    repoda hiç yoktur, bkz. docs/decision-log.md) modeli o an eğitip diske
    kaydeder, sonra döner. Böylece dashboard/pipeline, elle bir ön-eğitim adımı
    (`python -m ml.prediction --size ... --task ...`) çalıştırılması gerekmeden,
    seçilen HERHANGİ bir dataset boyutuyla ilk denemede de çalışır."""
    path = _model_path(size, task)
    if Path(path).exists():
        return load_model(path)
    best_model, _, _, _ = train_and_save_best_model(size=size, task=task, config_path=config_path)
    return best_model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tahmin modeli eğitimi (işlem süresi / enerji tüketimi)")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small")
    parser.add_argument("--task", choices=["processing_time", "energy_consumption"], default="processing_time")
    args = parser.parse_args()

    _, results, feature_table, best_model_name = train_and_save_best_model(size=args.size, task=args.task)

    print(f"--- {args.task} Tahmini — {args.size.upper()} ({len(feature_table)} operasyon) ---")
    print(results)
    print(f"\nEn iyi model (RMSE'ye göre): {best_model_name}")
    print(f"Kaydedildi: {_model_path(args.size, args.task)}")
