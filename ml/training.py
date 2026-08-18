"""İşlem süresi tahmin modellerini eğitir — bkz. docs/decision-log.md Phase 10.

Üç model karşılaştırılır: Linear Regression (basit, açıklanabilir) →
Random Forest → Gradient Boosting (daha esnek, etkileşimleri yakalayabilir).

Kategorik sütunlar (required_machine_type, product_type) one-hot encoding ile
sayısala çevrilir; sayısal sütunlar (quantity, priority, sequence_no) olduğu
gibi kullanılır. Tüm modeller aynı ön-işleme adımını (ColumnTransformer)
paylaşır ki karşılaştırma adil olsun.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

CATEGORICAL_FEATURES = ["required_machine_type", "product_type"]
NUMERIC_FEATURES = ["quantity", "priority", "sequence_no"]
TARGET = "processing_time"

RANDOM_STATE = 42  # aynı proje çapındaki SEED — reproducibility için


def _build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="passthrough",  # NUMERIC_FEATURES olduğu gibi geçer
    )


def _build_pipelines() -> dict[str, Pipeline]:
    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE),
        "gradient_boosting": GradientBoostingRegressor(random_state=RANDOM_STATE),
    }
    return {
        name: Pipeline(steps=[("preprocess", _build_preprocessor()), ("model", model)])
        for name, model in models.items()
    }


def split_features_target(feature_table):
    X = feature_table[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y = feature_table[TARGET]
    return train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)


def train_all_models(X_train, y_train) -> dict[str, Pipeline]:
    pipelines = _build_pipelines()
    for name, pipeline in pipelines.items():
        pipeline.fit(X_train, y_train)
    return pipelines
