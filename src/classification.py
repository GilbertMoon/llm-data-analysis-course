"""Chapter 10 leakage-aware classification analysis utilities.

The workflow protects target definition, merge integrity, model selection,
threshold selection, final test independence, and public-result privacy.

Core contract:
1. completed=0 and cancelled=1 only; other statuses are excluded,
2. validate line_total = quantity * unit_price before aggregation,
3. fail on broken order/customer joins instead of silently filling unmatched rows,
4. keep target, identifiers, and post-outcome fields out of features,
5. learn preprocessing inside sklearn Pipelines,
6. select the model on validation data,
7. select the probability threshold on validation data,
8. freeze model and threshold before final test evaluation,
9. separate identifier-bearing internal outputs from public predictions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET_COLUMN = "is_cancelled"
ALLOWED_TARGET_STATUSES = {"completed", "cancelled"}

CANDIDATE_NUMERIC_FEATURES = [
    "age",
    "item_count",
    "total_quantity",
    "order_amount",
    "order_month",
    "order_dayofweek",
    "days_since_signup",
]
CANDIDATE_CATEGORICAL_FEATURES = [
    "gender",
    "city",
    "payment_method",
]

FORBIDDEN_FEATURES = {
    "order_status",
    TARGET_COLUMN,
    "order_id",
    "customer_id",
    "product_id",
    "cancel_reason",
    "cancelled_at",
}
FORBIDDEN_REASONS = {
    "order_status": "예측 결과와 직접 연결되는 주문 상태",
    TARGET_COLUMN: "예측 대상 자체",
    "order_id": "주문 식별자",
    "customer_id": "고객 식별자",
    "product_id": "주문 상세 식별 정보",
    "cancel_reason": "취소 이후 생성되는 사후 정보",
    "cancelled_at": "취소 이후 생성되는 사후 정보",
}
LEAKAGE_COLUMNS = {"order_status", TARGET_COLUMN}

REQUIRED_COLUMNS = {
    "customers": {"customer_id", "gender", "age", "city", "signup_date"},
    "orders": {
        "order_id",
        "customer_id",
        "order_date",
        "order_status",
        "payment_method",
    },
    "order_items": {
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    },
}


def make_one_hot_encoder() -> OneHotEncoder:
    """Return a dense encoder compatible with multiple sklearn versions."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_classification_source_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """Load Chapter10 validated processed inputs without falling back to raw data."""
    input_dir = Path(processed_dir)
    file_map = {
        "customers": input_dir / "customers_clean.csv",
        "orders": input_dir / "orders_clean.csv",
        "order_items": input_dir / "order_items_clean.csv",
    }
    missing = [path for path in file_map.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Chapter10 모델링 입력이 없습니다. 먼저 "
            "`python scripts/prepare_ch10_data.py`를 실행하세요. "
            + "누락 파일: "
            + ", ".join(str(path) for path in missing)
        )
    return {name: pd.read_csv(path) for name, path in file_map.items()}


def validate_required_columns(datasets: dict[str, pd.DataFrame]) -> None:
    """Fail fast when required datasets or columns are missing."""
    missing_datasets = sorted(set(REQUIRED_COLUMNS) - set(datasets))
    if missing_datasets:
        raise KeyError(f"필수 데이터셋이 없습니다: {missing_datasets}")

    for name, required in REQUIRED_COLUMNS.items():
        missing = sorted(required - set(datasets[name].columns))
        if missing:
            raise KeyError(f"{name}에 필요한 컬럼이 없습니다: {missing}")


def validate_feature_columns(feature_columns: Iterable[str]) -> None:
    """Reject target, identifier, and post-outcome fields from model input."""
    columns = list(feature_columns)
    forbidden = sorted(set(columns) & FORBIDDEN_FEATURES)
    if forbidden:
        raise ValueError(f"입력값에 누수/식별 위험 컬럼이 있습니다: {forbidden}")
    duplicates = pd.Index(columns)[pd.Index(columns).duplicated()].tolist()
    if duplicates:
        raise ValueError(f"입력값 목록에 중복 컬럼이 있습니다: {duplicates}")


def _require_unique_key(df: pd.DataFrame, key: str, dataset: str) -> None:
    missing_count = int(df[key].isna().sum())
    duplicate_count = int(df[key].duplicated().sum())
    if missing_count or duplicate_count:
        raise ValueError(
            f"{dataset}.{key} 검증 실패: "
            f"missing={missing_count}, duplicate={duplicate_count}"
        )


def build_order_item_features(order_items: pd.DataFrame) -> pd.DataFrame:
    """Validate line totals and aggregate order items to one row per order."""
    required = {"order_id", "product_id", "quantity", "unit_price"}
    missing = sorted(required - set(order_items.columns))
    if missing:
        raise KeyError(f"order_items에 필요한 컬럼이 없습니다: {missing}")

    items = order_items.copy()
    invalid_key_or_value = items[
        ["order_id", "product_id", "quantity", "unit_price"]
    ].isna().any(axis=1)
    if invalid_key_or_value.any():
        raise ValueError(
            "주문 특징을 만들 수 없는 주문 상세 행이 있습니다: "
            f"{int(invalid_key_or_value.sum())}건"
        )

    items["quantity"] = pd.to_numeric(items["quantity"], errors="coerce")
    items["unit_price"] = pd.to_numeric(items["unit_price"], errors="coerce")
    if items[["quantity", "unit_price"]].isna().any(axis=None):
        raise ValueError("quantity 또는 unit_price에 숫자 변환 실패가 있습니다.")
    if (items["quantity"] <= 0).any() or (items["unit_price"] <= 0).any():
        raise ValueError("quantity와 unit_price는 0보다 커야 합니다.")

    expected_line_total = items["quantity"] * items["unit_price"]
    if "line_total" in items.columns:
        items["line_total"] = pd.to_numeric(items["line_total"], errors="coerce")
        if items["line_total"].isna().any():
            raise ValueError("order_items.line_total에 숫자 변환 실패가 있습니다.")
        mismatch = (items["line_total"] - expected_line_total).abs().gt(1e-6)
        if mismatch.any():
            raise ValueError(
                "line_total과 quantity × unit_price가 일치하지 않는 행이 있습니다: "
                f"{int(mismatch.sum())}건"
            )
    else:
        items["line_total"] = expected_line_total

    if (items["line_total"] <= 0).any():
        raise ValueError("line_total에 0 이하 값이 있습니다.")

    features = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_count=("product_id", "size"),
            total_quantity=("quantity", "sum"),
            order_amount=("line_total", "sum"),
        )
        .sort_values("order_id")
        .reset_index(drop=True)
    )
    if features["order_id"].duplicated().any():
        raise ValueError("주문 단위 특징이 order_id당 한 행이 아닙니다.")
    return features


def _checked_left_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    on: str,
    validate: str,
    right_label: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Run a validated left merge and fail on row loss/growth or unmatched rows."""
    before_rows = len(left)
    merged = left.merge(
        right,
        on=on,
        how="left",
        validate=validate,
        indicator=True,
    )
    after_rows = len(merged)
    unmatched_count = int(merged["_merge"].eq("left_only").sum())
    row_count_preserved = before_rows == after_rows

    check = {
        "merge": f"{on} → {right_label}",
        "before_rows": before_rows,
        "after_rows": after_rows,
        "row_count_preserved": row_count_preserved,
        "unmatched_count": unmatched_count,
        "status": (
            "PASS"
            if row_count_preserved and unmatched_count == 0
            else "FAIL"
        ),
    }

    if not row_count_preserved or unmatched_count:
        raise ValueError(
            f"{on} → {right_label} 병합 검증 실패: "
            f"before={before_rows}, after={after_rows}, "
            f"unmatched={unmatched_count}"
        )

    return merged.drop(columns="_merge"), check


