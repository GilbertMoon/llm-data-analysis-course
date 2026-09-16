"""Chapter 9 leakage-aware regression analysis utilities.

The workflow intentionally separates model selection from final test evaluation:

1. build the order-level target from order details,
2. keep target ingredients and post-outcome information out of features,
3. split chronologically without placing the same calendar day in both sets,
4. learn preprocessing inside sklearn Pipelines,
5. compare candidate models with TimeSeriesSplit on the training period,
6. freeze the selected non-baseline model before looking at final test metrics,
7. compare the frozen model with a mean DummyRegressor on the final test period,
8. save internal identifier-bearing diagnostics separately from public reports.
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
NUMERIC_FEATURES = ["order_month", "order_dayofweek", "age"]
CATEGORICAL_FEATURES = ["payment_method", "gender", "city"]
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
    "product_id",
}

FORBIDDEN_REASONS = {
    "order_total": "예측 대상 자체",
    "line_total": "목표값을 구성하는 주문 상세 금액",
    "quantity": "목표값 계산 재료",
    "unit_price": "목표값 계산 재료",
    "item_count": "주문 상세가 확인된 뒤 계산되는 사후 집계",
    "total_quantity": "주문 상세에서 만든 목표 대리 변수",
    "avg_unit_price": "주문 상세에서 만든 목표 대리 변수",
    "order_status": "예측 시점 이후에 확정될 수 있는 사후 정보",
    "order_id": "주문 식별자",
    "customer_id": "고객 식별자",
    "product_id": "주문 상세가 확인되어야 알 수 있는 식별자",
}

REQUIRED_COLUMNS = {
    "customers": {"customer_id", "gender", "age", "city"},
    "orders": {
        "order_id",
        "customer_id",
        "order_date",
        "payment_method",
        "order_status",
    },
    "order_items": {"order_id", "quantity", "unit_price"},
}


def make_one_hot_encoder() -> OneHotEncoder:
    """Return a dense encoder compatible with multiple sklearn versions."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_regression_source_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """Load Chapter09 validated processed files; never silently fall back to raw data."""
    input_dir = Path(processed_dir)
    file_map = {
        "customers": input_dir / "customers_clean.csv",
        "orders": input_dir / "orders_clean.csv",
        "order_items": input_dir / "order_items_clean.csv",
    }
    missing_files = [path for path in file_map.values() if not path.exists()]
    if missing_files:
        raise FileNotFoundError(
            "Chapter09 모델링 입력이 없습니다. 먼저 `python scripts/prepare_ch09_data.py`를 실행하세요. "
            + "누락 파일: "
            + ", ".join(str(path) for path in missing_files)
        )
    return {name: pd.read_csv(path) for name, path in file_map.items()}


def validate_required_columns(datasets: dict[str, pd.DataFrame]) -> None:
    """Fail fast when a required dataset or modeling column is missing."""
    missing_datasets = sorted(set(REQUIRED_COLUMNS) - set(datasets))
    if missing_datasets:
        raise KeyError(f"필수 데이터셋이 없습니다: {missing_datasets}")
    for name, columns in REQUIRED_COLUMNS.items():
        missing_columns = sorted(columns - set(datasets[name].columns))
        if missing_columns:
            raise KeyError(f"{name}에 필요한 컬럼이 없습니다: {missing_columns}")


def validate_feature_columns(
    feature_columns: Iterable[str] = FEATURE_COLUMNS,
) -> None:
    """Reject target values, target proxies, post-outcome fields, and identifiers."""
    columns = list(feature_columns)
    leaked_features = sorted(set(columns) & FORBIDDEN_FEATURES)
    if leaked_features:
        raise ValueError(f"입력값에 누수 위험 컬럼이 있습니다: {leaked_features}")
    duplicates = pd.Index(columns)[pd.Index(columns).duplicated()].tolist()
    if duplicates:
        raise ValueError(f"입력값 목록에 중복 컬럼이 있습니다: {duplicates}")


def _require_unique_key(df: pd.DataFrame, key: str, dataset: str) -> None:
    if key not in df.columns:
        raise KeyError(f"{dataset}.{key} 컬럼이 없습니다.")
    missing_count = int(df[key].isna().sum())
    duplicate_count = int(df[key].duplicated().sum())
    if missing_count or duplicate_count:
        raise ValueError(
            f"{dataset}.{key} 검증 실패: "
            f"missing={missing_count}, duplicate={duplicate_count}"
        )


def build_order_totals(order_items: pd.DataFrame) -> pd.DataFrame:
    """Create order_total and verify line_total = quantity * unit_price."""
    items = order_items.copy()
    missing = sorted({"order_id", "quantity", "unit_price"} - set(items.columns))
    if missing:
        raise KeyError(f"order_items에 필요한 컬럼이 없습니다: {missing}")

    items["quantity"] = pd.to_numeric(items["quantity"], errors="coerce")
    items["unit_price"] = pd.to_numeric(items["unit_price"], errors="coerce")
    invalid = items[["order_id", "quantity", "unit_price"]].isna().any(axis=1)
    if invalid.any():
        raise ValueError(
            "주문 금액 목표값을 만들 수 없는 주문 상세 행이 있습니다: "
            f"{int(invalid.sum())}건"
        )

    expected = items["quantity"] * items["unit_price"]
    if "line_total" in items.columns:
        items["line_total"] = pd.to_numeric(items["line_total"], errors="coerce")
        if items["line_total"].isna().any():
            raise ValueError("order_items.line_total에 숫자 변환 실패가 있습니다.")
        mismatch = (items["line_total"] - expected).abs().gt(1e-6)
        if mismatch.any():
            raise ValueError(
                "line_total과 quantity × unit_price가 일치하지 않는 행이 있습니다: "
                f"{int(mismatch.sum())}건"
            )
    else:
        items["line_total"] = expected

    if (items["line_total"] <= 0).any():
        raise ValueError("주문 금액 목표값에 0 이하의 line_total이 있습니다.")

    return (
        items.groupby("order_id", as_index=False)
        .agg(order_total=("line_total", "sum"))
        .sort_values("order_id")
        .reset_index(drop=True)
    )


def build_regression_dataset(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """Build one-row-per-order modeling data and reject silent join losses."""
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

    _require_unique_key(customers_data, "customer_id", "customers")
    _require_unique_key(orders_data, "order_id", "orders")
    if orders_data["customer_id"].isna().any():
        raise ValueError("orders.customer_id에 결측치가 있습니다.")
    if items_data["order_id"].isna().any():
        raise ValueError("order_items.order_id에 결측치가 있습니다.")

    order_totals = build_order_totals(items_data)
    merged = orders_data.merge(
        order_totals,
        on="order_id",
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    unmatched = merged.loc[merged["_merge"].ne("both")]
    if not unmatched.empty:
        raise ValueError(
            "orders와 주문별 목표값의 관계가 완전하지 않습니다: "
            f"{merged['_merge'].value_counts().to_dict()}"
        )
    model_data = merged.drop(columns="_merge")

    model_data = model_data.merge(
        customers_data[["customer_id", "gender", "age", "city"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    unmatched_customer_count = int(model_data["_merge"].eq("left_only").sum())
    if unmatched_customer_count:
        raise ValueError(
            "orders.customer_id가 customers에 연결되지 않는 주문이 있습니다: "
            f"{unmatched_customer_count}건"
        )
    model_data = model_data.drop(columns="_merge")

    model_data["order_date"] = pd.to_datetime(model_data["order_date"], errors="coerce")
    if model_data["order_date"].isna().any():
        raise ValueError(
            "order_date 날짜 변환 실패가 있습니다: "
            f"{int(model_data['order_date'].isna().sum())}건"
        )
    model_data["age"] = pd.to_numeric(model_data["age"], errors="coerce")
    model_data[TARGET_COLUMN] = pd.to_numeric(model_data[TARGET_COLUMN], errors="coerce")
    if model_data[TARGET_COLUMN].isna().any():
        raise ValueError("order_total 목표값에 결측치가 있습니다.")
    if (model_data[TARGET_COLUMN] <= 0).any():
        raise ValueError("order_total 목표값에 0 이하 값이 있습니다.")

    model_data["order_month"] = model_data["order_date"].dt.month
    model_data["order_dayofweek"] = model_data["order_date"].dt.dayofweek
    return model_data.sort_values(["order_date", "order_id"]).reset_index(drop=True)


def split_model_data_by_time(
    model_data: pd.DataFrame,
    test_size: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by calendar-day groups; the same date cannot appear in both sets."""
    if not 0 < test_size < 1:
        raise ValueError("test_size는 0과 1 사이여야 합니다.")

    required = {"order_date", "order_id", TARGET_COLUMN, *FEATURE_COLUMNS}
    missing = sorted(required - set(model_data.columns))
    if missing:
        raise KeyError(f"시간 분할에 필요한 컬럼이 없습니다: {missing}")

    data = model_data.sort_values(["order_date", "order_id"]).reset_index(drop=True).copy()
    data["_split_day"] = data["order_date"].dt.normalize()
    unique_days = pd.Index(data["_split_day"].drop_duplicates())
    if len(unique_days) < 2:
        raise ValueError("시간 순서 분할에는 최소 2개의 서로 다른 주문일이 필요합니다.")

    split_day_index = int(len(unique_days) * (1 - test_size))
    split_day_index = min(max(split_day_index, 1), len(unique_days) - 1)
    test_start_day = unique_days[split_day_index]

    train_data = data.loc[data["_split_day"] < test_start_day].drop(columns="_split_day")
    test_data = data.loc[data["_split_day"] >= test_start_day].drop(columns="_split_day")
    if len(train_data) < 2 or len(test_data) < 2:
        raise ValueError("훈련·테스트에 각각 최소 2개 주문이 필요합니다.")
    if train_data["order_date"].max().normalize() >= test_data["order_date"].min().normalize():
        raise ValueError("같은 주문일이 훈련과 테스트에 동시에 포함되었습니다.")

    return train_data.reset_index(drop=True), test_data.reset_index(drop=True)


