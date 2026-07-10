"""Chapter 10 분류 분석 공통 함수 모음.

온라인 쇼핑몰 데이터를 사용해 완료 주문과 취소 주문을 구분하고,
주문 취소 여부(is_cancelled)를 예측하는 분류 모델링 흐름을 제공합니다.

모델 선택과 임계값 조정에는 검증 데이터를 사용하고, 테스트 데이터는
최종 성능 확인에 한 번만 사용합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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

from src.eda import load_processed_sales_data


TARGET_COLUMN = "is_cancelled"
ALLOWED_TARGET_STATUSES = {"completed", "cancelled"}
LEAKAGE_COLUMNS = {
    "order_status",
    TARGET_COLUMN,
}
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


def make_one_hot_encoder() -> OneHotEncoder:
    """설치된 scikit-learn 버전에 맞는 OneHotEncoder를 생성합니다."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_classification_source_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """5장에서 만든 전처리 데이터를 불러옵니다."""
    return load_processed_sales_data(processed_dir)


def build_order_item_features(order_items: pd.DataFrame) -> pd.DataFrame:
    """주문 상세 데이터를 주문 단위 특징으로 요약합니다."""
    required = {"order_id", "product_id", "quantity", "unit_price"}
    missing = sorted(required - set(order_items.columns))
    if missing:
        raise KeyError(f"order_items에 필요한 컬럼이 없습니다: {missing}")

    items = order_items.copy()
    if "line_total" not in items.columns:
        items["line_total"] = items["quantity"] * items["unit_price"]

    return (
        items.groupby("order_id", as_index=False)
        .agg(
            item_count=("product_id", "count"),
            total_quantity=("quantity", "sum"),
            order_amount=("line_total", "sum"),
        )
    )


def _checked_left_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    on: str,
    validate: str,
    right_label: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """left merge를 실행하고 행 수와 미매칭 건수를 함께 반환합니다."""
    before_rows = len(left)
    merged = left.merge(
        right,
        on=on,
        how="left",
        validate=validate,
        indicator=True,
    )
    after_rows = len(merged)
    unmatched_count = int((merged["_merge"] == "left_only").sum())

    check = {
        "merge": f"{on} → {right_label}",
        "before_rows": before_rows,
        "after_rows": after_rows,
        "row_count_preserved": before_rows == after_rows,
        "unmatched_count": unmatched_count,
    }
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
    """완료/취소 주문만 사용해 분류 데이터셋과 검증표를 생성합니다."""
    required_columns = {
        "customers": {"customer_id"},
        "orders": {
            "order_id",
            "customer_id",
            "order_date",
            "order_status",
        },
        "order_items": {
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
        },
    }
    frames = {
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
    }
    for name, required in required_columns.items():
        missing = sorted(required - set(frames[name].columns))
        if missing:
            raise KeyError(f"{name}에 필요한 컬럼이 없습니다: {missing}")

    customers_data = customers.copy()
    orders_data = orders.copy()

    orders_data["order_date"] = pd.to_datetime(
        orders_data["order_date"],
        errors="coerce",
    )
    orders_data = orders_data.dropna(
        subset=["order_id", "customer_id", "order_date", "order_status"]
    ).copy()

    status_scope = (
        orders_data["order_status"]
        .value_counts(dropna=False)
        .rename_axis("order_status")
        .reset_index(name="order_count")
    )
    status_scope["used_for_binary_target"] = status_scope[
        "order_status"
    ].isin(ALLOWED_TARGET_STATUSES)

    orders_data = orders_data[
        orders_data["order_status"].isin(ALLOWED_TARGET_STATUSES)
    ].copy()
    if orders_data.empty:
        raise ValueError(
            "completed 또는 cancelled 주문이 없어 분류 데이터를 만들 수 없습니다."
        )

    orders_data[TARGET_COLUMN] = (
        orders_data["order_status"] == "cancelled"
    ).astype(int)

    target_counts = orders_data[TARGET_COLUMN].value_counts()
    if len(target_counts) < 2:
        raise ValueError(
            "분류 학습에는 completed와 cancelled 주문이 모두 필요합니다."
        )
    if target_counts.min() < 5:
        raise ValueError(
            "각 클래스에 최소 5개 이상의 주문이 필요합니다. "
            f"현재 클래스별 건수: {target_counts.to_dict()}"
        )

    order_item_features = build_order_item_features(order_items)
    model_data, order_merge_check = _checked_left_merge(
        orders_data,
        order_item_features,
        on="order_id",
        validate="one_to_one",
        right_label="order_item_features",
    )

    customer_columns = [
        column
        for column in [
            "customer_id",
            "gender",
            "age",
            "city",
            "signup_date",
        ]
        if column in customers_data.columns
    ]
    customer_lookup = customers_data[customer_columns].copy()
    if "signup_date" in customer_lookup.columns:
        customer_lookup["signup_date"] = pd.to_datetime(
            customer_lookup["signup_date"],
            errors="coerce",
        )

    model_data, customer_merge_check = _checked_left_merge(
        model_data,
        customer_lookup,
        on="customer_id",
        validate="many_to_one",
        right_label="customers",
    )

    for column in ["item_count", "total_quantity", "order_amount"]:
        if column in model_data.columns:
            model_data[column] = model_data[column].fillna(0)

    model_data["order_month"] = model_data["order_date"].dt.month
    model_data["order_dayofweek"] = model_data[
        "order_date"
    ].dt.dayofweek

    temporal_invalid_count = 0
    if "signup_date" in model_data.columns:
        model_data["days_since_signup"] = (
            model_data["order_date"] - model_data["signup_date"]
        ).dt.days
        invalid_temporal = model_data["days_since_signup"] < 0
        temporal_invalid_count = int(invalid_temporal.sum())
        model_data.loc[invalid_temporal, "days_since_signup"] = np.nan

    numeric_features = [
        column
        for column in CANDIDATE_NUMERIC_FEATURES
        if (
            column in model_data.columns
            and model_data[column].notna().any()
        )
    ]
    categorical_features = [
        column
        for column in CANDIDATE_CATEGORICAL_FEATURES
        if (
            column in model_data.columns
            and model_data[column].notna().any()
        )
    ]
    features = numeric_features + categorical_features

    leakage_found = sorted(LEAKAGE_COLUMNS.intersection(features))
    if leakage_found:
        raise ValueError(
            "데이터 누수 위험 컬럼이 입력값에 포함되었습니다: "
            f"{leakage_found}"
        )
    if not features:
        raise ValueError("사용 가능한 입력 feature가 없습니다.")

    merge_checks = pd.DataFrame(
        [order_merge_check, customer_merge_check]
    )
    data_quality_checks = pd.DataFrame(
        {
            "check_item": [
                "binary_target_rows",
                "completed_rows",
                "cancelled_rows",
                "excluded_status_rows",
                "negative_days_since_signup",
                "missing_order_item_features",
                "missing_customer_match",
            ],
            "count": [
                len(model_data),
                int((model_data[TARGET_COLUMN] == 0).sum()),
                int((model_data[TARGET_COLUMN] == 1).sum()),
                int(
                    (
                        ~status_scope["used_for_binary_target"]
                    ).mul(status_scope["order_count"]).sum()
                ),
                temporal_invalid_count,
                order_merge_check["unmatched_count"],
                customer_merge_check["unmatched_count"],
            ],
        }
    )

    status_checks = status_scope.assign(
        check_item=lambda frame: (
            "status_scope:" + frame["order_status"].astype(str)
        ),
        count=lambda frame: frame["order_count"],
    )[["check_item", "count"]]

    return (
        model_data,
        numeric_features,
        categorical_features,
        merge_checks,
        pd.concat(
            [data_quality_checks, status_checks],
            ignore_index=True,
        ),
    )


def target_distribution(model_data: pd.DataFrame) -> pd.DataFrame:
    """타깃 클래스 분포를 개수와 비율로 반환합니다."""
    counts = (
        model_data[TARGET_COLUMN]
        .value_counts(dropna=False)
        .sort_index()
    )
    ratios = (
        model_data[TARGET_COLUMN]
        .value_counts(normalize=True, dropna=False)
        .sort_index()
    )
    labels = {
        0: "completed",
        1: "cancelled",
    }
    return pd.DataFrame(
        {
            TARGET_COLUMN: counts.index,
            "class_label": [
                labels.get(value, str(value))
                for value in counts.index
            ],
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
    """입력값과 타깃을 train/validation/test로 나눕니다."""
    if test_size <= 0 or validation_size <= 0:
        raise ValueError(
            "test_size와 validation_size는 0보다 커야 합니다."
        )
    if test_size + validation_size >= 1:
        raise ValueError(
            "test_size와 validation_size의 합은 1보다 작아야 합니다."
        )

    features = numeric_features + categorical_features
    leakage_found = sorted(LEAKAGE_COLUMNS.intersection(features))
    if leakage_found:
        raise ValueError(
            "데이터 누수 위험 컬럼이 입력값에 포함되었습니다: "
            f"{leakage_found}"
        )

    X = model_data[features].copy()
    y = model_data[TARGET_COLUMN].copy()

    if y.nunique() != 2:
        raise ValueError(
            "이진 분류에는 두 개의 타깃 클래스가 필요합니다."
        )

    X_train_valid, X_test, y_train_valid, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    validation_ratio_within_train_valid = (
        validation_size / (1 - test_size)
    )
    X_train, X_valid, y_train, y_valid = train_test_split(
        X_train_valid,
        y_train_valid,
        test_size=validation_ratio_within_train_valid,
        random_state=random_state,
        stratify=y_train_valid,
    )

    for split_name, target in {
        "train": y_train,
        "validation": y_valid,
        "test": y_test,
    }.items():
        if target.nunique() != 2:
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
    """데이터 분할별 클래스 건수와 비율을 요약합니다."""
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
                        "cancelled"
                        if class_value == 1
                        else "completed"
                    ),
                    "count": count,
                    "ratio": (
                        round(count / total, 4)
                        if total
                        else 0
                    ),
                }
            )
    return pd.DataFrame(rows)


def make_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    """숫자형/범주형 컬럼 전처리 파이프라인을 만듭니다."""
    transformers: list[tuple[str, Pipeline, list[str]]] = []

    if numeric_features:
        numeric_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(
            ("num", numeric_transformer, numeric_features)
        )

    if categorical_features:
        categorical_transformer = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="most_frequent"),
                ),
                ("onehot", make_one_hot_encoder()),
            ]
        )
        transformers.append(
            ("cat", categorical_transformer, categorical_features)
        )

    if not transformers:
        raise ValueError("전처리할 feature가 없습니다.")

    return ColumnTransformer(transformers=transformers)


def make_classification_models(
    numeric_features: list[str],
    categorical_features: list[str],
    random_state: int = 42,
) -> dict[str, Pipeline]:
    """기준 모델과 비교 모델을 생성합니다."""
    return {
        "Dummy Most Frequent": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(
                        numeric_features,
                        categorical_features,
                    ),
                ),
                (
                    "model",
                    DummyClassifier(strategy="most_frequent"),
                ),
            ]
        ),
        "Logistic Regression": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(
                        numeric_features,
                        categorical_features,
                    ),
                ),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                    ),
                ),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(
                        numeric_features,
                        categorical_features,
                    ),
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
    """분류 예측을 accuracy, precision, recall, f1로 평가합니다."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
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
    """train으로 학습하고 validation 성능을 비교합니다."""
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
        metrics = evaluate_classification_predictions(
            y_valid,
            y_pred,
        )
        rows.append(
            {
                "model": model_name,
                "evaluation_split": "validation",
                **metrics,
            }
        )
        predictions[model_name] = y_pred

        if hasattr(model, "predict_proba"):
            probabilities[model_name] = model.predict_proba(
                X_valid
            )[:, 1]

    comparison = (
        pd.DataFrame(rows)
        .sort_values(
            ["f1", "recall", "precision"],
            ascending=False,
        )
        .reset_index(drop=True)
    )
    return models, comparison, predictions, probabilities


