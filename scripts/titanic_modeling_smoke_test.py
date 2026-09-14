from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "titanic" / "train.csv"
MODELS_DIR = PROJECT_ROOT / "models"
BUNDLE_PATH = MODELS_DIR / "titanic_model_bundle.joblib"
CONTRACT_PATH = MODELS_DIR / "titanic_model_contract.json"

RAW_INPUT_COLUMNS = [
    "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"
]
MODEL_FEATURE_COLUMNS = RAW_INPUT_COLUMNS + ["FamilySize", "IsAlone"]
NUMERIC_FEATURES = ["Age", "SibSp", "Parch", "Fare", "FamilySize"]
CATEGORICAL_FEATURES = ["Pclass", "Sex", "Embarked", "IsAlone"]


def add_rowwise_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["FamilySize"] = result["SibSp"] + result["Parch"] + 1
    result["IsAlone"] = (result["FamilySize"] == 1).astype(int)
    return result


def fit_preprocessing(X_train: pd.DataFrame):
    numeric_imputer = SimpleImputer(strategy="median")
    categorical_imputer = SimpleImputer(strategy="most_frequent")
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    scaler = StandardScaler()

    train_num_imputed = numeric_imputer.fit_transform(X_train[NUMERIC_FEATURES])
    train_num_scaled = scaler.fit_transform(train_num_imputed)

    train_cat_imputed = categorical_imputer.fit_transform(
        X_train[CATEGORICAL_FEATURES]
    )
    train_cat_encoded = encoder.fit_transform(train_cat_imputed)

    prepared_columns = NUMERIC_FEATURES + list(
        encoder.get_feature_names_out(CATEGORICAL_FEATURES)
    )
    X_train_ready = pd.DataFrame(
        np.hstack([train_num_scaled, train_cat_encoded]),
        index=X_train.index,
        columns=prepared_columns,
    )

    return {
        "numeric_imputer": numeric_imputer,
        "categorical_imputer": categorical_imputer,
        "encoder": encoder,
        "scaler": scaler,
        "prepared_columns": prepared_columns,
        "X_train_ready": X_train_ready,
    }


def transform_features(frame: pd.DataFrame, fitted: dict) -> pd.DataFrame:
    numeric_imputed = fitted["numeric_imputer"].transform(frame[NUMERIC_FEATURES])
    numeric_scaled = fitted["scaler"].transform(numeric_imputed)

    categorical_imputed = fitted["categorical_imputer"].transform(
        frame[CATEGORICAL_FEATURES]
    )
    categorical_encoded = fitted["encoder"].transform(categorical_imputed)

    return pd.DataFrame(
        np.hstack([numeric_scaled, categorical_encoded]),
        index=frame.index,
        columns=fitted["prepared_columns"],
    )


def save_artifacts(fitted: dict, model) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    bundle = {
        "numeric_imputer": fitted["numeric_imputer"],
        "categorical_imputer": fitted["categorical_imputer"],
        "encoder": fitted["encoder"],
        "scaler": fitted["scaler"],
        "model": model,
    }
    joblib.dump(bundle, BUNDLE_PATH)

    contract = {
        "task": "binary_classification",
        "target": "Survived",
        "positive_class": 1,
        "raw_input_columns": RAW_INPUT_COLUMNS,
        "model_feature_columns": MODEL_FEATURE_COLUMNS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "prepared_feature_columns": fitted["prepared_columns"],
        "derived_features": {
            "FamilySize": "SibSp + Parch + 1",
            "IsAlone": "1 if FamilySize == 1 else 0",
        },
        "scaling": "StandardScaler",
        "final_estimator": model.__class__.__name__,
    }
    CONTRACT_PATH.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"saved: {BUNDLE_PATH}")
    print(f"saved: {CONTRACT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test Titanic STEP 11-16 without sklearn Pipeline."
    )
    parser.add_argument(
        "--save-artifacts",
        action="store_true",
        help="Persist preprocessing objects, final model, and contract under models/.",
    )
    args = parser.parse_args()

    if not DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Titanic data not found: {DATA_PATH}\n"
            "Run: python scripts/prepare_titanic_data.py"
        )

    df = pd.read_csv(DATA_PATH)
    model_source = add_rowwise_features(df)

    X = model_source[MODEL_FEATURE_COLUMNS].copy()
    y = model_source["Survived"].astype(int).copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    fitted = fit_preprocessing(X_train)
    X_train_ready = fitted["X_train_ready"]
    X_test_ready = transform_features(X_test, fitted)

    baseline_model = LogisticRegression(max_iter=1000, random_state=42)
    baseline_model.fit(X_train_ready, y_train)

    additional_model = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    additional_model.fit(X_train_ready, y_train)

    baseline_accuracy = accuracy_score(y_test, baseline_model.predict(X_test_ready))
    additional_accuracy = accuracy_score(
        y_test, additional_model.predict(X_test_ready)
    )

    print(f"shape: {df.shape}")
    print(f"train/test: {X_train.shape} / {X_test.shape}")
    print(f"baseline holdout accuracy: {baseline_accuracy:.4f}")
    print(f"additional holdout accuracy: {additional_accuracy:.4f}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "bundle.joblib"
        temp_bundle = {
            "numeric_imputer": fitted["numeric_imputer"],
            "categorical_imputer": fitted["categorical_imputer"],
            "encoder": fitted["encoder"],
            "scaler": fitted["scaler"],
            "model": baseline_model,
        }
        joblib.dump(temp_bundle, temp_path)
        reloaded = joblib.load(temp_path)
        if reloaded["model"].__class__.__name__ != "LogisticRegression":
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
    new_features = add_rowwise_features(new_passenger)[MODEL_FEATURE_COLUMNS]
    new_ready = transform_features(new_features, fitted)
    new_prediction = int(baseline_model.predict(new_ready)[0])
    positive_index = list(baseline_model.classes_).index(1)
    new_probability = float(
        baseline_model.predict_proba(new_ready)[0][positive_index]
    )

    print(f"new passenger class: {new_prediction}")
    print(f"new passenger class-1 probability: {new_probability:.4f}")
    print("Titanic modeling smoke test: PASS")

    if args.save_artifacts:
        save_artifacts(fitted, baseline_model)


if __name__ == "__main__":
    main()
