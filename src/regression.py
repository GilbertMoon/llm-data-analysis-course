"""Chapter 9 regression analysis utilities.

The module implements the leakage-aware workflow described in
``book/chapters/ch09_regression_analysis.md``:

- build ``order_total`` only as the target,
- use only information available at the educational prediction time,
- split train/test data in chronological order,
- fit preprocessing inside each model pipeline,
- compare against a mean baseline,
- validate stability with time-series cross-validation,
- save internal diagnostics without exposing them as public reports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET_COLUMN = "order_total"

NUMERIC_FEATURES = [
    "order_month",
    "order_dayofweek",
    "age",
]

CATEGORICAL_FEATURES = [
    "payment_method",
    "gender",
    "city",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

FORBIDDEN_FEATURES = {
    "order_total",
    "line_total",
    "quantity",
    "unit_price",
    "item_count",
    "total_quantity",
    "avg_unit_price",
    "order_status",
    "order_id",
    "customer_id",
}

REQUIRED_COLUMNS = {
    "customers": {
        "customer_id",
        "gender",
        "age",
        "city",
    },
    "orders": {
        "order_id",
        "customer_id",
        "order_date",
        "payment_method",
        "order_status",
    },
    "order_items": {
        "order_id",
        "quantity",
        "unit_price",
    },
}


def make_one_hot_encoder() -> OneHotEncoder:
    """Return a dense OneHotEncoder compatible with multiple sklearn versions."""
    try:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )
    except TypeError:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse=False,
        )


def load_regression_source_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """Load the three processed CSV files required for Chapter 9."""
    input_dir = Path(processed_dir)
    file_map = {
        "customers": input_dir / "customers_clean.csv",
        "orders": input_dir / "orders_clean.csv",
        "order_items": input_dir / "order_items_clean.csv",
    }

    missing_files = [
        path
        for path in file_map.values()
        if not path.exists()
    ]
    if missing_files:
        missing_text = ", ".join(str(path) for path in missing_files)
        raise FileNotFoundError(
            "전처리 파일이 없습니다. 먼저 "
            "`python scripts/preprocess_data.py`를 실행하세요. "
            f"누락 파일: {missing_text}"
        )

    return {
        name: pd.read_csv(path)
        for name, path in file_map.items()
    }


def validate_required_columns(
    datasets: dict[str, pd.DataFrame],
) -> None:
    """Raise a clear error when a required modeling column is missing."""
    for name, columns in REQUIRED_COLUMNS.items():
        if name not in datasets:
            raise KeyError(f"필수 데이터셋이 없습니다: {name}")

        missing_columns = columns - set(datasets[name].columns)
        if missing_columns:
            raise KeyError(
                f"{name}에 필요한 컬럼이 없습니다: "
                f"{sorted(missing_columns)}"
            )


def validate_feature_columns(
    feature_columns: Iterable[str] = FEATURE_COLUMNS,
) -> None:
    """Prevent identifiers, target values, and target proxies from being used."""
    columns = list(feature_columns)
    leaked_features = set(columns) & FORBIDDEN_FEATURES
    if leaked_features:
        raise ValueError(
            "입력값에 누수 위험 컬럼이 있습니다: "
            f"{sorted(leaked_features)}"
        )

    duplicated_features = pd.Index(columns)[
        pd.Index(columns).duplicated()
    ].tolist()
    if duplicated_features:
        raise ValueError(
            "입력값 목록에 중복 컬럼이 있습니다: "
            f"{duplicated_features}"
        )


def build_order_totals(
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """Create the order-level target without exposing detail-derived features."""
    items = order_items.copy()

    items["quantity"] = pd.to_numeric(
        items["quantity"],
        errors="coerce",
    )
    items["unit_price"] = pd.to_numeric(
        items["unit_price"],
        errors="coerce",
    )

    if "line_total" in items.columns:
        items["line_total"] = pd.to_numeric(
            items["line_total"],
            errors="coerce",
        )
    else:
        items["line_total"] = (
            items["quantity"]
            * items["unit_price"]
        )

    invalid_target_rows = items[
        ["order_id", "line_total"]
    ].isna().any(axis=1)
    if invalid_target_rows.any():
        invalid_count = int(invalid_target_rows.sum())
        raise ValueError(
            "주문 금액 목표값을 만들 수 없는 주문 상세 행이 있습니다: "
            f"{invalid_count}건"
        )

    return (
        items.groupby(
            "order_id",
            as_index=False,
        )
        .agg(
            order_total=(
                "line_total",
                "sum",
            ),
        )
    )


def build_regression_dataset(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """Build a leakage-aware order-level regression dataset."""
    datasets = {
        "customers": customers.copy(),
        "orders": orders.copy(),
        "order_items": order_items.copy(),
    }
    validate_required_columns(datasets)
    validate_feature_columns()

    customers_data = datasets["customers"]
    orders_data = datasets["orders"]
    items_data = datasets["order_items"]

    if customers_data["customer_id"].isna().any():
        raise ValueError("customers.customer_id에 결측치가 있습니다.")
    if customers_data["customer_id"].duplicated().any():
        raise ValueError("customers.customer_id에 중복이 있습니다.")
    if orders_data["order_id"].isna().any():
        raise ValueError("orders.order_id에 결측치가 있습니다.")
    if orders_data["order_id"].duplicated().any():
        raise ValueError("orders.order_id에 중복이 있습니다.")

    order_totals = build_order_totals(items_data)

    orders_data["order_date"] = pd.to_datetime(
        orders_data["order_date"],
        errors="coerce",
    )

    model_data = orders_data.merge(
        order_totals,
        on="order_id",
        how="inner",
        validate="one_to_one",
    )

    model_data = model_data.merge(
        customers_data[
            [
                "customer_id",
                "gender",
                "age",
                "city",
            ]
        ],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    model_data["age"] = pd.to_numeric(
        model_data["age"],
        errors="coerce",
    )
    model_data[TARGET_COLUMN] = pd.to_numeric(
        model_data[TARGET_COLUMN],
        errors="coerce",
    )
    model_data["order_month"] = model_data["order_date"].dt.month
    model_data["order_dayofweek"] = model_data["order_date"].dt.dayofweek

    # Date and target are indispensable. Feature missing values are intentionally
    # left for the pipelines so imputation is learned from training data only.
    model_data = model_data.dropna(
        subset=[
            "order_date",
            TARGET_COLUMN,
        ]
    ).copy()

    if model_data.empty:
        raise ValueError("모델링에 사용할 수 있는 주문 데이터가 없습니다.")

    return model_data.sort_values(
        ["order_date", "order_id"]
    ).reset_index(drop=True)


def split_model_data_by_time(
    model_data: pd.DataFrame,
    test_size: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split chronologically so later orders remain unseen test data."""
    if not 0 < test_size < 1:
        raise ValueError("test_size는 0과 1 사이여야 합니다.")

    required = {
        "order_date",
        "order_id",
        TARGET_COLUMN,
        *FEATURE_COLUMNS,
    }
    missing = required - set(model_data.columns)
    if missing:
        raise KeyError(
            "시간 분할에 필요한 컬럼이 없습니다: "
            f"{sorted(missing)}"
        )

    sorted_data = model_data.sort_values(
        ["order_date", "order_id"]
    ).reset_index(drop=True)

    if len(sorted_data) < 5:
        raise ValueError(
            "시간 순서 훈련·테스트 분할에는 최소 5개 주문이 필요합니다."
        )

    split_index = int(len(sorted_data) * (1 - test_size))
    split_index = min(
        max(split_index, 1),
        len(sorted_data) - 1,
    )

    train_data = sorted_data.iloc[:split_index].copy()
    test_data = sorted_data.iloc[split_index:].copy()

    if train_data["order_date"].max() > test_data["order_date"].min():
        raise ValueError("훈련 기간과 테스트 기간의 시간 순서가 올바르지 않습니다.")

    return train_data, test_data