def threshold_metrics(
    y_true: pd.Series,
    y_proba: np.ndarray,
    thresholds: list[float] | None = None,
) -> pd.DataFrame:
    """검증 데이터에서 여러 임계값의 분류 지표를 계산합니다."""
    thresholds = thresholds or [
        round(value, 2)
        for value in np.arange(0.2, 0.81, 0.05)
    ]
    rows = []
    for threshold in thresholds:
        y_pred = (y_proba >= threshold).astype(int)
        rows.append(
            {
                "threshold": threshold,
                **evaluate_classification_predictions(
                    y_true,
                    y_pred,
                ),
            }
        )
    return pd.DataFrame(rows)


def choose_threshold(
    threshold_df: pd.DataFrame,
    *,
    default_threshold: float = 0.5,
) -> float:
    """검증 데이터에서 F1, recall, precision 순으로 임계값을 선택합니다."""
    if threshold_df.empty:
        return default_threshold

    ranked = threshold_df.sort_values(
        ["f1", "recall", "precision", "threshold"],
        ascending=[False, False, False, True],
    )
    return float(ranked.iloc[0]["threshold"])


def final_test_evaluation(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    *,
    threshold: float,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """선택한 모델과 임계값을 테스트 데이터에서 한 번 평가합니다."""
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    metrics = pd.DataFrame(
        [
            {
                "evaluation_split": "test",
                "threshold": threshold,
                **evaluate_classification_predictions(
                    y_test,
                    y_pred,
                ),
            }
        ]
    )
    return y_pred, y_proba, metrics


def confusion_matrix_dataframe(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> pd.DataFrame:
    """혼동행렬을 읽기 쉬운 DataFrame으로 반환합니다."""
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
    """classification_report를 DataFrame으로 반환합니다."""
    report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1],
        target_names=["completed", "cancelled"],
        zero_division=0,
        output_dict=True,
    )
    return (
        pd.DataFrame(report)
        .T.reset_index()
        .rename(columns={"index": "label"})
    )


