"""Chapter 10 분류 분석 공통 함수 모음.

온라인 쇼핑몰 데이터를 사용해 주문 취소 여부(is_cancelled)를 예측하는 분류 모델링 흐름을 제공합니다.
노트북과 실행 스크립트에서 함께 사용할 수 있도록 데이터 준비, 모델 학습, 평가, 결과 저장, 보고서 생성을 함수로 분리했습니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
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
LEAKAGE_COLUMNS = ["order_status", "is_cancelled"]

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
    """scikit-learn 버전에 맞는 OneHotEncoder를 생성합니다."""
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


def build_classification_dataset(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """주문 취소 여부 예측을 위한 모델링 데이터셋을 생성합니다."""
    customers_data = customers.copy()
    orders_data = orders.copy()
    items_data = order_items.copy()

    orders_data["order_date"] = pd.to_datetime(orders_data["order_date"], errors="coerce")
    if "signup_date" in customers_data.columns:
        customers_data["signup_date"] = pd.to_datetime(
            customers_data["signup_date"], errors="coerce"
        )

    orders_data[TARGET_COLUMN] = (orders_data["order_status"] == "cancelled").astype(int)

    order_item_features = build_order_item_features(items_data)
    model_data = orders_data.merge(order_item_features, on="order_id", how="left")
    model_data = model_data.merge(customers_data, on="customer_id", how="left")

    for col in ["item_count", "total_quantity", "order_amount"]:
        if col in model_data.columns:
            model_data[col] = model_data[col].fillna(0)

    model_data["order_month"] = model_data["order_date"].dt.month
    model_data["order_dayofweek"] = model_data["order_date"].dt.dayofweek

    if "signup_date" in model_data.columns:
        model_data["days_since_signup"] = (
            model_data["order_date"] - model_data["signup_date"]
        ).dt.days
        model_data["days_since_signup"] = model_data["days_since_signup"].fillna(
            model_data["days_since_signup"].median()
        )

    numeric_features = [
        col for col in CANDIDATE_NUMERIC_FEATURES if col in model_data.columns
    ]
    categorical_features = [
        col for col in CANDIDATE_CATEGORICAL_FEATURES if col in model_data.columns
    ]

    features = numeric_features + categorical_features
    leakage_found = [col for col in LEAKAGE_COLUMNS if col in features]
    if leakage_found:
        raise ValueError(f"데이터 누수 위험 컬럼이 입력값에 포함되었습니다: {leakage_found}")

    model_data = model_data.dropna(subset=[TARGET_COLUMN]).copy()
    return model_data, numeric_features, categorical_features


def target_distribution(model_data: pd.DataFrame) -> pd.DataFrame:
    """타깃 클래스 분포를 개수와 비율로 반환합니다."""
    counts = model_data[TARGET_COLUMN].value_counts(dropna=False).sort_index()
    ratios = model_data[TARGET_COLUMN].value_counts(normalize=True, dropna=False).sort_index()
    return pd.DataFrame(
        {
            "is_cancelled": counts.index,
            "count": counts.values,
            "ratio": ratios.round(4).values,
        }
    )


def split_features_target(
    model_data: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, list[str]]:
    """입력값과 타깃을 분리하고 학습/테스트 데이터로 나눕니다."""
    features = numeric_features + categorical_features
    leakage_found = [col for col in LEAKAGE_COLUMNS if col in features]
    if leakage_found:
        raise ValueError(f"데이터 누수 위험 컬럼이 입력값에 포함되었습니다: {leakage_found}")

    X = model_data[features].copy()
    y = model_data[TARGET_COLUMN].copy()

    stratify = y if y.nunique() > 1 and y.value_counts().min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    return X_train, X_test, y_train, y_test, features


def make_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    """숫자형/범주형 컬럼 전처리 파이프라인을 만듭니다."""
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", make_one_hot_encoder()),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )


def make_classification_models(
    numeric_features: list[str],
    categorical_features: list[str],
    random_state: int = 42,
) -> dict[str, Pipeline]:
    """Logistic Regression과 Random Forest 분류 모델을 생성합니다."""
    return {
        "Logistic Regression": Pipeline(
            steps=[
                ("preprocessor", make_preprocessor(numeric_features, categorical_features)),
                (
                    "model",
                    LogisticRegression(max_iter=1000, class_weight="balanced"),
                ),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                ("preprocessor", make_preprocessor(numeric_features, categorical_features)),
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
    """분류 예측 결과를 accuracy, precision, recall, f1로 평가합니다."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def train_and_evaluate_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    numeric_features: list[str],
    categorical_features: list[str],
    random_state: int = 42,
) -> tuple[dict[str, Pipeline], pd.DataFrame, dict[str, np.ndarray], dict[str, np.ndarray]]:
    """분류 모델을 학습하고 평가 결과표와 예측값/확률을 반환합니다."""
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
        y_pred = model.predict(X_test)
        metrics = evaluate_classification_predictions(y_test, y_pred)
        rows.append({"model": model_name, **metrics})
        predictions[model_name] = y_pred

        if hasattr(model, "predict_proba"):
            probabilities[model_name] = model.predict_proba(X_test)[:, 1]

    comparison = pd.DataFrame(rows).sort_values("f1", ascending=False)
    return models, comparison, predictions, probabilities