def split_features_target(
    model_data: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Backward-compatible wrapper returning chronological X/y splits.

    ``random_state`` is accepted for compatibility with earlier course code,
    but chronological splitting is deterministic and does not use it.
    """
    _ = random_state
    validate_feature_columns()

    train_data, test_data = split_model_data_by_time(
        model_data,
        test_size=test_size,
    )

    return (
        train_data[FEATURE_COLUMNS].copy(),
        test_data[FEATURE_COLUMNS].copy(),
        train_data[TARGET_COLUMN].copy(),
        test_data[TARGET_COLUMN].copy(),
    )


def make_preprocessor() -> ColumnTransformer:
    """Create train-only numeric and categorical preprocessing pipelines."""
    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                make_one_hot_encoder(),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def make_regression_models(
    random_state: int = 42,
) -> dict[str, Pipeline]:
    """Create baseline, linear, and random-forest regression pipelines."""
    return {
        "Baseline Mean": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(),
                ),
                (
                    "model",
                    DummyRegressor(strategy="mean"),
                ),
            ]
        ),
        "Linear Regression": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(),
                ),
                (
                    "model",
                    LinearRegression(),
                ),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(),
                ),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=300,
                        min_samples_leaf=5,
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def evaluate_predictions(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """Evaluate regression predictions with MAE, RMSE, and R²."""
    mse = mean_squared_error(
        y_true,
        y_pred,
    )
    return {
        "MAE": float(
            mean_absolute_error(
                y_true,
                y_pred,
            )
        ),
        "RMSE": float(np.sqrt(mse)),
        "R2": float(
            r2_score(
                y_true,
                y_pred,
            )
        ),
    }


def train_and_evaluate_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    random_state: int = 42,
) -> tuple[
    dict[str, Pipeline],
    pd.DataFrame,
    dict[str, np.ndarray],
]:
    """Fit all models and compare train/test performance against baseline."""
    validate_feature_columns(X_train.columns)
    if list(X_train.columns) != list(X_test.columns):
        raise ValueError("훈련·테스트 입력 컬럼 구성이 다릅니다.")

    models = make_regression_models(
        random_state=random_state
    )
    rows: list[dict[str, Any]] = []
    predictions: dict[str, np.ndarray] = {}

    for model_name, model in models.items():
        model.fit(
            X_train,
            y_train,
        )
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)

        train_metrics = evaluate_predictions(
            y_train,
            train_pred,
        )
        test_metrics = evaluate_predictions(
            y_test,
            test_pred,
        )

        rows.append(
            {
                "model": model_name,
                "train_MAE": train_metrics["MAE"],
                "test_MAE": test_metrics["MAE"],
                "test_RMSE": test_metrics["RMSE"],
                "test_R2": test_metrics["R2"],
            }
        )
        predictions[model_name] = test_pred

    comparison = pd.DataFrame(rows).sort_values(
        "test_MAE"
    ).reset_index(drop=True)

    baseline_rows = comparison.loc[
        comparison["model"].eq("Baseline Mean"),
        "test_MAE",
    ]
    if baseline_rows.empty:
        raise RuntimeError("Baseline Mean 평가 결과가 없습니다.")

    baseline_mae = float(baseline_rows.iloc[0])
    if baseline_mae == 0:
        comparison[
            "MAE_improvement_vs_baseline_pct"
        ] = np.nan
    else:
        comparison[
            "MAE_improvement_vs_baseline_pct"
        ] = (
            (
                baseline_mae
                - comparison["test_MAE"]
            )
            / baseline_mae
            * 100
        ).round(2)

    return models, comparison, predictions


def cross_validate_regression_models(
    models: dict[str, Pipeline],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    max_splits: int = 5,
) -> pd.DataFrame:
    """Evaluate non-baseline models with chronological cross-validation."""
    if len(X_train) < 6:
        raise ValueError("시간 순서 교차검증에는 최소 6개의 훈련 행이 필요합니다.")

    # Keep at least two validation rows per fold so R² is meaningful.
    max_splits_for_two_test_rows = max(
        2,
        len(X_train) // 2 - 1,
    )
    n_splits = min(
        max_splits,
        max_splits_for_two_test_rows,
        len(X_train) - 1,
    )
    if n_splits < 2:
        raise ValueError("TimeSeriesSplit의 n_splits는 최소 2여야 합니다.")

    time_cv = TimeSeriesSplit(
        n_splits=n_splits
    )
    rows: list[dict[str, float | str]] = []

    for model_name in [
        "Linear Regression",
        "Random Forest",
    ]:
        if model_name not in models:
            raise KeyError(f"교차검증할 모델이 없습니다: {model_name}")

        cv_result = cross_validate(
            models[model_name],
            X_train,
            y_train,
            cv=time_cv,
            scoring={
                "mae": "neg_mean_absolute_error",
                "r2": "r2",
            },
            error_score="raise",
        )

        rows.append(
            {
                "model": model_name,
                "cv_MAE_mean": float(
                    -cv_result["test_mae"].mean()
                ),
                "cv_MAE_std": float(
                    cv_result["test_mae"].std()
                ),
                "cv_R2_mean": float(
                    cv_result["test_r2"].mean()
                ),
            }
        )

    return pd.DataFrame(rows).sort_values(
        "cv_MAE_mean"
    ).reset_index(drop=True)


def select_diagnostic_model(
    model_comparison: pd.DataFrame,
) -> str:
    """Select the lowest-test-MAE non-baseline model for diagnostics."""
    candidates = model_comparison.loc[
        ~model_comparison["model"].eq(
            "Baseline Mean"
        )
    ].sort_values("test_MAE")

    if candidates.empty:
        raise ValueError("진단할 비베이스라인 모델 결과가 없습니다.")

    return str(candidates.iloc[0]["model"])


def create_prediction_result(
    test_data: pd.DataFrame,
    y_test: pd.Series,
    y_pred: np.ndarray,
    model_name: str,
) -> pd.DataFrame:
    """Create an internal-only residual table with order identifiers."""
    if len(test_data) != len(y_test) or len(y_test) != len(y_pred):
        raise ValueError("테스트 데이터와 예측값의 길이가 일치하지 않습니다.")

    result = (
        test_data[
            [
                "order_id",
                "order_date",
            ]
        ]
        .reset_index(drop=True)
        .copy()
    )
    result["actual_order_total"] = (
        y_test.reset_index(drop=True)
    )
    result["predicted_order_total"] = y_pred
    result["residual"] = (
        result["actual_order_total"]
        - result["predicted_order_total"]
    )
    result["abs_error"] = result["residual"].abs()
    result["model"] = model_name

    return result.sort_values(
        "abs_error",
        ascending=False,
    ).reset_index(drop=True)


def configure_korean_font() -> bool:
    """Configure an installed Korean font and return whether one was found."""
    available_fonts = {
        font.name
        for font in font_manager.fontManager.ttflist
    }
    candidates = [
        "Malgun Gothic",
        "AppleGothic",
        "NanumGothic",
        "Noto Sans CJK KR",
        "Noto Sans KR",
    ]

    for font_name in candidates:
        if font_name in available_fonts:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return True

    return False


def create_diagnostic_figures(
    prediction_result: pd.DataFrame,
    figure_dir: str | Path = "reports/figures",
) -> dict[str, Path]:
    """Save actual-vs-predicted and residual diagnostic figures."""
    output_dir = Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_name = str(
        prediction_result["model"].iloc[0]
    )
    korean_font_available = configure_korean_font()
    actual_path = (
        output_dir
        / "ch09_actual_vs_predicted.png"
    )
    residual_path = (
        output_dir
        / "ch09_residual_histogram.png"
    )

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(
        prediction_result["actual_order_total"],
        prediction_result["predicted_order_total"],
        alpha=0.7,
    )

    min_value = min(
        prediction_result["actual_order_total"].min(),
        prediction_result["predicted_order_total"].min(),
    )
    max_value = max(
        prediction_result["actual_order_total"].max(),
        prediction_result["predicted_order_total"].max(),
    )
    ax.plot(
        [min_value, max_value],
        [min_value, max_value],
        linestyle="--",
    )
    if korean_font_available:
        ax.set_title(
            f"실제 주문 금액과 예측값: {model_name}"
        )
        ax.set_xlabel("실제 주문 금액")
        ax.set_ylabel("예측 주문 금액")
    else:
        ax.set_title(
            f"Actual vs. predicted order total: {model_name}"
        )
        ax.set_xlabel("Actual order total")
        ax.set_ylabel("Predicted order total")
    fig.tight_layout()
    fig.savefig(
        actual_path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(
        prediction_result["residual"],
        bins=15,
    )
    ax.axvline(
        0,
        linestyle="--",
    )
    if korean_font_available:
        ax.set_title("예측 잔차 분포")
        ax.set_xlabel("잔차(실제값 - 예측값)")
        ax.set_ylabel("주문 수")
    else:
        ax.set_title("Prediction residual distribution")
        ax.set_xlabel("Residual (actual - predicted)")
        ax.set_ylabel("Order count")
    fig.tight_layout()
    fig.savefig(
        residual_path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    return {
        "actual_vs_predicted_figure": actual_path,
        "residual_figure": residual_path,
    }


def build_leakage_checklist() -> pd.DataFrame:
    """Return the review checklist used in the chapter and LLM prompts."""
    check_items = [
        "예측 시점이 명확한가?",
        "목표값과 목표값의 계산 재료를 입력에서 제외했는가?",
        "예측 이후에 알 수 있는 정보를 사용하지 않았는가?",
        "식별자를 일반 숫자 변수로 사용하지 않았는가?",
        "전처리기가 훈련 데이터 안에서만 학습되는가?",
        "시간 순서 또는 업무 목적에 맞는 분할을 사용했는가?",
        "단순 베이스라인과 비교했는가?",
        "테스트 데이터로 최종 성능을 평가했는가?",
        "MAE, RMSE, R²를 올바르게 해석했는가?",
        "음수 R²와 낮은 성능을 숨기지 않았는가?",
        "훈련 성능과 테스트 성능을 비교했는가?",
        "식별자가 포함된 내부 결과를 외부에 공개하지 않았는가?",
    ]
    return pd.DataFrame(
        {
            "check_item": check_items,
            "status": ["□"] * len(check_items),
        }
    )


def build_regression_report(
    model_data: pd.DataFrame,
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    model_comparison: pd.DataFrame,
    cv_summary: pd.DataFrame,
    prediction_result: pd.DataFrame,
    checklist: pd.DataFrame,
    selected_model_name: str,
) -> str:
    """Build a Markdown report aligned with the Chapter 9 interpretation."""
    baseline_mae = model_comparison.loc[
        model_comparison["model"].eq("Baseline Mean"),
        "test_MAE",
    ].iloc[0]
    selected_row = model_comparison.loc[
        model_comparison["model"].eq(selected_model_name)
    ].iloc[0]
    improvement = selected_row[
        "MAE_improvement_vs_baseline_pct"
    ]

    if pd.isna(improvement):
        baseline_interpretation = (
            "베이스라인 MAE가 0이어서 개선율을 계산하지 않았습니다."
        )
    elif improvement > 0:
        baseline_interpretation = (
            f"{selected_model_name}의 테스트 MAE가 "
            f"베이스라인보다 {improvement:.2f}% 낮았습니다."
        )
    else:
        baseline_interpretation = (
            f"{selected_model_name}의 테스트 MAE가 "
            "베이스라인보다 개선되지 않았습니다."
        )

    return f"""# Chapter 9 회귀 분석 요약 보고서

## 1. 분석 목적

주문 상세 수량·단가·금액을 모델 입력에서 제외한 상태에서,
주문 시점 정보와 고객의 비식별 특성만으로 주문별 상세 금액 합계를
추정하는 교육용 회귀 모델을 비교했습니다.

## 2. 모델링 데이터 개요

- 전체 행 수: {model_data.shape[0]}
- 훈련 행 수: {train_data.shape[0]}
- 테스트 행 수: {test_data.shape[0]}
- 훈련 기간: {train_data["order_date"].min()} ~ {train_data["order_date"].max()}
- 테스트 기간: {test_data["order_date"].min()} ~ {test_data["order_date"].max()}
- 예측 대상: {TARGET_COLUMN}
- 입력값: {", ".join(FEATURE_COLUMNS)}
- 베이스라인 테스트 MAE: {baseline_mae:,.2f}

## 3. 모델 비교 결과

```text
{model_comparison.to_string(index=False)}
```

{baseline_interpretation}

## 4. 시간 순서 교차검증

```text
{cv_summary.to_string(index=False)}
```

교차검증 평균과 표준편차가 불안정하거나 R²가 반복적으로 음수라면,
현재 입력 변수만으로는 주문 금액을 안정적으로 예측하기 어렵다는 뜻일 수 있습니다.

## 5. 내부 예측 오차 상위 10건

아래 결과에는 주문 식별자가 포함되어 있으므로 외부 공개용이 아닙니다.

```text
{prediction_result.head(10).to_string(index=False)}
```

## 6. 모델링 검토 체크리스트

```text
{checklist.to_string(index=False)}
```

## 7. 해석 시 주의사항

- MAE와 RMSE는 주문 금액과 같은 단위로 해석합니다.
- R²는 음수가 될 수 있으며, 이는 평균 예측보다 낮은 성능을 뜻합니다.
- 훈련 MAE가 낮고 테스트 MAE가 크면 과적합 가능성을 확인합니다.
- 현재 가상 데이터는 강한 예측 패턴이 설계되어 있지 않을 수 있습니다.
- 낮은 성능을 감추기 위해 목표값의 계산 재료를 입력에 추가하면 안 됩니다.
- 모델을 운영에 사용하지 않는 결정도 올바른 분석 결과가 될 수 있습니다.
- 주문 식별자가 포함된 예측 결과는 내부 검토용으로만 관리합니다.

## 8. 다음 단계

- 예측 시점 이전의 고객 구매 이력이나 프로모션 변수를 적법하게 추가합니다.
- 새로운 기간의 데이터로 성능을 다시 검증합니다.
- 시간 순서 교차검증의 변동 원인을 확인합니다.
- LLM이 만든 코드도 동일한 누수·분할·베이스라인 기준으로 검토합니다.
"""


def save_regression_outputs(
    model_data: pd.DataFrame,
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    model_comparison: pd.DataFrame,
    cv_summary: pd.DataFrame,
    prediction_result: pd.DataFrame,
    checklist: pd.DataFrame,
    selected_model_name: str,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """Save tables, internal diagnostics, report, and figures."""
    output_dir = Path(report_dir)
    figure_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "model_data_internal": (
            output_dir
            / "ch09_regression_model_data_internal.csv"
        ),
        "model_comparison": (
            output_dir
            / "ch09_regression_model_comparison.csv"
        ),
        "cv_summary": (
            output_dir
            / "ch09_regression_cv_summary.csv"
        ),
        "predictions_internal": (
            output_dir
            / "ch09_regression_predictions_internal.csv"
        ),
        "checklist": (
            output_dir
            / "ch09_regression_checklist.csv"
        ),
        "report": (
            output_dir
            / "ch09_regression_report.md"
        ),
    }

    model_data.to_csv(
        paths["model_data_internal"],
        index=False,
        encoding="utf-8-sig",
    )
    model_comparison.to_csv(
        paths["model_comparison"],
        index=False,
        encoding="utf-8-sig",
    )
    cv_summary.to_csv(
        paths["cv_summary"],
        index=False,
        encoding="utf-8-sig",
    )
    prediction_result.to_csv(
        paths["predictions_internal"],
        index=False,
        encoding="utf-8-sig",
    )
    checklist.to_csv(
        paths["checklist"],
        index=False,
        encoding="utf-8-sig",
    )

    report_text = build_regression_report(
        model_data=model_data,
        train_data=train_data,
        test_data=test_data,
        model_comparison=model_comparison,
        cv_summary=cv_summary,
        prediction_result=prediction_result,
        checklist=checklist,
        selected_model_name=selected_model_name,
    )
    paths["report"].write_text(
        report_text,
        encoding="utf-8",
    )

    figure_paths = create_diagnostic_figures(
        prediction_result=prediction_result,
        figure_dir=figure_dir,
    )
    paths.update(figure_paths)

    return paths


def run_regression_analysis(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, object]:
    """Run the complete leakage-aware Chapter 9 regression workflow."""
    data = load_regression_source_data(
        processed_dir
    )
    model_data = build_regression_dataset(
        customers=data["customers"],
        orders=data["orders"],
        order_items=data["order_items"],
    )

    train_data, test_data = split_model_data_by_time(
        model_data,
        test_size=test_size,
    )
    X_train = train_data[FEATURE_COLUMNS].copy()
    X_test = test_data[FEATURE_COLUMNS].copy()
    y_train = train_data[TARGET_COLUMN].copy()
    y_test = test_data[TARGET_COLUMN].copy()

    models, model_comparison, predictions = (
        train_and_evaluate_models(
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            random_state=random_state,
        )
    )

    cv_summary = cross_validate_regression_models(
        models=models,
        X_train=X_train,
        y_train=y_train,
    )

    selected_model_name = select_diagnostic_model(
        model_comparison
    )
    prediction_result = create_prediction_result(
        test_data=test_data,
        y_test=y_test,
        y_pred=predictions[selected_model_name],
        model_name=selected_model_name,
    )
    checklist = build_leakage_checklist()
    output_paths = save_regression_outputs(
        model_data=model_data,
        train_data=train_data,
        test_data=test_data,
        model_comparison=model_comparison,
        cv_summary=cv_summary,
        prediction_result=prediction_result,
        checklist=checklist,
        selected_model_name=selected_model_name,
        report_dir=report_dir,
    )

    return {
        "data": data,
        "model_data": model_data,
        "train_data": train_data,
        "test_data": test_data,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "models": models,
        "model_comparison": model_comparison,
        "predictions": predictions,
        "cv_summary": cv_summary,
        "selected_model_name": selected_model_name,
        # Keep the earlier key as an alias for notebooks/scripts that used it.
        "best_model_name": selected_model_name,
        "prediction_result": prediction_result,
        "checklist": checklist,
        "output_paths": output_paths,
    }