def create_prediction_result(
    source_index: pd.Index,
    y_test: pd.Series,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
    *,
    model_name: str,
    threshold: float,
) -> pd.DataFrame:
    """개인정보를 제외한 테스트 예측 결과표를 생성합니다."""
    return pd.DataFrame(
        {
            "record_id": [
                f"test_{position:04d}"
                for position in range(1, len(y_test) + 1)
            ],
            "source_index": source_index.to_numpy(),
            "actual_is_cancelled": y_test.to_numpy(),
            "predicted_is_cancelled": y_pred,
            "cancel_probability": y_proba,
            "model": model_name,
            "threshold": threshold,
        }
    )


def build_classification_checklist() -> pd.DataFrame:
    """분류 모델링과 LLM 생성 코드 검토 체크리스트를 반환합니다."""
    items = [
        "completed와 cancelled만 사용해 이진 타깃을 만들었는가?",
        "refunded 등 다른 상태를 0 클래스에 섞지 않았는가?",
        "order_status와 타깃 파생 컬럼을 feature에서 제외했는가?",
        "병합에 validate를 사용하고 미매칭 건수를 확인했는가?",
        "train, validation, test를 분리했는가?",
        "모델과 임계값은 validation에서 선택했는가?",
        "test는 최종 평가에 한 번만 사용했는가?",
        "Dummy 기준 모델과 비교했는가?",
        "accuracy 외 precision, recall, f1을 함께 확인했는가?",
        "모델 결과를 취소 원인으로 단정하지 않았는가?",
        "예측 결과에 고객명 등 개인정보가 포함되지 않았는가?",
    ]
    return pd.DataFrame(
        {
            "check_item": items,
            "status": ["□"] * len(items),
        }
    )