def build_classification_dataset(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    list[str],
    list[str],
    pd.DataFrame,
    pd.DataFrame,
]:
    """Build strict one-row-per-order binary-classification data."""
    datasets = {
        "customers": customers.copy(),
        "orders": orders.copy(),
        "order_items": order_items.copy(),
    }
    validate_required_columns(datasets)

    customers_data = datasets["customers"]
    orders_data = datasets["orders"]
    items_data = datasets["order_items"]

    _require_unique_key(customers_data, "customer_id", "customers")
    _require_unique_key(orders_data, "order_id", "orders")

    required_order_values = ["order_id", "customer_id", "order_date", "order_status"]
    missing_order_values = orders_data[required_order_values].isna().any(axis=1)
    if missing_order_values.any():
        raise ValueError(
            "orders 필수값에 결측치가 있습니다: "
            f"{int(missing_order_values.sum())}건"
        )

    orders_data["order_date"] = pd.to_datetime(
        orders_data["order_date"], errors="coerce"
    )
    if orders_data["order_date"].isna().any():
        raise ValueError(
            "order_date 날짜 변환 실패가 있습니다: "
            f"{int(orders_data['order_date'].isna().sum())}건"
        )

    status_scope = (
        orders_data["order_status"]
        .value_counts(dropna=False)
        .rename_axis("order_status")
        .reset_index(name="order_count")
    )
    status_scope["used_for_binary_target"] = status_scope[
        "order_status"
    ].isin(ALLOWED_TARGET_STATUSES)

    binary_orders = orders_data[
        orders_data["order_status"].isin(ALLOWED_TARGET_STATUSES)
    ].copy()
    if binary_orders.empty:
        raise ValueError(
            "completed 또는 cancelled 주문이 없어 분류 데이터를 만들 수 없습니다."
        )

    binary_orders[TARGET_COLUMN] = (
        binary_orders["order_status"].eq("cancelled").astype(int)
    )
    target_counts = binary_orders[TARGET_COLUMN].value_counts()
    if set(target_counts.index) != {0, 1}:
        raise ValueError(
            "분류 학습에는 completed와 cancelled 주문이 모두 필요합니다."
        )
    if int(target_counts.min()) < 5:
        raise ValueError(
            "각 클래스에 최소 5개 이상의 주문이 필요합니다. "
            f"현재 클래스별 건수: {target_counts.to_dict()}"
        )

    order_item_features = build_order_item_features(items_data)
    model_data, order_merge_check = _checked_left_merge(
        binary_orders,
        order_item_features,
        on="order_id",
        validate="one_to_one",
        right_label="order_item_features",
    )

    customer_lookup = customers_data[
        ["customer_id", "gender", "age", "city", "signup_date"]
    ].copy()
    customer_lookup["signup_date"] = pd.to_datetime(
        customer_lookup["signup_date"], errors="coerce"
    )
    if customer_lookup["signup_date"].isna().any():
        raise ValueError(
            "customers.signup_date 날짜 변환 실패가 있습니다: "
            f"{int(customer_lookup['signup_date'].isna().sum())}건"
        )

    model_data, customer_merge_check = _checked_left_merge(
        model_data,
        customer_lookup,
        on="customer_id",
        validate="many_to_one",
        right_label="customers",
    )

    model_data["age"] = pd.to_numeric(model_data["age"], errors="coerce")
    model_data["order_month"] = model_data["order_date"].dt.month
    model_data["order_dayofweek"] = model_data["order_date"].dt.dayofweek
    model_data["days_since_signup"] = (
        model_data["order_date"] - model_data["signup_date"]
    ).dt.days

    negative_days = model_data["days_since_signup"].lt(0)
    if negative_days.any():
        raise ValueError(
            "signup_date가 order_date보다 늦은 주문이 있습니다: "
            f"{int(negative_days.sum())}건"
        )

    numeric_features = [
        column
        for column in CANDIDATE_NUMERIC_FEATURES
        if column in model_data.columns and model_data[column].notna().any()
    ]
    categorical_features = [
        column
        for column in CANDIDATE_CATEGORICAL_FEATURES
        if column in model_data.columns and model_data[column].notna().any()
    ]
    features = numeric_features + categorical_features
    if not features:
        raise ValueError("사용 가능한 입력 feature가 없습니다.")
    validate_feature_columns(features)

    merge_checks = pd.DataFrame([order_merge_check, customer_merge_check])
    excluded_rows = int(
        status_scope.loc[
            ~status_scope["used_for_binary_target"], "order_count"
        ].sum()
    )
    data_quality_checks = pd.DataFrame(
        {
            "check_item": [
                "binary_target_rows",
                "completed_rows",
                "cancelled_rows",
                "excluded_status_rows",
                "line_total_mismatch",
                "negative_days_since_signup",
                "missing_order_item_features",
                "missing_customer_match",
            ],
            "count": [
                len(model_data),
                int(model_data[TARGET_COLUMN].eq(0).sum()),
                int(model_data[TARGET_COLUMN].eq(1).sum()),
                excluded_rows,
                0,
                0,
                order_merge_check["unmatched_count"],
                customer_merge_check["unmatched_count"],
            ],
        }
    )
    status_checks = status_scope.assign(
        check_item=lambda frame: "status_scope:" + frame["order_status"].astype(str),
        count=lambda frame: frame["order_count"],
    )[["check_item", "count"]]

    return (
        model_data.sort_values(["order_date", "order_id"]).reset_index(drop=True),
        numeric_features,
        categorical_features,
        merge_checks,
        pd.concat([data_quality_checks, status_checks], ignore_index=True),
    )


