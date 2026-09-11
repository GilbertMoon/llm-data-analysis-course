from __future__ import annotations

import pandas as pd

RAW_INPUT_COLUMNS = [
    "Pclass",
    "Sex",
    "Age",
    "SibSp",
    "Parch",
    "Fare",
    "Embarked",
]

DERIVED_FEATURES = [
    "FamilySize",
    "IsAlone",
]

MODEL_FEATURE_COLUMNS = RAW_INPUT_COLUMNS + DERIVED_FEATURES

NUMERIC_FEATURES = [
    "Age",
    "SibSp",
    "Parch",
    "Fare",
    "FamilySize",
]

CATEGORICAL_FEATURES = [
    "Pclass",
    "Sex",
    "Embarked",
    "IsAlone",
]


def build_model_features(frame: pd.DataFrame) -> pd.DataFrame:
    """고정된 row-wise 규칙만 사용해 Titanic 모델 Feature를 만든다."""
    missing = [column for column in RAW_INPUT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required raw input columns: {missing}")

    result = frame.copy()
    result["FamilySize"] = result["SibSp"] + result["Parch"] + 1
    result["IsAlone"] = (result["FamilySize"] == 1).astype(int)

    return result