def build_classification_report_text(
    model_data: pd.DataFrame,
    target_dist: pd.DataFrame,
    split_summary: pd.DataFrame,
    validation_comparison: pd.DataFrame,
    selected_model_name: str,
    selected_threshold: float,
    threshold_df: pd.DataFrame,
    test_metrics: pd.DataFrame,
    confusion_df: pd.DataFrame,
    checklist: pd.DataFrame,
) -> str:
    """분류 분석 결과 보고서 Markdown 문자열을 생성합니다."""
    return f"""# Chapter 10 분류 분석 요약 보고서

## 1. 분석 목적

온라인 쇼핑몰의 완료 주문과 취소 주문을 사용해 주문 취소 여부를 예측하는 이진 분류 모델을 만들었습니다.

## 2. 모델링 데이터 개요

- 행 수: {model_data.shape[0]}
- 열 수: {model_data.shape[1]}
- 0 클래스: completed
- 1 클래스: cancelled
- refunded 등 다른 주문 상태는 이진 분류 대상에서 제외

## 3. 타깃 클래스 분포

```text
{target_dist.to_string(index=False)}
```

## 4. 데이터 분할

```text
{split_summary.to_string(index=False)}
```

## 5. 검증 데이터 모델 비교

```text
{validation_comparison.to_string(index=False)}
```

- 선택 모델: {selected_model_name}

## 6. 검증 데이터 임계값 비교

```text
{threshold_df.to_string(index=False)}
```

- 선택 임계값: {selected_threshold:.2f}

## 7. 최종 테스트 성능

```text
{test_metrics.to_string(index=False)}
```

## 8. 테스트 혼동행렬

```text
{confusion_df.to_string()}
```

## 9. LLM 코드 검토 체크리스트

```text
{checklist.to_string(index=False)}
```

## 10. 해석 시 주의사항

- 모델과 임계값은 validation 데이터에서 선택했습니다.
- test 데이터는 최종 성능 확인에 한 번만 사용했습니다.
- 정확도만 보지 않고 precision, recall, f1을 함께 확인했습니다.
- 현재 결과는 샘플 데이터와 선택한 feature 범위에 한정됩니다.
- 모델이 학습한 것은 상관 패턴이며 주문 취소의 원인을 증명하지 않습니다.
- 실제 서비스 적용 전에는 시간 순서 분할, 비용 기준, 재학습 주기, 공정성 검토가 필요합니다.
"""


