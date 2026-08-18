"""Tahmin modellerini eğitir — bkz. docs/decision-log.md Phase 10, Phase 12.

Üç model karşılaştırılır: Linear Regression (basit, açıklanabilir) →
Random Forest → Gradient Boosting (daha esnek, etkileşimleri yakalayabilir).

Kategorik sütunlar one-hot encoding ile sayısala çevrilir; sayısal sütunlar
olduğu gibi kullanılır. Tüm modeller aynı ön-işleme adımını (ColumnTransformer)
paylaşır ki karşılaştırma adil olsun.

Phase 10 (işlem süresi) ve Phase 12 (enerji tüketimi) aynı altyapıyı,
farklı feature/target setleriyle kullanır — bkz. TASKS sözlüğü.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

RANDOM_STATE = 42  # aynı proje çapındaki SEED — reproducibility için

# Phase 10 — işlem süresi tahmini
CATEGORICAL_FEATURES = ["required_machine_type", "product_type"]
NUMERIC_FEATURES = ["quantity", "priority", "sequence_no"]
TARGET = "processing_time"

# Phase 12 — enerji tüketimi tahmini. processing_time burada bir FEATURE (generator'da
# energy_consumption = processing_time × sabit oran × gürültü ilişkisi olduğu için,
# bkz. data_generator/generator.py). Eğitim/test'te ground-truth processing_time
# kullanılıyor; gerçek Predict->Optimize akışında (Phase 11'deki gibi) bunun yerine
# Phase 10 modelinin tahmini beslenebilir.
ENERGY_CATEGORICAL_FEATURES = CATEGORICAL_FEATURES
ENERGY_NUMERIC_FEATURES = NUMERIC_FEATURES + ["processing_time"]
ENERGY_TARGET = "energy_consumption"

TASKS = {
    "processing_time": {
        "categorical": CATEGORICAL_FEATURES,
        "numeric": NUMERIC_FEATURES,
        "target": TARGET,
    },
    "energy_consumption": {
        "categorical": ENERGY_CATEGORICAL_FEATURES,
        "numeric": ENERGY_NUMERIC_FEATURES,
        "target": ENERGY_TARGET,
    },
}


def _build_preprocessor(categorical_features: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ],
        remainder="passthrough",  # sayısal feature'lar olduğu gibi geçer
    )


def _build_pipelines(categorical_features: list[str]) -> dict[str, Pipeline]:
    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE),
        "gradient_boosting": GradientBoostingRegressor(random_state=RANDOM_STATE),
    }
    return {
        name: Pipeline(steps=[("preprocess", _build_preprocessor(categorical_features)), ("model", model)])
        for name, model in models.items()
    }


def split_features_target(feature_table, task: str = "processing_time"):
    spec = TASKS[task]
    X = feature_table[spec["categorical"] + spec["numeric"]]
    y = feature_table[spec["target"]]
    return train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)


def train_all_models(X_train, y_train, task: str = "processing_time") -> dict[str, Pipeline]:
    spec = TASKS[task]
    pipelines = _build_pipelines(spec["categorical"])
    for name, pipeline in pipelines.items():
        pipeline.fit(X_train, y_train)
    return pipelines