def confusion_matrix_dataframe(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> pd.DataFrame:
    """혼동행렬을 읽기 쉬운 DataFrame으로 반환합니다."""
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return pd.DataFrame(
        matrix,
        index=["actual_not_cancelled", "actual_cancelled"],
        columns=["pred_not_cancelled", "pred_cancelled"],
    )


def classification_report_dataframe(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> pd.DataFrame:
    """classification_report를 DataFrame으로 반환합니다."""
    report = classification_report(y_true, y_pred, zero_division=0, output_dict=True)
    return pd.DataFrame(report).T.reset_index().rename(columns={"index": "label"})


def threshold_metrics(
    y_true: pd.Series,
    y_proba: np.ndarray,
    thresholds: list[float] | None = None,
) -> pd.DataFrame:
    """여러 임계값에서 분류 지표가 어떻게 달라지는지 계산합니다."""
    thresholds = thresholds or [0.2, 0.3, 0.4, 0.5, 0.6]
    rows = []

    for threshold in thresholds:
        y_pred = (y_proba >= threshold).astype(int)
        rows.append({"threshold": threshold, **evaluate_classification_predictions(y_true, y_pred)})

    return pd.DataFrame(rows)


def create_prediction_result(
    X_test: pd.DataFrame,
    y_test: pd.Series,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None,
    model_name: str,
) -> pd.DataFrame:
    """실제값, 예측값, 예측 확률을 비교하는 결과표를 생성합니다."""
    result = X_test.copy()
    result["actual_is_cancelled"] = y_test.values
    result["predicted_is_cancelled"] = y_pred
    if y_proba is not None:
        result["cancel_probability"] = y_proba
    result["model"] = model_name
    return result


def build_classification_checklist() -> pd.DataFrame:
    """LLM 코드 검토와 분류 모델링 점검에 사용할 체크리스트를 반환합니다."""
    return pd.DataFrame(
        {
            "check_item": [
                "is_cancelled가 올바르게 만들어졌는가?",
                "order_status를 입력값으로 사용하지 않았는가?",
                "train_test_split에 stratify=y를 사용했는가?",
                "학습/테스트 데이터의 클래스 비율을 확인했는가?",
                "범주형 컬럼을 OneHotEncoder 등으로 처리했는가?",
                "결측치 처리가 학습 파이프라인 안에서 이루어졌는가?",
                "accuracy 외 precision, recall, f1-score를 함께 확인했는가?",
                "모델 결과를 취소 원인으로 단정하지 않았는가?",
            ],
            "status": ["□"] * 8,
        }
    )


def build_classification_report_text(
    model_data: pd.DataFrame,
    target_dist: pd.DataFrame,
    model_comparison: pd.DataFrame,
    confusion_df: pd.DataFrame,
    threshold_df: pd.DataFrame,
    checklist: pd.DataFrame,
) -> str:
    """분류 분석 결과 보고서 Markdown 문자열을 생성합니다."""
    return f"""# Chapter 10 분류 분석 요약 보고서

## 1. 분석 목적

온라인 쇼핑몰 주문 데이터를 사용해 주문 취소 여부(is_cancelled)를 예측하는 이진 분류 모델을 만들었습니다.

## 2. 모델링 데이터 개요

- 행 수: {model_data.shape[0]}
- 열 수: {model_data.shape[1]}
- 예측 대상: is_cancelled

## 3. 타깃 클래스 분포

```text
{target_dist.to_string(index=False)}
```

## 4. 모델 비교 결과

```text
{model_comparison.to_string(index=False)}
```

## 5. 혼동행렬

```text
{confusion_df.to_string()}
```

## 6. 임계값별 성능 비교

```text
{threshold_df.to_string(index=False)}
```

## 7. LLM 코드 검토 체크리스트

```text
{checklist.to_string(index=False)}
```

## 8. 해석 시 주의사항

- 취소 주문 비율이 낮으면 accuracy만으로 모델을 평가하면 위험합니다.
- 취소 주문을 놓치지 않는 것이 중요하면 recall을 함께 확인해야 합니다.
- 취소 위험 알림의 정확도를 높이고 싶다면 precision을 함께 확인해야 합니다.
- 임계값을 낮추면 recall이 올라갈 수 있지만 precision은 낮아질 수 있습니다.
- 모델은 취소 여부와 입력값 사이의 패턴을 학습한 것이며, 취소 원인을 증명하지는 않습니다.
- order_status를 입력값으로 사용하면 정답을 미리 알려 주는 데이터 누수가 발생합니다.

## 9. 다음 단계

- 임계값을 바꿔 precision과 recall의 균형을 비교합니다.
- 취소 주문 오분류 사례를 살펴봅니다.
- 입력값에서 order_amount를 제외했을 때 성능이 어떻게 달라지는지 확인합니다.
- LLM이 작성한 분류 코드는 데이터 누수와 평가 지표 중심으로 검토합니다.
"""


def save_classification_outputs(
    model_data: pd.DataFrame,
    target_dist: pd.DataFrame,
    model_comparison: pd.DataFrame,
    prediction_result: pd.DataFrame,
    confusion_df: pd.DataFrame,
    report_df: pd.DataFrame,
    threshold_df: pd.DataFrame,
    checklist: pd.DataFrame,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """분류 분석 결과표와 보고서를 저장합니다."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "model_data": output_dir / "ch10_classification_model_data.csv",
        "target_distribution": output_dir / "ch10_target_distribution.csv",
        "model_comparison": output_dir / "ch10_classification_model_comparison.csv",
        "predictions": output_dir / "ch10_classification_predictions.csv",
        "confusion_matrix": output_dir / "ch10_confusion_matrix.csv",
        "classification_report": output_dir / "ch10_classification_report.csv",
        "threshold_metrics": output_dir / "ch10_threshold_metrics.csv",
        "checklist": output_dir / "ch10_classification_checklist.csv",
        "report": output_dir / "ch10_classification_summary.md",
    }

    model_data.to_csv(paths["model_data"], index=False, encoding="utf-8-sig")
    target_dist.to_csv(paths["target_distribution"], index=False, encoding="utf-8-sig")
    model_comparison.to_csv(paths["model_comparison"], index=False, encoding="utf-8-sig")
    prediction_result.to_csv(paths["predictions"], index=False, encoding="utf-8-sig")
    confusion_df.to_csv(paths["confusion_matrix"], encoding="utf-8-sig")
    report_df.to_csv(paths["classification_report"], index=False, encoding="utf-8-sig")
    threshold_df.to_csv(paths["threshold_metrics"], index=False, encoding="utf-8-sig")
    checklist.to_csv(paths["checklist"], index=False, encoding="utf-8-sig")

    report_text = build_classification_report_text(
        model_data=model_data,
        target_dist=target_dist,
        model_comparison=model_comparison,
        confusion_df=confusion_df,
        threshold_df=threshold_df,
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
    model_data, numeric_features, categorical_features = build_classification_dataset(
        customers=data["customers"],
        orders=data["orders"],
        order_items=data["order_items"],
    )
    target_dist = target_distribution(model_data)

    X_train, X_test, y_train, y_test, features = split_features_target(
        model_data=model_data,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        random_state=random_state,
    )
    models, model_comparison, predictions, probabilities = train_and_evaluate_models(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        random_state=random_state,
    )

    best_model_name = model_comparison.iloc[0]["model"]
    y_pred_best = predictions[best_model_name]
    y_proba_best = probabilities.get(best_model_name)

    prediction_result = create_prediction_result(
        X_test=X_test,
        y_test=y_test,
        y_pred=y_pred_best,
        y_proba=y_proba_best,
        model_name=best_model_name,
    )
    confusion_df = confusion_matrix_dataframe(y_test, y_pred_best)
    report_df = classification_report_dataframe(y_test, y_pred_best)
    threshold_df = threshold_metrics(y_test, y_proba_best) if y_proba_best is not None else pd.DataFrame()
    checklist = build_classification_checklist()

    output_paths = save_classification_outputs(
        model_data=model_data,
        target_dist=target_dist,
        model_comparison=model_comparison,
        prediction_result=prediction_result,
        confusion_df=confusion_df,
        report_df=report_df,
        threshold_df=threshold_df,
        checklist=checklist,
        report_dir=report_dir,
    )

    return {
        "data": data,
        "model_data": model_data,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "features": features,
        "target_distribution": target_dist,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "models": models,
        "model_comparison": model_comparison,
        "predictions": predictions,
        "probabilities": probabilities,
        "best_model_name": best_model_name,
        "prediction_result": prediction_result,
        "confusion_matrix": confusion_df,
        "classification_report": report_df,
        "threshold_metrics": threshold_df,
        "checklist": checklist,
        "output_paths": output_paths,
    }