def save_classification_outputs(
    *,
    model_data: pd.DataFrame,
    target_dist: pd.DataFrame,
    merge_checks: pd.DataFrame,
    data_quality_checks: pd.DataFrame,
    split_summary: pd.DataFrame,
    validation_comparison: pd.DataFrame,
    threshold_df: pd.DataFrame,
    test_metrics: pd.DataFrame,
    prediction_result: pd.DataFrame,
    confusion_df: pd.DataFrame,
    report_df: pd.DataFrame,
    checklist: pd.DataFrame,
    selected_model_name: str,
    selected_threshold: float,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """분류 분석 결과표와 보고서를 저장합니다."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_model_columns = [
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
    safe_model_data = model_data[safe_model_columns].copy()

    paths = {
        "model_data": (
            output_dir / "ch10_classification_model_data.csv"
        ),
        "target_distribution": (
            output_dir / "ch10_target_distribution.csv"
        ),
        "merge_checks": output_dir / "ch10_merge_checks.csv",
        "data_quality_checks": (
            output_dir / "ch10_data_quality_checks.csv"
        ),
        "split_summary": output_dir / "ch10_split_summary.csv",
        "validation_comparison": (
            output_dir / "ch10_validation_model_comparison.csv"
        ),
        "threshold_metrics": (
            output_dir / "ch10_validation_threshold_metrics.csv"
        ),
        "test_metrics": output_dir / "ch10_test_metrics.csv",
        "predictions": (
            output_dir / "ch10_classification_predictions.csv"
        ),
        "confusion_matrix": (
            output_dir / "ch10_confusion_matrix.csv"
        ),
        "classification_report": (
            output_dir / "ch10_classification_report.csv"
        ),
        "checklist": (
            output_dir / "ch10_classification_checklist.csv"
        ),
        "report": output_dir / "ch10_classification_summary.md",
    }

    safe_model_data.to_csv(
        paths["model_data"],
        index=False,
        encoding="utf-8-sig",
    )
    target_dist.to_csv(
        paths["target_distribution"],
        index=False,
        encoding="utf-8-sig",
    )
    merge_checks.to_csv(
        paths["merge_checks"],
        index=False,
        encoding="utf-8-sig",
    )
    data_quality_checks.to_csv(
        paths["data_quality_checks"],
        index=False,
        encoding="utf-8-sig",
    )
    split_summary.to_csv(
        paths["split_summary"],
        index=False,
        encoding="utf-8-sig",
    )
    validation_comparison.to_csv(
        paths["validation_comparison"],
        index=False,
        encoding="utf-8-sig",
    )
    threshold_df.to_csv(
        paths["threshold_metrics"],
        index=False,
        encoding="utf-8-sig",
    )
    test_metrics.to_csv(
        paths["test_metrics"],
        index=False,
        encoding="utf-8-sig",
    )
    prediction_result.to_csv(
        paths["predictions"],
        index=False,
        encoding="utf-8-sig",
    )
    confusion_df.to_csv(
        paths["confusion_matrix"],
        encoding="utf-8-sig",
    )
    report_df.to_csv(
        paths["classification_report"],
        index=False,
        encoding="utf-8-sig",
    )
    checklist.to_csv(
        paths["checklist"],
        index=False,
        encoding="utf-8-sig",
    )

    report_text = build_classification_report_text(
        model_data=model_data,
        target_dist=target_dist,
        split_summary=split_summary,
        validation_comparison=validation_comparison,
        selected_model_name=selected_model_name,
        selected_threshold=selected_threshold,
        threshold_df=threshold_df,
        test_metrics=test_metrics,
        confusion_df=confusion_df,
        checklist=checklist,
    )
    paths["report"].write_text(report_text, encoding="utf-8")
    return paths


def run_classification_analysis(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    random_state: int = 42,
) -> dict[str, object]:
    """10장 분류 분석 전체 파이프라인을 실행합니다."""
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
    split_summary = build_split_summary(
        y_train,
        y_valid,
        y_test,
    )

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

    non_dummy_comparison = validation_comparison[
        validation_comparison["model"] != "Dummy Most Frequent"
    ]
    if non_dummy_comparison.empty:
        raise ValueError("비교 가능한 학습 모델이 없습니다.")

    selected_model_name = str(
        non_dummy_comparison.iloc[0]["model"]
    )
    selected_model = models[selected_model_name]
    validation_proba = validation_probabilities[
        selected_model_name
    ]
    threshold_df = threshold_metrics(
        y_valid,
        validation_proba,
    )
    selected_threshold = choose_threshold(threshold_df)

    y_pred_test, y_proba_test, test_metrics = final_test_evaluation(
        selected_model,
        X_test,
        y_test,
        threshold=selected_threshold,
    )
    confusion_df = confusion_matrix_dataframe(
        y_test,
        y_pred_test,
    )
    report_df = classification_report_dataframe(
        y_test,
        y_pred_test,
    )
    prediction_result = create_prediction_result(
        source_index=X_test.index,
        y_test=y_test,
        y_pred=y_pred_test,
        y_proba=y_proba_test,
        model_name=selected_model_name,
        threshold=selected_threshold,
    )
    checklist = build_classification_checklist()

    output_paths = save_classification_outputs(
        model_data=model_data,
        target_dist=target_dist,
        merge_checks=merge_checks,
        data_quality_checks=data_quality_checks,
        split_summary=split_summary,
        validation_comparison=validation_comparison,
        threshold_df=threshold_df,
        test_metrics=test_metrics,
        prediction_result=prediction_result,
        confusion_df=confusion_df,
        report_df=report_df,
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
        "prediction_result": prediction_result,
        "confusion_matrix": confusion_df,
        "classification_report": report_df,
        "checklist": checklist,
        "output_paths": output_paths,
    }