def build_feature_audit(
    numeric_features: list[str],
    categorical_features: list[str],
) -> pd.DataFrame:
    """Document selected features and explicitly forbidden fields."""
    selected = numeric_features + categorical_features
    validate_feature_columns(selected)

    rows = [
        {
            "column": column,
            "selected": True,
            "role": "allowed_feature",
            "reason": "교육용 예측 시점에 사용 가능하다고 가정",
        }
        for column in selected
    ]
    rows.extend(
        {
            "column": column,
            "selected": False,
            "role": "forbidden",
            "reason": FORBIDDEN_REASONS[column],
        }
        for column in sorted(FORBIDDEN_FEATURES)
    )
    return pd.DataFrame(rows)


def target_distribution(model_data: pd.DataFrame) -> pd.DataFrame:
    """Return target class counts and ratios."""
    counts = model_data[TARGET_COLUMN].value_counts(dropna=False).sort_index()
    ratios = (
        model_data[TARGET_COLUMN]
        .value_counts(normalize=True, dropna=False)
        .sort_index()
    )
    labels = {0: "completed", 1: "cancelled"}
    return pd.DataFrame(
        {
            TARGET_COLUMN: counts.index,
            "class_label": [labels.get(value, str(value)) for value in counts.index],
            "count": counts.values,
            "ratio": ratios.round(4).values,
        }
    )


