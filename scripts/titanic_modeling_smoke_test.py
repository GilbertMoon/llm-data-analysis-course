from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from titanic_app.features import (  # noqa: E402
    CATEGORICAL_FEATURES,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    RAW_INPUT_COLUMNS,
    build_model_features,
)

DATA_PATH = PROJECT_ROOT / "data" / "titanic" / "train.csv"
MODELS_DIR = PROJECT_ROOT / "models"
PIPELINE_PATH = MODELS_DIR / "titanic_final_pipeline.joblib"
CONTRACT_PATH = MODELS_DIR / "titanic_model_contract.json"


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def positive_class_probability(pipeline: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    estimator = pipeline.named_steps["model"]
    positions = np.where(estimator.classes_ == 1)[0]
    if len(positions) != 1:
        raise ValueError(f"positive class 1 not found in {estimator.classes_}")
    return pipeline.predict_proba(frame)[:, positions[0]]


def save_artifacts(final_pipeline: Pipeline) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipeline, PIPELINE_PATH)

    contract = {
        "target": "Survived",
        "positive_class": 1,
        "raw_input_columns": RAW_INPUT_COLUMNS,
        "model_feature_columns": MODEL_FEATURE_COLUMNS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "derived_features": {
            "FamilySize": "SibSp + Parch + 1",
            "IsAlone": "1 if FamilySize == 1 else 0",
        },
        "final_estimator": final_pipeline.named_steps["model"].__class__.__name__,
    }
    CONTRACT_PATH.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"saved: {PIPELINE_PATH}")
    print(f"saved: {CONTRACT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test the Titanic STEP 11-16 modeling contract."
    )
    parser.add_argument(
        "--save-artifacts",
        action="store_true",
        help="Persist the baseline pipeline and model contract under models/.",
    )
    args = parser.parse_args()

    if not DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Titanic data not found: {DATA_PATH}\n"
            "Run: python scripts/prepare_titanic_data.py"
        )

    df = pd.read_csv(DATA_PATH)
    model_source = build_model_features(df.copy())

    X = model_source[MODEL_FEATURE_COLUMNS].copy()
    y = model_source["Survived"].astype(int).copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    preprocessor = build_preprocessor()

    baseline_pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    baseline_pipeline.fit(X_train, y_train)

    additional_pipeline = Pipeline(
        [
            ("preprocessor", clone(preprocessor)),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    additional_pipeline.fit(X_train, y_train)

    baseline_pred = baseline_pipeline.predict(X_test)
    additional_pred = additional_pipeline.predict(X_test)

    baseline_accuracy = accuracy_score(y_test, baseline_pred)
    additional_accuracy = accuracy_score(y_test, additional_pred)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    baseline_cv = cross_val_score(
        baseline_pipeline,
        X_train,
        y_train,
        cv=cv,
        scoring="accuracy",
        n_jobs=-1,
    )
    additional_cv = cross_val_score(
        additional_pipeline,
        X_train,
        y_train,
        cv=cv,
        scoring="accuracy",
        n_jobs=-1,
    )

    print(f"shape: {df.shape}")
    print(f"train/test: {X_train.shape} / {X_test.shape}")
    print(f"baseline holdout accuracy: {baseline_accuracy:.4f}")
    print(f"baseline CV mean/std: {baseline_cv.mean():.4f} / {baseline_cv.std():.4f}")
    print(f"additional holdout accuracy: {additional_accuracy:.4f}")
    print(
        "additional CV mean/std: "
        f"{additional_cv.mean():.4f} / {additional_cv.std():.4f}"
    )

    _ = positive_class_probability(baseline_pipeline, X_test.head(5))

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "pipeline.joblib"
        joblib.dump(baseline_pipeline, temp_path)
        reloaded = joblib.load(temp_path)
        if not np.array_equal(
            reloaded.predict(X_test),
            baseline_pipeline.predict(X_test),
        ):
            raise RuntimeError("Persistence check failed.")

    new_passenger = pd.DataFrame(
        [
            {
                "Pclass": 3,
                "Sex": "male",
                "Age": 30.0,
                "SibSp": 0,
                "Parch": 0,
                "Fare": 10.0,
                "Embarked": "S",
            }
        ]
    )
    new_features = build_model_features(new_passenger)[MODEL_FEATURE_COLUMNS]
    new_prediction = int(baseline_pipeline.predict(new_features)[0])
    new_probability = float(
        positive_class_probability(baseline_pipeline, new_features)[0]
    )

    print(f"new passenger class: {new_prediction}")
    print(f"new passenger class-1 probability: {new_probability:.4f}")
    print("Titanic modeling smoke test: PASS")

    if args.save_artifacts:
        save_artifacts(baseline_pipeline)


if __name__ == "__main__":
    main()
