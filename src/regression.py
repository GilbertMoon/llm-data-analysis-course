"""Chapter 9 회귀 분석 공통 함수 모음.

온라인 쇼핑몰 데이터를 사용해 주문별 총금액(order_total)을 예측하는 회귀 모델링 흐름을 제공합니다.
노트북과 실행 스크립트에서 함께 사용할 수 있도록 데이터 준비, 모델 학습, 평가, 결과 저장, 보고서 생성을 함수로 분리했습니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.eda import load_processed_sales_data


TARGET_COLUMN = "order_total"

NUMERIC_FEATURES = [
    "item_count",
    "total_quantity",
    "avg_unit_price",
    "order_month",
    "order_dayofweek",
    "age",
]

CATEGORICAL_FEATURES = [
    "payment_method",
    "order_status",
    "gender",
    "city",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def make_one_hot_encoder() -> OneHotEncoder:
    """scikit-learn 버전에 맞는 OneHotEncoder를 생성합니다."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_regression_source_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """5장에서 만든 전처리 데이터를 불러옵니다."""
    return load_processed_sales_data(processed_dir)


def build_order_features(
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """주문 상세 데이터를 주문 단위 모델링 데이터로 요약합니다."""
    items = order_items.copy()

    if "line_total" not in items.columns:
        items["line_total"] = items["quantity"] * items["unit_price"]

    order_features = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_count=("product_id", "count"),
            total_quantity=("quantity", "sum"),
            avg_unit_price=("unit_price", "mean"),
            order_total=("line_total", "sum"),
        )
    )

    return order_features


def build_regression_dataset(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """주문별 총금액 예측을 위한 모델링 데이터셋을 생성합니다."""
    customers_data = customers.copy()
    orders_data = orders.copy()
    items_data = order_items.copy()

    order_features = build_order_features(items_data)

    orders_data["order_date"] = pd.to_datetime(orders_data["order_date"], errors="coerce")
    orders_data["order_month"] = orders_data["order_date"].dt.month
    orders_data["order_dayofweek"] = orders_data["order_date"].dt.dayofweek

    order_columns = [
        "order_id",
        "customer_id",
        "payment_method",
        "order_status",
        "order_month",
        "order_dayofweek",
    ]
    customer_columns = ["customer_id", "gender", "age", "city"]

    model_data = order_features.merge(
        orders_data[order_columns],
        on="order_id",
        how="left",
    )
    model_data = model_data.merge(
        customers_data[customer_columns],
        on="customer_id",
        how="left",
    )

    model_data["age"] = pd.to_numeric(model_data["age"], errors="coerce")
    model_data["avg_unit_price"] = pd.to_numeric(model_data["avg_unit_price"], errors="coerce")
    model_data["total_quantity"] = pd.to_numeric(model_data["total_quantity"], errors="coerce")
    model_data["item_count"] = pd.to_numeric(model_data["item_count"], errors="coerce")
    model_data["order_total"] = pd.to_numeric(model_data["order_total"], errors="coerce")

    return model_data.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy()


def split_features_target(
    model_data: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """입력값과 예측 대상을 분리하고 학습/테스트 데이터로 나눕니다."""
    if TARGET_COLUMN in FEATURE_COLUMNS:
        raise ValueError("데이터 누수 위험: order_total이 feature 목록에 포함되어 있습니다.")

    X = model_data[FEATURE_COLUMNS]
    y = model_data[TARGET_COLUMN]

    return train_test_split(X, y, test_size=test_size, random_state=random_state)


def make_preprocessor() -> ColumnTransformer:
    """범주형 컬럼은 OneHotEncoder로 변환하고 숫자형 컬럼은 그대로 통과시킵니다."""
    return ColumnTransformer(
        transformers=[
            ("cat", make_one_hot_encoder(), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )


def make_regression_models(random_state: int = 42) -> dict[str, Pipeline]:
    """선형 회귀와 랜덤 포레스트 회귀 모델 파이프라인을 생성합니다."""
    preprocessor = make_preprocessor()

    return {
        "Linear Regression": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", LinearRegression()),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                ("preprocessor", make_preprocessor()),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=200,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
    }


def evaluate_predictions(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """회귀 예측 결과를 MAE, RMSE, R2로 평가합니다."""
    mse = mean_squared_error(y_true, y_pred)
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mse)),
        "R2": float(r2_score(y_true, y_pred)),
    }


def train_and_evaluate_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    random_state: int = 42,
) -> tuple[dict[str, Pipeline], pd.DataFrame, dict[str, np.ndarray]]:
    """회귀 모델을 학습하고 평가 결과표와 예측값을 반환합니다."""
    models = make_regression_models(random_state=random_state)
    rows: list[dict[str, Any]] = []
    predictions: dict[str, np.ndarray] = {}

    for model_name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = evaluate_predictions(y_test, y_pred)
        rows.append({"model": model_name, **metrics})
        predictions[model_name] = y_pred

    comparison = pd.DataFrame(rows).sort_values("MAE")
    return models, comparison, predictions


def create_prediction_result(
    X_test: pd.DataFrame,
    y_test: pd.Series,
    y_pred: np.ndarray,
    model_name: str,
) -> pd.DataFrame:
    """실제값, 예측값, 오차를 비교하는 결과표를 생성합니다."""
    result = X_test.copy()
    result["actual_order_total"] = y_test.values
    result["predicted_order_total"] = y_pred
    result["error"] = result["actual_order_total"] - result["predicted_order_total"]
    result["abs_error"] = result["error"].abs()
    result["model"] = model_name
    return result.sort_values("abs_error", ascending=False)


def build_leakage_checklist() -> pd.DataFrame:
    """LLM 코드 검토와 회귀 모델링 점검에 사용할 체크리스트를 반환합니다."""
    return pd.DataFrame(
        {
            "check_item": [
                "예측 대상이 명확히 분리되었는가?",
                "정답 컬럼을 입력값으로 사용하지 않았는가?",
                "실제 데이터에 없는 컬럼명을 만들지 않았는가?",
                "범주형 컬럼을 적절히 인코딩했는가?",
                "train/test split을 적용했는가?",
                "테스트 데이터 기준으로 평가했는가?",
                "MAE, RMSE, R²를 함께 확인했는가?",
                "성능 결과를 과장해서 해석하지 않았는가?",
            ],
            "status": ["□"] * 8,
        }
    )


def build_regression_report(
    model_data: pd.DataFrame,
    model_comparison: pd.DataFrame,
    prediction_result: pd.DataFrame,
    checklist: pd.DataFrame,
) -> str:
    """회귀 분석 결과 보고서 Markdown 문자열을 생성합니다."""
    return f"""# Chapter 9 회귀 분석 요약 보고서