def split_train_validation_test(
    model_data: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
    *,
    test_size: float = 0.2,
    validation_size: float = 0.2,
    random_state: int = 42,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
    pd.Series,
    pd.Series,
    list[str],
]:
    """Create educational stratified train/validation/test splits."""
    if test_size <= 0 or validation_size <= 0:
        raise ValueError("test_size와 validation_size는 0보다 커야 합니다.")
    if test_size + validation_size >= 1:
        raise ValueError("test_size와 validation_size의 합은 1보다 작아야 합니다.")

    features = numeric_features + categorical_features
    validate_feature_columns(features)
    X = model_data[features].copy()
    y = model_data[TARGET_COLUMN].copy()

    if set(y.dropna().unique()) != {0, 1}:
        raise ValueError("이진 분류에는 0과 1 두 타깃 클래스가 필요합니다.")

    X_train_valid, X_test, y_train_valid, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
    validation_ratio = validation_size / (1 - test_size)
    X_train, X_valid, y_train, y_valid = train_test_split(
        X_train_valid,
        y_train_valid,
        test_size=validation_ratio,
        random_state=random_state,
        stratify=y_train_valid,
    )

    for split_name, target in {
        "train": y_train,
        "validation": y_valid,
        "test": y_test,
    }.items():
        if set(target.unique()) != {0, 1}:
            raise ValueError(
                f"{split_name} 데이터에 두 클래스가 모두 포함되지 않았습니다."
            )

    return (
        X_train,
        X_valid,
        X_test,
        y_train,
        y_valid,
        y_test,
        features,
    )


def build_split_summary(
    y_train: pd.Series,
    y_valid: pd.Series,
    y_test: pd.Series,
) -> pd.DataFrame:
    """Summarize class counts and ratios for each split."""
    rows: list[dict[str, object]] = []
    for split_name, target in {
        "train": y_train,
        "validation": y_valid,
        "test": y_test,
    }.items():
        counts = target.value_counts().sort_index()
        total = len(target)
        for class_value in [0, 1]:
            count = int(counts.get(class_value, 0))
            rows.append(
                {
                    "split": split_name,
                    TARGET_COLUMN: class_value,
                    "class_label": (
                        "cancelled" if class_value == 1 else "completed"
                    ),
                    "count": count,
                    "ratio": round(count / total, 4) if total else 0,
                }
            )
    return pd.DataFrame(rows)


def make_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    """Create train-only numeric and categorical preprocessing."""
    transformers: list[tuple[str, Pipeline, list[str]]] = []

    if numeric_features:
        numeric = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("num", numeric, numeric_features))

    if categorical_features:
        categorical = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", make_one_hot_encoder()),
            ]
        )
        transformers.append(("cat", categorical, categorical_features))

    if not transformers:
        raise ValueError("전처리할 feature가 없습니다.")
    return ColumnTransformer(transformers=transformers)


def make_classification_models(
    numeric_features: list[str],
    categorical_features: list[str],
    random_state: int = 42,
) -> dict[str, Pipeline]:
    """Create the fixed baseline and candidate models."""
    return {
        "Dummy Most Frequent": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(numeric_features, categorical_features),
                ),
                ("model", DummyClassifier(strategy="most_frequent")),
            ]
        ),
        "Logistic Regression": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(numeric_features, categorical_features),
                ),
                (
                    "model",
                    LogisticRegression(max_iter=1000, class_weight="balanced"),
                ),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(numeric_features, categorical_features),
                ),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=200,
                        random_state=random_state,
                        class_weight="balanced",
                    ),
                ),
            ]
        ),
    }


