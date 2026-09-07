"""ML pipeline testleri — bkz. docs/decision-log.md Phase 21."""

from __future__ import annotations

import numpy as np

from data_generator.generator import generate_dataset
from ml.evaluation import evaluate_all
from ml.training import TASKS, split_features_target, train_all_models
from preprocessing.features import build_feature_table


def test_feature_table_has_expected_columns_and_no_nans():
    dataset = generate_dataset(size="small")
    table = build_feature_table(dataset)

    expected = {
        "operation_id", "required_machine_type", "product_type",
        "quantity", "priority", "sequence_no", "processing_time", "energy_consumption",
    }
    assert expected <= set(table.columns)
    assert not table.isna().any().any()


def test_split_is_reproducible():
    dataset = generate_dataset(size="small")
    table = build_feature_table(dataset)

    X_train_1, X_test_1, y_train_1, y_test_1 = split_features_target(table, task="processing_time")
    X_train_2, X_test_2, y_train_2, y_test_2 = split_features_target(table, task="processing_time")

    assert list(X_train_1.index) == list(X_train_2.index)
    assert (y_train_1.values == y_train_2.values).all()


def test_train_and_evaluate_processing_time_models():
    dataset = generate_dataset(size="small")
    table = build_feature_table(dataset)
    X_train, X_test, y_train, y_test = split_features_target(table, task="processing_time")

    models = train_all_models(X_train, y_train, task="processing_time")
    assert set(models.keys()) == {"linear_regression", "random_forest", "gradient_boosting"}

    results = evaluate_all(models, X_test, y_test)
    assert set(results.columns) == {"mae", "rmse", "r2"}
    assert np.isfinite(results.values).all()
    assert (results["mae"] >= 0).all()
    assert (results["rmse"] >= 0).all()


def test_energy_task_uses_processing_time_as_feature():
    """Phase 12 tasarım kararı: energy_consumption tahmininde processing_time
    bir feature olarak kullanılıyor (generator'daki gerçek ilişki nedeniyle)."""
    assert "processing_time" in TASKS["energy_consumption"]["numeric"]
    assert TASKS["energy_consumption"]["target"] == "energy_consumption"