## 1. 분석 목적

온라인 쇼핑몰 주문 데이터를 사용해 주문별 총금액(order_total)을 예측하는 회귀 모델을 만들었습니다.

## 2. 모델링 데이터 개요

- 행 수: {model_data.shape[0]}
- 열 수: {model_data.shape[1]}
- 예측 대상: order_total
- 입력값: {', '.join(FEATURE_COLUMNS)}

## 3. 모델 비교 결과

```text
{model_comparison.to_string(index=False)}
```

## 4. 예측 오차 상위 10건

```text
{prediction_result.head(10).to_string(index=False)}
```

## 5. 모델링 검토 체크리스트

```text
{checklist.to_string(index=False)}
```

## 6. 해석 시 주의사항

- MAE는 예측값이 실제 주문 금액과 평균적으로 얼마나 차이 나는지 보여줍니다.
- RMSE는 큰 오차에 더 민감합니다.
- R²는 모델이 실제 값의 변동을 얼마나 설명하는지 보여주지만, 항상 1에 가까워야만 좋은 것은 아닙니다.
- 성능이 더 좋아 보이는 모델이 항상 실제 운영에 적합한 모델은 아닙니다.
- order_total 같은 정답 컬럼을 입력값으로 사용하면 데이터 누수가 발생합니다.

## 7. 다음 단계

- 입력값에서 avg_unit_price를 제외했을 때 성능이 어떻게 바뀌는지 비교합니다.
- 예측 오차가 큰 주문 10건의 공통점을 살펴봅니다.
- 고객별 총 구매 금액 예측 또는 상품별 총매출 예측 문제로 확장합니다.
- LLM이 작성한 모델링 코드는 데이터 누수와 평가 방식 중심으로 검토합니다.
"""


def save_regression_outputs(
    model_data: pd.DataFrame,
    model_comparison: pd.DataFrame,
    prediction_result: pd.DataFrame,
    checklist: pd.DataFrame,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """회귀 분석 결과표와 보고서를 저장합니다."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "model_data": output_dir / "ch09_regression_model_data.csv",
        "model_comparison": output_dir / "ch09_regression_model_comparison.csv",
        "predictions": output_dir / "ch09_regression_predictions.csv",
        "checklist": output_dir / "ch09_regression_checklist.csv",
        "report": output_dir / "ch09_regression_report.md",
    }

    model_data.to_csv(paths["model_data"], index=False, encoding="utf-8-sig")
    model_comparison.to_csv(paths["model_comparison"], index=False, encoding="utf-8-sig")
    prediction_result.to_csv(paths["predictions"], index=False, encoding="utf-8-sig")
    checklist.to_csv(paths["checklist"], index=False, encoding="utf-8-sig")

    report_text = build_regression_report(
        model_data=model_data,
        model_comparison=model_comparison,
        prediction_result=prediction_result,
        checklist=checklist,
    )
    paths["report"].write_text(report_text, encoding="utf-8")

    return paths


def run_regression_analysis(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    random_state: int = 42,
) -> dict[str, object]:
    """9장 회귀 분석 전체 파이프라인을 실행합니다."""
    data = load_regression_source_data(processed_dir)
    model_data = build_regression_dataset(
        customers=data["customers"],
        orders=data["orders"],
        order_items=data["order_items"],
    )

    X_train, X_test, y_train, y_test = split_features_target(
        model_data,
        random_state=random_state,
    )
    models, model_comparison, predictions = train_and_evaluate_models(
        X_train,
        X_test,
        y_train,
        y_test,
        random_state=random_state,
    )

    best_model_name = model_comparison.iloc[0]["model"]
    prediction_result = create_prediction_result(
        X_test=X_test,
        y_test=y_test,
        y_pred=predictions[best_model_name],
        model_name=best_model_name,
    )
    checklist = build_leakage_checklist()
    output_paths = save_regression_outputs(
        model_data=model_data,
        model_comparison=model_comparison,
        prediction_result=prediction_result,
        checklist=checklist,
        report_dir=report_dir,
    )

    return {
        "data": data,
        "model_data": model_data,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "models": models,
        "model_comparison": model_comparison,
        "predictions": predictions,
        "best_model_name": best_model_name,
        "prediction_result": prediction_result,
        "checklist": checklist,
        "output_paths": output_paths,
    }