def split_features_target(
    model_data: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Compatibility wrapper returning chronological X/y splits."""
    _ = random_state
    validate_feature_columns()
    train_data, test_data = split_model_data_by_time(model_data, test_size=test_size)
    return (
        train_data[FEATURE_COLUMNS].copy(),
        test_data[FEATURE_COLUMNS].copy(),
        train_data[TARGET_COLUMN].copy(),
        test_data[TARGET_COLUMN].copy(),
    )


def make_preprocessor() -> ColumnTransformer:
    """Create train-only numeric and categorical preprocessing pipelines."""
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", make_one_hot_encoder()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )


def make_regression_models(random_state: int = 42) -> dict[str, Pipeline]:
    """Create fixed candidates used for training-period model selection."""
    return {
        "Baseline Mean": Pipeline(
            [("preprocessor", make_preprocessor()), ("model", DummyRegressor(strategy="mean"))]
        ),
        "Linear Regression": Pipeline(
            [("preprocessor", make_preprocessor()), ("model", LinearRegression())]
        ),
        "Random Forest": Pipeline(
            [
                ("preprocessor", make_preprocessor()),
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
    mse = mean_squared_error(y_true, y_pred)
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mse)),
        "R2": float(r2_score(y_true, y_pred)),
    }


def _choose_time_series_splits(n_rows: int, max_splits: int = 5) -> int:
    candidates = [
        n
        for n in range(2, min(max_splits, n_rows - 1) + 1)
        if n_rows // (n + 1) >= 2
    ]
    if not candidates:
        raise ValueError(
            "시간 순서 교차검증에는 각 validation fold에 최소 2개 행이 필요합니다."
        )
    return max(candidates)


def cross_validate_regression_models(
    models: dict[str, Pipeline],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    max_splits: int = 5,
) -> pd.DataFrame:
    """Compare all fixed candidates using training-period TimeSeriesSplit only."""
    validate_feature_columns(X_train.columns)
    if len(X_train) < 6:
        raise ValueError("시간 순서 교차검증에는 최소 6개의 훈련 행이 필요합니다.")

    n_splits = _choose_time_series_splits(len(X_train), max_splits)
    time_cv = TimeSeriesSplit(n_splits=n_splits)
    rows: list[dict[str, Any]] = []
    for model_name, model in models.items():
        cv_result = cross_validate(
            model,
            X_train,
            y_train,
            cv=time_cv,
            scoring={"mae": "neg_mean_absolute_error", "r2": "r2"},
            error_score="raise",
        )
        rows.append(
            {
                "model": model_name,
                "n_splits": n_splits,
                "cv_MAE_mean": float(-cv_result["test_mae"].mean()),
                "cv_MAE_std": float(cv_result["test_mae"].std()),
                "cv_R2_mean": float(cv_result["test_r2"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["cv_MAE_mean", "model"]).reset_index(drop=True)


def select_diagnostic_model(cv_summary: pd.DataFrame) -> str:
    """Freeze the best non-baseline candidate using training-only CV MAE."""
    required = {"model", "cv_MAE_mean"}
    missing = sorted(required - set(cv_summary.columns))
    if missing:
        raise KeyError(f"CV 요약에 필요한 컬럼이 없습니다: {missing}")
    candidates = cv_summary.loc[
        ~cv_summary["model"].eq("Baseline Mean")
    ].sort_values(["cv_MAE_mean", "model"])
    if candidates.empty:
        raise ValueError("선택할 비베이스라인 모델 결과가 없습니다.")
    return str(candidates.iloc[0]["model"])


def train_and_evaluate_models(
    models: dict[str, Pipeline],
    selected_model_name: str,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Evaluate only baseline and the frozen selected model on final test."""
    validate_feature_columns(X_train.columns)
    if list(X_train.columns) != list(X_test.columns):
        raise ValueError("훈련·테스트 입력 컬럼 구성이 다릅니다.")
    if selected_model_name == "Baseline Mean":
        raise ValueError("선택 모델은 비베이스라인 후보여야 합니다.")
    if selected_model_name not in models or "Baseline Mean" not in models:
        raise KeyError("최종 평가에 필요한 모델이 없습니다.")

    rows: list[dict[str, Any]] = []
    predictions: dict[str, np.ndarray] = {}
    for model_name in ["Baseline Mean", selected_model_name]:
        model = models[model_name]
        model.fit(X_train, y_train)
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        train_metrics = evaluate_predictions(y_train, train_pred)
        test_metrics = evaluate_predictions(y_test, test_pred)
        rows.append(
            {
                "model": model_name,
                "selection_role": (
                    "baseline" if model_name == "Baseline Mean" else "selected_by_train_cv"
                ),
                "train_MAE": train_metrics["MAE"],
                "test_MAE": test_metrics["MAE"],
                "test_RMSE": test_metrics["RMSE"],
                "test_R2": test_metrics["R2"],
            }
        )
        predictions[model_name] = test_pred

    comparison = pd.DataFrame(rows)
    baseline_mae = float(
        comparison.loc[comparison["model"].eq("Baseline Mean"), "test_MAE"].iloc[0]
    )
    if baseline_mae == 0:
        comparison["MAE_improvement_vs_baseline_pct"] = np.nan
    else:
        comparison["MAE_improvement_vs_baseline_pct"] = (
            (baseline_mae - comparison["test_MAE"]) / baseline_mae * 100
        ).round(2)
    return comparison.reset_index(drop=True), predictions


def build_split_summary(train_data: pd.DataFrame, test_data: pd.DataFrame) -> pd.DataFrame:
    total_rows = len(train_data) + len(test_data)
    return pd.DataFrame(
        [
            {
                "split": "train",
                "rows": len(train_data),
                "ratio_pct": round(len(train_data) / total_rows * 100, 2),
                "start_date": train_data["order_date"].min(),
                "end_date": train_data["order_date"].max(),
            },
            {
                "split": "test",
                "rows": len(test_data),
                "ratio_pct": round(len(test_data) / total_rows * 100, 2),
                "start_date": test_data["order_date"].min(),
                "end_date": test_data["order_date"].max(),
            },
        ]
    )


def build_feature_audit() -> pd.DataFrame:
    allowed = [
        {
            "column": column,
            "selected": True,
            "role": "allowed_feature",
            "reason": "교육용 예측 시점에 사용 가능하다고 가정",
        }
        for column in FEATURE_COLUMNS
    ]
    forbidden = [
        {
            "column": column,
            "selected": False,
            "role": "forbidden",
            "reason": FORBIDDEN_REASONS[column],
        }
        for column in sorted(FORBIDDEN_FEATURES)
    ]
    return pd.DataFrame(allowed + forbidden)


def create_prediction_result(
    test_data: pd.DataFrame,
    y_test: pd.Series,
    y_pred: np.ndarray,
    model_name: str,
) -> pd.DataFrame:
    if len(test_data) != len(y_test) or len(y_test) != len(y_pred):
        raise ValueError("테스트 데이터와 예측값의 길이가 일치하지 않습니다.")
    result = test_data[["order_id", "order_date"]].reset_index(drop=True).copy()
    result["actual_order_total"] = y_test.reset_index(drop=True)
    result["predicted_order_total"] = y_pred
    result["residual"] = result["actual_order_total"] - result["predicted_order_total"]
    result["abs_error"] = result["residual"].abs()
    result["model"] = model_name
    return result.sort_values("abs_error", ascending=False).reset_index(drop=True)


def public_prediction_result(prediction_result: pd.DataFrame) -> pd.DataFrame:
    return prediction_result[
        [
            "order_date",
            "actual_order_total",
            "predicted_order_total",
            "residual",
            "abs_error",
            "model",
        ]
    ].copy()


def configure_korean_font() -> bool:
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    for font_name in [
        "Malgun Gothic",
        "AppleGothic",
        "NanumGothic",
        "Noto Sans CJK KR",
        "Noto Sans KR",
    ]:
        if font_name in available_fonts:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return True
    return False


def create_diagnostic_figures(
    prediction_result: pd.DataFrame,
    figure_dir: str | Path = "reports/figures",
) -> dict[str, Path]:
    if prediction_result.empty:
        raise ValueError("예측 진단 결과가 비어 있습니다.")
    output_dir = Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_name = str(prediction_result["model"].iloc[0])
    korean = configure_korean_font()
    actual_path = output_dir / "ch09_actual_vs_predicted.png"
    residual_path = output_dir / "ch09_residual_histogram.png"

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
    ax.plot([min_value, max_value], [min_value, max_value], linestyle="--")
    ax.set_title(
        f"실제 주문 금액과 예측값: {model_name}"
        if korean
        else f"Actual vs. predicted order total: {model_name}"
    )
    ax.set_xlabel("실제 주문 금액" if korean else "Actual order total")
    ax.set_ylabel("예측 주문 금액" if korean else "Predicted order total")
    fig.tight_layout()
    fig.savefig(actual_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(prediction_result["residual"], bins=15)
    ax.axvline(0, linestyle="--")
    ax.set_title("예측 잔차 분포" if korean else "Prediction residual distribution")
    ax.set_xlabel("잔차(실제값 - 예측값)" if korean else "Residual (actual - predicted)")
    ax.set_ylabel("주문 수" if korean else "Order count")
    fig.tight_layout()
    fig.savefig(residual_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "actual_vs_predicted_figure": actual_path,
        "residual_figure": residual_path,
    }


def build_leakage_checklist() -> pd.DataFrame:
    check_items = [
        "예측 시점이 명확한가?",
        "목표값과 목표값의 계산 재료를 입력에서 제외했는가?",
        "예측 이후에 알 수 있는 정보를 사용하지 않았는가?",
        "식별자를 일반 숫자 변수로 사용하지 않았는가?",
        "전처리기가 훈련 데이터 안에서만 학습되는가?",
        "같은 날짜가 train과 test에 동시에 포함되지 않는가?",
        "후보 모델 선택을 훈련 기간 TimeSeriesSplit에서만 수행했는가?",
        "모델 선택을 고정한 뒤 test를 최종 평가에만 사용했는가?",
        "DummyRegressor 베이스라인과 비교했는가?",
        "MAE, RMSE, R²를 올바르게 해석했는가?",
        "음수 R²와 낮은 성능을 숨기지 않았는가?",
        "식별자가 포함된 내부 결과를 외부에 공개하지 않았는가?",
    ]
    return pd.DataFrame({"check_item": check_items, "status": ["□"] * len(check_items)})


def build_regression_validation(
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    cv_summary: pd.DataFrame,
    selected_model_name: str,
    model_comparison: pd.DataFrame,
) -> pd.DataFrame:
    """Create machine-checkable evidence for the core Chapter09 rules."""
    leaked_features = sorted(set(FEATURE_COLUMNS) & FORBIDDEN_FEATURES)
    strict_time_order = (
        train_data["order_date"].max().normalize()
        < test_data["order_date"].min().normalize()
    )
    selected_in_cv = selected_model_name in set(cv_summary["model"])
    baseline_present = "Baseline Mean" in set(model_comparison["model"])
    selected_present = selected_model_name in set(model_comparison["model"])
    rows = [
        ["forbidden_feature_overlap", len(leaked_features), not leaked_features],
        ["strict_train_before_test", strict_time_order, strict_time_order],
        ["selected_model_exists_in_train_cv", selected_in_cv, selected_in_cv],
        ["final_test_contains_baseline", baseline_present, baseline_present],
        [
            "final_test_contains_frozen_selected_model",
            selected_present,
            selected_present,
        ],
        ["test_rows_for_r2", len(test_data), len(test_data) >= 2],
    ]
    validation = pd.DataFrame(rows, columns=["check", "value", "passed"])
    validation["status"] = validation["passed"].map({True: "PASS", False: "FAIL"})
    failed = validation.loc[validation["status"].eq("FAIL")]
    if not failed.empty:
        raise ValueError(
            "회귀 분석 핵심 검증에 실패했습니다:\n" + failed.to_string(index=False)
        )
    return validation.drop(columns="passed")


def build_regression_report(
    model_data: pd.DataFrame,
    split_summary: pd.DataFrame,
    feature_audit: pd.DataFrame,
    cv_summary: pd.DataFrame,
    selected_model_name: str,
    model_comparison: pd.DataFrame,
    prediction_result: pd.DataFrame,
    validation: pd.DataFrame,
    checklist: pd.DataFrame,
) -> str:
    baseline_mae = float(
        model_comparison.loc[
            model_comparison["model"].eq("Baseline Mean"), "test_MAE"
        ].iloc[0]
    )
    selected_row = model_comparison.loc[
        model_comparison["model"].eq(selected_model_name)
    ].iloc[0]
    improvement = selected_row["MAE_improvement_vs_baseline_pct"]
    if pd.isna(improvement):
        baseline_text = "베이스라인 MAE가 0이어서 개선율을 계산하지 않았습니다."
    elif improvement > 0:
        baseline_text = (
            f"{selected_model_name}의 최종 테스트 MAE가 "
            f"베이스라인보다 {improvement:.2f}% 낮았습니다."
        )
    else:
        baseline_text = (
            f"{selected_model_name}의 최종 테스트 MAE가 베이스라인보다 개선되지 않았습니다."
        )

    public_errors = public_prediction_result(prediction_result).head(10)
    return f"""# Chapter 9 회귀 분석 요약 보고서

## 1. 분석 목적과 예측 시점
주문 상세 수량·단가·금액은 모델 입력에서 제외하고, 주문 시점 정보와 고객의 비식별 특성만으로 주문별 `order_total`을 추정합니다.

후보 모델 선택은 **훈련 기간 내부 TimeSeriesSplit**으로만 수행했고, 선택 모델을 고정한 뒤 테스트 기간을 최종 평가에 사용했습니다.

## 2. 모델링 데이터와 분할
- 전체 행 수: {model_data.shape[0]}
- 예측 대상: {TARGET_COLUMN}
- 입력값: {", ".join(FEATURE_COLUMNS)}

```text
{split_summary.to_string(index=False)}
```

## 3. Feature Audit
```text
{feature_audit.to_string(index=False)}
```

## 4. 훈련 기간 후보 모델 비교
```text
{cv_summary.to_string(index=False)}
```

선택 모델: **{selected_model_name}**

## 5. 최종 테스트 평가
```text
{model_comparison.to_string(index=False)}
```

{baseline_text}

## 6. 공개 가능한 오차 상위 10건
```text
{public_errors.to_string(index=False)}
```

## 7. 자동 검증 Evidence
```text
{validation.to_string(index=False)}
```

## 8. 사람 검토 체크리스트
```text
{checklist.to_string(index=False)}
```

## 9. 해석 시 주의사항
- MAE와 RMSE는 주문 금액과 같은 단위로 해석합니다.
- R²는 음수가 될 수 있습니다.
- 낮은 성능을 감추기 위해 목표 계산 재료나 사후 정보를 feature로 추가하지 않습니다.
- 테스트 결과를 본 뒤 후보를 다시 고르면 Final Test 역할이 깨집니다.
- 모델을 운영하지 않는 결정도 올바른 분석 결과가 될 수 있습니다.
"""


def save_regression_outputs(
    model_data: pd.DataFrame,
    split_summary: pd.DataFrame,
    feature_audit: pd.DataFrame,
    cv_summary: pd.DataFrame,
    selected_model_name: str,
    model_comparison: pd.DataFrame,
    prediction_result: pd.DataFrame,
    validation: pd.DataFrame,
    checklist: pd.DataFrame,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    output_dir = Path(report_dir)
    figure_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "model_data_internal": output_dir / "ch09_regression_model_data_internal.csv",
        "split_summary": output_dir / "ch09_regression_split_summary.csv",
        "feature_audit": output_dir / "ch09_regression_feature_audit.csv",
        "cv_summary": output_dir / "ch09_regression_cv_summary.csv",
        "model_comparison": output_dir / "ch09_regression_model_comparison.csv",
        "predictions_internal": output_dir / "ch09_regression_predictions_internal.csv",
        "validation": output_dir / "ch09_regression_validation.csv",
        "checklist": output_dir / "ch09_regression_checklist.csv",
        "report": output_dir / "ch09_regression_report.md",
    }
    model_data.to_csv(paths["model_data_internal"], index=False, encoding="utf-8-sig")
    split_summary.to_csv(paths["split_summary"], index=False, encoding="utf-8-sig")
    feature_audit.to_csv(paths["feature_audit"], index=False, encoding="utf-8-sig")
    cv_summary.to_csv(paths["cv_summary"], index=False, encoding="utf-8-sig")
    model_comparison.to_csv(paths["model_comparison"], index=False, encoding="utf-8-sig")
    prediction_result.to_csv(
        paths["predictions_internal"], index=False, encoding="utf-8-sig"
    )
    validation.to_csv(paths["validation"], index=False, encoding="utf-8-sig")
    checklist.to_csv(paths["checklist"], index=False, encoding="utf-8-sig")
    report_text = build_regression_report(
        model_data=model_data,
        split_summary=split_summary,
        feature_audit=feature_audit,
        cv_summary=cv_summary,
        selected_model_name=selected_model_name,
        model_comparison=model_comparison,
        prediction_result=prediction_result,
        validation=validation,
        checklist=checklist,
    )
    paths["report"].write_text(report_text, encoding="utf-8")
    paths.update(create_diagnostic_figures(prediction_result, figure_dir))
    return paths


def run_regression_analysis(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, object]:
    """Run the complete Chapter09 workflow with train-only model selection."""
    data = load_regression_source_data(processed_dir)
    model_data = build_regression_dataset(
        customers=data["customers"],
        orders=data["orders"],
        order_items=data["order_items"],
    )
    train_data, test_data = split_model_data_by_time(model_data, test_size=test_size)
    X_train = train_data[FEATURE_COLUMNS].copy()
    X_test = test_data[FEATURE_COLUMNS].copy()
    y_train = train_data[TARGET_COLUMN].copy()
    y_test = test_data[TARGET_COLUMN].copy()

    models = make_regression_models(random_state=random_state)
    cv_summary = cross_validate_regression_models(models, X_train, y_train)
    selected_model_name = select_diagnostic_model(cv_summary)

    model_comparison, predictions = train_and_evaluate_models(
        models=models,
        selected_model_name=selected_model_name,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
    )
    prediction_result = create_prediction_result(
        test_data=test_data,
        y_test=y_test,
        y_pred=predictions[selected_model_name],
        model_name=selected_model_name,
    )
    split_summary = build_split_summary(train_data, test_data)
    feature_audit = build_feature_audit()
    validation = build_regression_validation(
        train_data=train_data,
        test_data=test_data,
        cv_summary=cv_summary,
        selected_model_name=selected_model_name,
        model_comparison=model_comparison,
    )
    checklist = build_leakage_checklist()
    output_paths = save_regression_outputs(
        model_data=model_data,
        split_summary=split_summary,
        feature_audit=feature_audit,
        cv_summary=cv_summary,
        selected_model_name=selected_model_name,
        model_comparison=model_comparison,
        prediction_result=prediction_result,
        validation=validation,
        checklist=checklist,
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
        "cv_summary": cv_summary,
        "selected_model_name": selected_model_name,
        "best_model_name": selected_model_name,
        "model_comparison": model_comparison,
        "predictions": predictions,
        "prediction_result": prediction_result,
        "split_summary": split_summary,
        "feature_audit": feature_audit,
        "validation": validation,
        "checklist": checklist,
        "output_paths": output_paths,
    }