def evaluate_classification_predictions(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """Evaluate predictions with accuracy, precision, recall, and F1."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def train_and_compare_on_validation(
    X_train: pd.DataFrame,
    X_valid: pd.DataFrame,
    y_train: pd.Series,
    y_valid: pd.Series,
    numeric_features: list[str],
    categorical_features: list[str],
    random_state: int = 42,
) -> tuple[
    dict[str, Pipeline],
    pd.DataFrame,
    dict[str, np.ndarray],
    dict[str, np.ndarray],
]:
    """Fit on train and compare fixed candidates on validation only."""
    validate_feature_columns(X_train.columns)
    if list(X_train.columns) != list(X_valid.columns):
        raise ValueError("Train과 Validation 입력 컬럼 구성이 다릅니다.")

    models = make_classification_models(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        random_state=random_state,
    )
    rows: list[dict[str, Any]] = []
    predictions: dict[str, np.ndarray] = {}
    probabilities: dict[str, np.ndarray] = {}

    for model_name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_valid)
        rows.append(
            {
                "model": model_name,
                "evaluation_split": "validation",
                **evaluate_classification_predictions(y_valid, y_pred),
            }
        )
        predictions[model_name] = y_pred
        if hasattr(model, "predict_proba"):
            probabilities[model_name] = model.predict_proba(X_valid)[:, 1]

    comparison = (
        pd.DataFrame(rows)
        .sort_values(
            ["f1", "recall", "precision", "model"],
            ascending=[False, False, False, True],
        )
        .reset_index(drop=True)
    )
    return models, comparison, predictions, probabilities


def select_validation_model(validation_comparison: pd.DataFrame) -> str:
    """Freeze the best non-dummy model using validation metrics only."""
    required = {"model", "f1", "recall", "precision"}
    missing = sorted(required - set(validation_comparison.columns))
    if missing:
        raise KeyError(f"Validation 모델 비교표에 필요한 컬럼이 없습니다: {missing}")

    candidates = validation_comparison.loc[
        ~validation_comparison["model"].eq("Dummy Most Frequent")
    ].sort_values(
        ["f1", "recall", "precision", "model"],
        ascending=[False, False, False, True],
    )
    if candidates.empty:
        raise ValueError("선택할 비베이스라인 모델이 없습니다.")
    return str(candidates.iloc[0]["model"])


def threshold_metrics(
    y_true: pd.Series,
    y_proba: np.ndarray,
    thresholds: list[float] | None = None,
) -> pd.DataFrame:
    """Evaluate probability thresholds on validation data."""
    thresholds = thresholds or [
        round(value, 2) for value in np.arange(0.2, 0.81, 0.05)
    ]
    rows = []
    for threshold in thresholds:
        y_pred = (y_proba >= threshold).astype(int)
        rows.append(
            {
                "threshold": float(threshold),
                **evaluate_classification_predictions(y_true, y_pred),
            }
        )
    return pd.DataFrame(rows)


def choose_threshold(
    threshold_df: pd.DataFrame,
    *,
    default_threshold: float = 0.5,
) -> float:
    """Choose validation threshold by F1, recall, precision, then lower threshold."""
    if threshold_df.empty:
        return default_threshold
    ranked = threshold_df.sort_values(
        ["f1", "recall", "precision", "threshold"],
        ascending=[False, False, False, True],
    )
    return float(ranked.iloc[0]["threshold"])


def build_selection_summary(
    selected_model_name: str,
    selected_threshold: float,
    validation_comparison: pd.DataFrame,
    threshold_df: pd.DataFrame,
) -> pd.DataFrame:
    """Record that model and threshold selection occurred on validation data."""
    model_row = validation_comparison.loc[
        validation_comparison["model"].eq(selected_model_name)
    ]
    threshold_match = np.isclose(
        threshold_df["threshold"].astype(float).to_numpy(),
        float(selected_threshold),
    )
    if model_row.empty or not threshold_match.any():
        raise ValueError("선택 모델 또는 임계값이 validation evidence에 없습니다.")
    return pd.DataFrame(
        [
            {
                "selection_item": "model",
                "value": selected_model_name,
                "selected_on": "validation",
                "criterion": "f1 → recall → precision",
            },
            {
                "selection_item": "threshold",
                "value": selected_threshold,
                "selected_on": "validation",
                "criterion": "f1 → recall → precision → lower threshold",
            },
        ]
    )


def final_test_evaluation(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    *,
    threshold: float,
    model_name: str | None = None,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Evaluate one frozen model/threshold pair on final test.

    Chapter 10 legacy callers omit ``model_name`` and keep the historical
    ``evaluation_split='test'`` label. Chapter 15 supplies ``model_name`` and
    receives explicit frozen-before-test evidence.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold는 0과 1 사이여야 합니다.")
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    row: dict[str, Any] = {
        "evaluation_split": "test_final" if model_name is not None else "test",
        "threshold": threshold,
        "selection_status": "frozen_before_test",
        **evaluate_classification_predictions(y_test, y_pred),
    }
    if model_name is not None:
        row = {"model": model_name, **row}
    return y_pred, y_proba, pd.DataFrame([row])


def confusion_matrix_dataframe(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> pd.DataFrame:
    """Return a readable binary confusion matrix."""
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return pd.DataFrame(
        matrix,
        index=["actual_completed", "actual_cancelled"],
        columns=["pred_completed", "pred_cancelled"],
    )


def classification_report_dataframe(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> pd.DataFrame:
    """Return sklearn classification_report as a DataFrame."""
    report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1],
        target_names=["completed", "cancelled"],
        zero_division=0,
        output_dict=True,
    )
    return pd.DataFrame(report).T.reset_index().rename(columns={"index": "label"})


def create_prediction_result(
    y_test: pd.Series,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
    *,
    model_name: str,
    threshold: float,
    source_index: pd.Index | None = None,
) -> pd.DataFrame:
    """Create prediction evidence with optional internal source traceability.

    Chapter 10 can pass ``source_index`` for an internal-only artifact. Chapter
    15 omits it, so the returned table is public-safe by construction.
    """
    if len(y_test) != len(y_pred) or len(y_pred) != len(y_proba):
        raise ValueError("테스트 실제값·예측값·확률의 길이가 일치하지 않습니다.")
    if source_index is not None and len(source_index) != len(y_test):
        raise ValueError("source_index와 테스트 결과 길이가 일치하지 않습니다.")

    result = pd.DataFrame(
        {
            "record_id": [
                f"test_{position:04d}" for position in range(1, len(y_test) + 1)
            ],
            "actual_is_cancelled": y_test.to_numpy(),
            "predicted_is_cancelled": y_pred,
            "cancel_probability": y_proba,
            "model": model_name,
            "threshold": threshold,
        }
    )
    if source_index is not None:
        result.insert(1, "source_index", source_index.to_numpy())
    return result


def public_prediction_result(prediction_result: pd.DataFrame) -> pd.DataFrame:
    """Remove internal source references from public predictions."""
    public_columns = [
        "record_id",
        "actual_is_cancelled",
        "predicted_is_cancelled",
        "cancel_probability",
        "model",
        "threshold",
    ]
    return prediction_result[public_columns].copy()


def build_classification_checklist() -> pd.DataFrame:
    """Return the human-review checklist for classification and LLM code."""
    items = [
        "completed와 cancelled만 사용해 이진 타깃을 만들었는가?",
        "refunded 등 다른 상태를 0 클래스에 섞지 않았는가?",
        "예측 시점과 feature 가용성 가정을 설명할 수 있는가?",
        "line_total = quantity × unit_price를 검증했는가?",
        "병합에 validate를 사용하고 미매칭 0건을 확인했는가?",
        "order_status, target, ID, 사후 정보를 feature에서 제외했는가?",
        "train, validation, test를 분리했는가?",
        "모델과 threshold는 validation에서 선택했는가?",
        "모델과 threshold를 고정한 뒤 test를 한 번만 사용했는가?",
        "Dummy 기준 모델과 비교했는가?",
        "accuracy 외 precision, recall, F1과 FP/FN을 함께 확인했는가?",
        "공개 prediction에서 내부 source index와 식별자를 제거했는가?",
        "random split의 교육용 한계를 기록했는가?",
        "모델 결과를 취소 원인으로 단정하지 않았는가?",
    ]
    return pd.DataFrame({"check_item": items, "status": ["□"] * len(items)})


def build_classification_validation(
    *,
    model_data: pd.DataFrame,
    features: list[str],
    merge_checks: pd.DataFrame,
    y_train: pd.Series,
    y_valid: pd.Series,
    y_test: pd.Series,
    validation_comparison: pd.DataFrame,
    selected_model_name: str,
    threshold_df: pd.DataFrame,
    selected_threshold: float,
    test_metrics: pd.DataFrame | None = None,
    prediction_result: pd.DataFrame | None = None,
    prediction_result_public: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create machine-checkable evidence for Chapter 10 and Chapter 15.

    ``prediction_result_public`` is retained for the Chapter 10 pipeline.
    Chapter 15 passes ``prediction_result`` and ``test_metrics`` so the final
    test frozen-decision contract is also validated.
    """
    target_values = set(model_data[TARGET_COLUMN].dropna().unique())
    feature_forbidden = sorted(set(features) & set(FORBIDDEN_FEATURES))
    merge_pass = bool(
        not merge_checks.empty
        and merge_checks["row_count_preserved"].eq(True).all()
        and merge_checks["unmatched_count"].eq(0).all()
    )
    split_has_both = all(
        set(target.unique()) == {0, 1}
        for target in [y_train, y_valid, y_test]
    )
    selected_in_validation = bool(
        selected_model_name in set(validation_comparison["model"])
        and selected_model_name != "Dummy Most Frequent"
    )
    threshold_in_validation = bool(
        np.isclose(
            threshold_df["threshold"].astype(float).to_numpy(),
            float(selected_threshold),
        ).any()
    )

    public_frame = prediction_result if prediction_result is not None else prediction_result_public
    public_forbidden_columns = {
        "source_index",
        "order_id",
        "customer_id",
        "product_id",
        "name",
        "email",
        "phone",
        "address",
    }
    public_leak = (
        sorted(public_forbidden_columns & set(public_frame.columns))
        if public_frame is not None
        else ["prediction_result_missing"]
    )

    rows: list[dict[str, object]] = [
        {
            "check": "target_exactly_completed_cancelled",
            "value": sorted(target_values),
            "status": "PASS" if target_values == {0, 1} else "FAIL",
        },
        {
            "check": "forbidden_feature_overlap",
            "value": len(feature_forbidden),
            "status": "PASS" if not feature_forbidden else "FAIL",
        },
        {
            "check": "merge_rows_and_matches",
            "value": merge_pass,
            "status": "PASS" if merge_pass else "FAIL",
        },
        {
            "check": "all_splits_have_both_classes",
            "value": split_has_both,
            "status": "PASS" if split_has_both else "FAIL",
        },
        {
            "check": "model_selected_on_validation",
            "value": selected_in_validation,
            "status": "PASS" if selected_in_validation else "FAIL",
        },
        {
            "check": "threshold_selected_on_validation",
            "value": threshold_in_validation,
            "status": "PASS" if threshold_in_validation else "FAIL",
        },
        {
            "check": "public_prediction_identifier_columns",
            "value": ",".join(public_leak) if public_leak else "none",
            "status": "PASS" if not public_leak else "FAIL",
        },
    ]

    if test_metrics is not None:
        test_is_final = bool(
            len(test_metrics) == 1
            and "evaluation_split" in test_metrics.columns
            and test_metrics["evaluation_split"].eq("test_final").all()
            and "selection_status" in test_metrics.columns
            and test_metrics["selection_status"].eq("frozen_before_test").all()
        )
        rows.append(
            {
                "check": "test_used_as_final_evaluation",
                "value": test_is_final,
                "status": "PASS" if test_is_final else "FAIL",
            }
        )

    validation = pd.DataFrame(rows)
    failed = validation.loc[validation["status"].eq("FAIL")]
    if not failed.empty:
        raise ValueError(
            "분류 분석 핵심 검증에 실패했습니다:\n"
            + failed.to_string(index=False)
        )
    return validation


def build_classification_report_text(
    model_data: pd.DataFrame,
    target_dist: pd.DataFrame,
    feature_audit: pd.DataFrame,
    merge_checks: pd.DataFrame,
    split_summary: pd.DataFrame,
    validation_comparison: pd.DataFrame,
    selected_model_name: str,
    selected_threshold: float,
    threshold_df: pd.DataFrame,
    test_metrics: pd.DataFrame,
    confusion_df: pd.DataFrame,
    validation: pd.DataFrame,
    checklist: pd.DataFrame,
) -> str:
    """Build the public Markdown summary report."""
    return f"""# Chapter 10 분류 분석 요약 보고서

## 1. 분석 목적과 타깃
완료 주문과 취소 주문만 사용해 주문 취소 여부를 예측합니다.

- completed = 0
- cancelled = 1
- refunded 및 기타 상태 = 모델링 범위 제외

## 2. 모델링 데이터
- 행 수: {model_data.shape[0]}
- 예측 대상: {TARGET_COLUMN}

## 3. 타깃 클래스 분포
```text
{target_dist.to_string(index=False)}
```

## 4. Feature Audit
```text
{feature_audit.to_string(index=False)}
```

## 5. 병합 검증
```text
{merge_checks.to_string(index=False)}
```

## 6. Train / Validation / Test
```text
{split_summary.to_string(index=False)}
```

## 7. Validation 모델 비교
```text
{validation_comparison.to_string(index=False)}
```

선택 모델: **{selected_model_name}**

## 8. Validation Threshold 비교
```text
{threshold_df.to_string(index=False)}
```

선택 threshold: **{selected_threshold:.2f}**

## 9. Final Test
```text
{test_metrics.to_string(index=False)}
```

## 10. Confusion Matrix
```text
{confusion_df.to_string()}
```

## 11. 자동 Validation Evidence
```text
{validation.to_string(index=False)}
```

## 12. 사람 검토 체크리스트
```text
{checklist.to_string(index=False)}
```

## 13. 해석 시 주의사항
- 모델과 threshold는 Validation에서 선택했습니다.
- Final Test는 선택이 끝난 뒤 마지막 평가에만 사용했습니다.
- accuracy뿐 아니라 precision, recall, F1과 FP/FN을 함께 봅니다.
- random split은 교육용 설계이며 실제 운영 전에는 out-of-time 평가가 필요합니다.
- 모델이 학습한 예측 패턴을 취소의 원인으로 단정하지 않습니다.
- 공개 prediction에는 내부 source index나 원본 식별자를 포함하지 않습니다.
"""


def save_classification_outputs(
    *,
    model_data: pd.DataFrame,
    target_dist: pd.DataFrame,
    feature_audit: pd.DataFrame,
    merge_checks: pd.DataFrame,
    data_quality_checks: pd.DataFrame,
    split_summary: pd.DataFrame,
    validation_comparison: pd.DataFrame,
    threshold_df: pd.DataFrame,
    test_metrics: pd.DataFrame,
    prediction_result_internal: pd.DataFrame,
    prediction_result_public: pd.DataFrame,
    confusion_df: pd.DataFrame,
    report_df: pd.DataFrame,
    validation: pd.DataFrame,
    checklist: pd.DataFrame,
    selected_model_name: str,
    selected_threshold: float,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """Save internal evidence and privacy-safe public outputs separately."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    internal_columns = [
        column
        for column in [
            "order_id",
            "customer_id",
            TARGET_COLUMN,
            *CANDIDATE_NUMERIC_FEATURES,
            *CANDIDATE_CATEGORICAL_FEATURES,
        ]
        if column in model_data.columns
    ]
    internal_model_data = model_data[internal_columns].copy()

    paths = {
        "model_data_internal": (
            output_dir / "ch10_classification_model_data_internal.csv"
        ),
        "target_distribution": output_dir / "ch10_target_distribution.csv",
        "feature_audit": output_dir / "ch10_feature_audit.csv",
        "merge_checks": output_dir / "ch10_merge_checks.csv",
        "data_quality_checks": output_dir / "ch10_data_quality_checks.csv",
        "split_summary": output_dir / "ch10_split_summary.csv",
        "validation_comparison": (
            output_dir / "ch10_validation_model_comparison.csv"
        ),
        "threshold_metrics": (
            output_dir / "ch10_validation_threshold_metrics.csv"
        ),
        "test_metrics": output_dir / "ch10_test_metrics.csv",
        "predictions_internal": (
            output_dir / "ch10_classification_predictions_internal.csv"
        ),
        "predictions": output_dir / "ch10_classification_predictions.csv",
        "confusion_matrix": output_dir / "ch10_confusion_matrix.csv",
        "classification_report": (
            output_dir / "ch10_classification_report.csv"
        ),
        "validation": output_dir / "ch10_classification_validation.csv",
        "checklist": output_dir / "ch10_classification_checklist.csv",
        "report": output_dir / "ch10_classification_summary.md",
    }

    csv_objects = {
        "model_data_internal": internal_model_data,
        "target_distribution": target_dist,
        "feature_audit": feature_audit,
        "merge_checks": merge_checks,
        "data_quality_checks": data_quality_checks,
        "split_summary": split_summary,
        "validation_comparison": validation_comparison,
        "threshold_metrics": threshold_df,
        "test_metrics": test_metrics,
        "predictions_internal": prediction_result_internal,
        "predictions": prediction_result_public,
        "classification_report": report_df,
        "validation": validation,
        "checklist": checklist,
    }
    for key, frame in csv_objects.items():
        frame.to_csv(paths[key], index=False, encoding="utf-8-sig")
    confusion_df.to_csv(paths["confusion_matrix"], encoding="utf-8-sig")

    report_text = build_classification_report_text(
        model_data=model_data,
        target_dist=target_dist,
        feature_audit=feature_audit,
        merge_checks=merge_checks,
        split_summary=split_summary,
        validation_comparison=validation_comparison,
        selected_model_name=selected_model_name,
        selected_threshold=selected_threshold,
        threshold_df=threshold_df,
        test_metrics=test_metrics,
        confusion_df=confusion_df,
        validation=validation,
        checklist=checklist,
    )
    paths["report"].write_text(report_text, encoding="utf-8")
    return paths


def run_classification_analysis(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    random_state: int = 42,
) -> dict[str, object]:
    """Run the complete Chapter10 pipeline with protected final test."""
    data = load_classification_source_data(processed_dir)

    (
        model_data,
        numeric_features,
        categorical_features,
        merge_checks,
        data_quality_checks,
    ) = build_classification_dataset(
        customers=data["customers"],
        orders=data["orders"],
        order_items=data["order_items"],
    )
    features = numeric_features + categorical_features
    feature_audit = build_feature_audit(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )
    target_dist = target_distribution(model_data)

    (
        X_train,
        X_valid,
        X_test,
        y_train,
        y_valid,
        y_test,
        features,
    ) = split_train_validation_test(
        model_data=model_data,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        random_state=random_state,
    )
    split_summary = build_split_summary(y_train, y_valid, y_test)

    (
        models,
        validation_comparison,
        validation_predictions,
        validation_probabilities,
    ) = train_and_compare_on_validation(
        X_train=X_train,
        X_valid=X_valid,
        y_train=y_train,
        y_valid=y_valid,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        random_state=random_state,
    )

    selected_model_name = select_validation_model(validation_comparison)
    selected_model = models[selected_model_name]
    if selected_model_name not in validation_probabilities:
        raise ValueError("선택 모델의 Validation probability가 없습니다.")

    threshold_df = threshold_metrics(
        y_valid,
        validation_probabilities[selected_model_name],
    )
    selected_threshold = choose_threshold(threshold_df)

    y_pred_test, y_proba_test, test_metrics = final_test_evaluation(
        selected_model,
        X_test,
        y_test,
        threshold=selected_threshold,
    )
    confusion_df = confusion_matrix_dataframe(y_test, y_pred_test)
    report_df = classification_report_dataframe(y_test, y_pred_test)

    prediction_result_internal = create_prediction_result(
        source_index=X_test.index,
        y_test=y_test,
        y_pred=y_pred_test,
        y_proba=y_proba_test,
        model_name=selected_model_name,
        threshold=selected_threshold,
    )
    prediction_result_public = public_prediction_result(
        prediction_result_internal
    )
    validation = build_classification_validation(
        model_data=model_data,
        features=features,
        merge_checks=merge_checks,
        y_train=y_train,
        y_valid=y_valid,
        y_test=y_test,
        validation_comparison=validation_comparison,
        selected_model_name=selected_model_name,
        threshold_df=threshold_df,
        selected_threshold=selected_threshold,
        prediction_result_public=prediction_result_public,
    )
    checklist = build_classification_checklist()

    output_paths = save_classification_outputs(
        model_data=model_data,
        target_dist=target_dist,
        feature_audit=feature_audit,
        merge_checks=merge_checks,
        data_quality_checks=data_quality_checks,
        split_summary=split_summary,
        validation_comparison=validation_comparison,
        threshold_df=threshold_df,
        test_metrics=test_metrics,
        prediction_result_internal=prediction_result_internal,
        prediction_result_public=prediction_result_public,
        confusion_df=confusion_df,
        report_df=report_df,
        validation=validation,
        checklist=checklist,
        selected_model_name=selected_model_name,
        selected_threshold=selected_threshold,
        report_dir=report_dir,
    )

    return {
        "data": data,
        "model_data": model_data,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "features": features,
        "feature_audit": feature_audit,
        "target_distribution": target_dist,
        "merge_checks": merge_checks,
        "data_quality_checks": data_quality_checks,
        "split_summary": split_summary,
        "X_train": X_train,
        "X_validation": X_valid,
        "X_test": X_test,
        "y_train": y_train,
        "y_validation": y_valid,
        "y_test": y_test,
        "models": models,
        "validation_model_comparison": validation_comparison,
        "validation_predictions": validation_predictions,
        "validation_probabilities": validation_probabilities,
        "selected_model_name": selected_model_name,
        "selected_threshold": selected_threshold,
        "threshold_metrics": threshold_df,
        "test_metrics": test_metrics,
        "prediction_result": prediction_result_public,
        "prediction_result_internal": prediction_result_internal,
        "confusion_matrix": confusion_df,
        "classification_report": report_df,
        "validation": validation,
        "checklist": checklist,
        "output_paths": output_paths,
    }
