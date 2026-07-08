"""Chapter 15 기말 종합 프로젝트 공통 함수 모음.

온라인 쇼핑몰 고객·상품·주문 데이터를 바탕으로 데이터 구조 점검, 전처리, EDA, 시각화,
회귀/분류 모델링, 외부 데이터 통합, LLM 활용 기록, 자동화 설계, 최종 보고서 생성을 하나의
프로젝트 흐름으로 실행합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


RAW_FILES = {
    "customers": "customers.csv",
    "products": "products.csv",
    "orders": "orders.csv",
    "order_items": "order_items.csv",
}


def get_project_paths(base_dir: str | Path = ".") -> dict[str, Path]:
    """15장 프로젝트 주요 폴더 경로를 반환하고 필요한 폴더를 생성합니다."""
    base_path = Path(base_dir).resolve()
    paths = {
        "base_dir": base_path,
        "raw_dir": base_path / "data" / "raw",
        "processed_dir": base_path / "data" / "processed",
        "external_dir": base_path / "data" / "external",
        "report_dir": base_path / "reports",
        "figure_dir": base_path / "reports" / "figures",
    }
    for key in ["processed_dir", "external_dir", "report_dir", "figure_dir"]:
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def make_one_hot_encoder() -> OneHotEncoder:
    """scikit-learn 버전에 맞는 OneHotEncoder를 생성합니다."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_raw_data(base_dir: str | Path = ".") -> dict[str, pd.DataFrame]:
    """기말 프로젝트 원본 데이터를 불러옵니다."""
    paths = get_project_paths(base_dir)
    missing = [filename for filename in RAW_FILES.values() if not (paths["raw_dir"] / filename).exists()]
    if missing:
        raise FileNotFoundError(
            "원본 데이터 파일이 없습니다: " + ", ".join(missing) +
            ". 먼저 python scripts/generate_sample_data.py 를 실행하세요."
        )
    return {name: pd.read_csv(paths["raw_dir"] / filename) for name, filename in RAW_FILES.items()}


def build_dataset_summary(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """데이터셋 구조 요약표를 생성합니다."""
    return pd.DataFrame(
        [
            {
                "dataset": name,
                "rows": df.shape[0],
                "columns": df.shape[1],
                "column_list": ", ".join(df.columns),
                "missing_values": int(df.isna().sum().sum()),
                "duplicated_rows": int(df.duplicated().sum()),
            }
            for name, df in datasets.items()
        ]
    )


def strip_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """문자열 컬럼의 앞뒤 공백을 제거합니다."""
    result = df.copy()
    for col in result.select_dtypes(include="object").columns:
        result[col] = result[col].where(result[col].isna(), result[col].astype(str).str.strip())
    return result


def to_number(series: pd.Series) -> pd.Series:
    """쉼표가 포함된 문자열 숫자를 숫자형으로 변환합니다."""
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def preprocess_project_data(datasets: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """최종 프로젝트용 전처리를 수행하고 전처리 전후 비교표를 반환합니다."""
    raw_summary = build_dataset_summary(datasets)

    customers = strip_string_columns(datasets["customers"])
    products = strip_string_columns(datasets["products"])
    orders = strip_string_columns(datasets["orders"])
    order_items = strip_string_columns(datasets["order_items"])

    if "age" in customers.columns:
        customers["age"] = to_number(customers["age"])
        customers["age"] = customers["age"].fillna(customers["age"].median())
    if "city" in customers.columns:
        customers["city"] = customers["city"].replace({"nan": "Unknown", "": "Unknown"}).fillna("Unknown")
    customers = customers.drop_duplicates()

    if "price" in products.columns:
        products["price"] = to_number(products["price"])
        products = products[products["price"] > 0]
    products = products.drop_duplicates()

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders = orders.dropna(subset=["order_id", "customer_id", "order_date"])
    orders["order_month"] = orders["order_date"].dt.to_period("M").astype(str)
    orders["order_dayofweek"] = orders["order_date"].dt.dayofweek
    orders["order_day"] = orders["order_date"].dt.date
    if "order_status" in orders.columns:
        status_map = {
            "complete": "completed",
            "Complete": "completed",
            "COMPLETED": "completed",
            "완료": "completed",
            "cancel": "cancelled",
            "Cancel": "cancelled",
            "CANCELLED": "cancelled",
            "취소": "cancelled",
            "refund": "refunded",
            "Refund": "refunded",
            "REFUNDED": "refunded",
            "환불": "refunded",
        }
        orders["order_status"] = orders["order_status"].replace(status_map)
    orders = orders.drop_duplicates()

    order_items = order_items.dropna(subset=["order_id", "product_id", "quantity", "unit_price"])
    order_items["quantity"] = to_number(order_items["quantity"])
    order_items["unit_price"] = to_number(order_items["unit_price"])
    order_items = order_items.dropna(subset=["quantity", "unit_price"])
    order_items = order_items[(order_items["quantity"] > 0) & (order_items["unit_price"] > 0)]
    order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]
    order_items = order_items.drop_duplicates()

    processed = {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
    }
    processed_summary = pd.DataFrame(
        {
            "dataset": list(processed.keys()),
            "rows_processed": [df.shape[0] for df in processed.values()],
            "columns_processed": [df.shape[1] for df in processed.values()],
        }
    )
    comparison = raw_summary.merge(processed_summary, on="dataset", how="left")
    comparison["row_change"] = comparison["rows_processed"] - comparison["rows"]
    return processed, comparison


def save_processed_data(processed: dict[str, pd.DataFrame], base_dir: str | Path = ".") -> dict[str, Path]:
    """전처리 데이터를 data/processed에 저장합니다."""
    paths = get_project_paths(base_dir)
    outputs = {
        "customers": paths["processed_dir"] / "customers_clean.csv",
        "products": paths["processed_dir"] / "products_clean.csv",
        "orders": paths["processed_dir"] / "orders_clean.csv",
        "order_items": paths["processed_dir"] / "order_items_clean.csv",
    }
    for name, path in outputs.items():
        processed[name].to_csv(path, index=False, encoding="utf-8-sig")
    return outputs


def build_project_tables(processed: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """최종 프로젝트 핵심 EDA 집계표를 생성합니다."""
    customers = processed["customers"]
    products = processed["products"]
    orders = processed["orders"]
    order_items = processed["order_items"]

    sales_items = order_items.merge(products, on="product_id", how="left")
    order_sales = order_items.merge(orders, on="order_id", how="left")
    customer_sales_base = order_sales.merge(customers, on="customer_id", how="left")

    merge_validation = pd.DataFrame(
        {
            "check_item": [
                "sales_items 행 수",
                "order_sales 행 수",
                "customer_sales_base 행 수",
                "category 누락 수",
                "order_date 누락 수",
                "customer_id 누락 수",
            ],
            "value": [
                sales_items.shape[0],
                order_sales.shape[0],
                customer_sales_base.shape[0],
                int(sales_items["category"].isna().sum()) if "category" in sales_items.columns else None,
                int(order_sales["order_date"].isna().sum()) if "order_date" in order_sales.columns else None,
                int(customer_sales_base["customer_id"].isna().sum()) if "customer_id" in customer_sales_base.columns else None,
            ],
        }
    )

    category_sales = (
        sales_items.groupby("category", as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    category_sales["sales_ratio"] = (category_sales["total_sales"] / category_sales["total_sales"].sum() * 100).round(2)
    category_sales["avg_unit_revenue"] = (category_sales["total_sales"] / category_sales["total_quantity"]).round(0)

    monthly_sales = (
        order_sales.groupby("order_month", as_index=False)
        .agg(total_sales=("line_total", "sum"), order_count=("order_id", "nunique"))
        .sort_values("order_month")
    )
    monthly_sales["avg_order_value"] = (monthly_sales["total_sales"] / monthly_sales["order_count"]).round(0)
    monthly_sales["sales_change_ratio"] = (monthly_sales["total_sales"].pct_change() * 100).round(2)

    customer_group_cols = ["customer_id", "city"]
    if "name" in customer_sales_base.columns:
        customer_group_cols = ["customer_id", "name", "city"]
    customer_sales = (
        customer_sales_base.groupby(customer_group_cols, as_index=False)
        .agg(order_count=("order_id", "nunique"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    customer_sales["avg_order_value"] = (customer_sales["total_sales"] / customer_sales["order_count"]).round(0)
    customer_sales["customer_label"] = "Customer " + customer_sales["customer_id"].astype(str)

    product_group_cols = ["product_id", "category", "price"]
    if "product_name" in sales_items.columns:
        product_group_cols = ["product_id", "product_name", "category", "price"]
    product_sales = (
        sales_items.groupby(product_group_cols, as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    product_sales["avg_unit_revenue"] = (product_sales["total_sales"] / product_sales["total_quantity"]).round(0)

    return {
        "sales_items": sales_items,
        "order_sales": order_sales,
        "customer_sales_base": customer_sales_base,
        "merge_validation": merge_validation,
        "category_sales": category_sales,
        "monthly_sales": monthly_sales,
        "customer_sales": customer_sales,
        "product_sales": product_sales,
    }


def save_project_tables(tables: dict[str, pd.DataFrame], base_dir: str | Path = ".") -> dict[str, Path]:
    """최종 프로젝트 집계표를 reports 폴더에 저장합니다."""
    paths = get_project_paths(base_dir)
    file_map = {
        "merge_validation": "ch15_merge_validation.csv",
        "category_sales": "ch15_category_sales.csv",
        "monthly_sales": "ch15_monthly_sales.csv",
        "customer_sales": "ch15_customer_sales.csv",
        "product_sales": "ch15_product_sales.csv",
    }
    outputs = {}
    for key, filename in file_map.items():
        path = paths["report_dir"] / filename
        tables[key].to_csv(path, index=False, encoding="utf-8-sig")
        outputs[key] = path
    return outputs


def generate_project_figures(tables: dict[str, pd.DataFrame], base_dir: str | Path = ".") -> dict[str, Path]:
    """최종 프로젝트 주요 시각화 파일을 생성합니다."""
    paths = get_project_paths(base_dir)
    figure_dir = paths["figure_dir"]
    category_sales = tables["category_sales"]
    monthly_sales = tables["monthly_sales"]
    customer_sales = tables["customer_sales"]
    product_sales = tables["product_sales"]

    outputs = {}

    plt.figure(figsize=(10, 5))
    plt.bar(category_sales["category"], category_sales["total_sales"])
    plt.title("Category Sales")
    plt.xlabel("Category")
    plt.ylabel("Total Sales")
    plt.xticks(rotation=45)
    plt.tight_layout()
    outputs["category_sales"] = figure_dir / "ch15_category_sales.png"
    plt.savefig(outputs["category_sales"], dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(monthly_sales["order_month"], monthly_sales["total_sales"], marker="o")
    plt.title("Monthly Sales Trend")
    plt.xlabel("Order Month")
    plt.ylabel("Total Sales")
    plt.xticks(rotation=45)
    plt.tight_layout()
    outputs["monthly_sales"] = figure_dir / "ch15_monthly_sales.png"
    plt.savefig(outputs["monthly_sales"], dpi=150)
    plt.close()

    top_customers = customer_sales.head(10).copy().sort_values("total_sales")
    plt.figure(figsize=(10, 6))
    plt.barh(top_customers["customer_label"], top_customers["total_sales"])
    plt.title("Top 10 Customers by Sales")
    plt.xlabel("Total Sales")
    plt.ylabel("Customer")
    plt.tight_layout()
    outputs["top_customers"] = figure_dir / "ch15_top_customers.png"
    plt.savefig(outputs["top_customers"], dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.scatter(product_sales["price"], product_sales["total_quantity"], alpha=0.6)
    plt.title("Product Price and Quantity")
    plt.xlabel("Product Price")
    plt.ylabel("Total Quantity")
    plt.tight_layout()
    outputs["price_quantity"] = figure_dir / "ch15_price_quantity_scatter.png"
    plt.savefig(outputs["price_quantity"], dpi=150)
    plt.close()

    return outputs


def train_regression_models(processed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """주문별 총금액 예측 회귀 모델을 학습하고 비교표를 반환합니다."""
    customers = processed["customers"]
    orders = processed["orders"]
    order_items = processed["order_items"]

    order_features = (
        order_items.groupby("order_id", as_index=False)
        .agg(
            item_count=("product_id", "count"),
            total_quantity=("quantity", "sum"),
            avg_unit_price=("unit_price", "mean"),
            order_total=("line_total", "sum"),
        )
    )
    regression_data = (
        order_features.merge(
            orders[["order_id", "customer_id", "payment_method", "order_status", "order_month", "order_dayofweek"]],
            on="order_id",
            how="left",
        )
        .merge(customers[["customer_id", "gender", "age", "city"]], on="customer_id", how="left")
        .dropna()
    )

    features = [
        "item_count",
        "total_quantity",
        "avg_unit_price",
        "payment_method",
        "order_status",
        "order_dayofweek",
        "gender",
        "age",
        "city",
    ]
    categorical = ["payment_method", "order_status", "gender", "city"]
    X = regression_data[features]
    y = regression_data["order_total"]
    preprocessor = ColumnTransformer([("cat", make_one_hot_encoder(), categorical)], remainder="passthrough")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=200, random_state=42),
    }
    rows = []
    for model_name, model in models.items():
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        rows.append(
            {
                "model": model_name,
                "MAE": float(mean_absolute_error(y_test, y_pred)),
                "RMSE": float(np.sqrt(mse)),
                "R2": float(r2_score(y_test, y_pred)),
            }
        )
    return pd.DataFrame(rows).sort_values("MAE")


def train_classification_models(processed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """주문 취소 여부 예측 분류 모델을 학습하고 비교표를 반환합니다."""
    customers = processed["customers"]
    orders = processed["orders"]
    order_items = processed["order_items"]

    order_features = (
        order_items.groupby("order_id", as_index=False)
        .agg(item_count=("product_id", "count"), total_quantity=("quantity", "sum"), avg_unit_price=("unit_price", "mean"))
    )
    classification_data = (
        order_features.merge(
            orders[["order_id", "customer_id", "payment_method", "order_status", "order_dayofweek"]],
            on="order_id",
            how="left",
        )
        .merge(customers[["customer_id", "gender", "age", "city"]], on="customer_id", how="left")
        .dropna()
    )
    classification_data["is_cancelled"] = (classification_data["order_status"] == "cancelled").astype(int)

    features = ["item_count", "total_quantity", "avg_unit_price", "payment_method", "order_dayofweek", "gender", "age", "city"]
    categorical = ["payment_method", "gender", "city"]
    X = classification_data[features]
    y = classification_data["is_cancelled"]
    stratify = y if y.nunique() > 1 and y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify)
    preprocessor = ColumnTransformer([("cat", make_one_hot_encoder(), categorical)], remainder="passthrough")

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Random Forest Classifier": RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced"),
    }
    rows = []
    for model_name, model in models.items():
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        rows.append(
            {
                "model": model_name,
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision": float(precision_score(y_test, y_pred, zero_division=0)),
                "recall": float(recall_score(y_test, y_pred, zero_division=0)),
                "confusion_matrix": str(confusion_matrix(y_test, y_pred).tolist()),
            }
        )
    return pd.DataFrame(rows).sort_values("recall", ascending=False)


def create_sample_holidays(base_dir: str | Path = ".") -> Path:
    """예시 공휴일 데이터를 data/external/holidays.csv에 생성합니다."""
    paths = get_project_paths(base_dir)
    holiday_path = paths["external_dir"] / "holidays.csv"
    if holiday_path.exists():
        return holiday_path
    holidays_sample = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-02-16",
                "2026-02-17",
                "2026-02-18",
                "2026-03-01",
                "2026-05-05",
                "2026-06-06",
                "2026-08-15",
                "2026-10-03",
                "2026-10-09",
                "2026-12-25",
            ],
            "holiday_name": ["신정", "설날", "설날", "설날", "삼일절", "어린이날", "현충일", "광복절", "개천절", "한글날", "성탄절"],
            "is_holiday": [1] * 11,
        }
    )
    holidays_sample.to_csv(holiday_path, index=False, encoding="utf-8-sig")
    return holiday_path


def analyze_holiday_sales(tables: dict[str, pd.DataFrame], base_dir: str | Path = ".") -> dict[str, pd.DataFrame | Path]:
    """공휴일 예시 데이터를 일자별 매출과 연결해 비교합니다."""
    paths = get_project_paths(base_dir)
    holiday_path = create_sample_holidays(base_dir)
    holidays = pd.read_csv(holiday_path)
    holidays["date"] = pd.to_datetime(holidays["date"], errors="coerce")
    holidays["order_day"] = holidays["date"].dt.date

    holiday_summary = pd.DataFrame(
        [{"dataset": "holidays", "rows": holidays.shape[0], "columns": holidays.shape[1], "column_list": ", ".join(holidays.columns), "missing_values": int(holidays.isna().sum().sum())}]
    )

    order_sales = tables["order_sales"].copy()
    daily_sales = (
        order_sales.groupby("order_day", as_index=False)
        .agg(total_sales=("line_total", "sum"), order_count=("order_id", "nunique"))
    )
    daily_sales["order_day"] = pd.to_datetime(daily_sales["order_day"]).dt.date
    holiday_sales = daily_sales.merge(holidays[["order_day", "holiday_name", "is_holiday"]], on="order_day", how="left")
    holiday_sales["is_holiday"] = holiday_sales["is_holiday"].fillna(0).astype(int)
    holiday_sales["holiday_name"] = holiday_sales["holiday_name"].fillna("일반일")

    comparison = (
        holiday_sales.groupby("is_holiday", as_index=False)
        .agg(day_count=("order_day", "count"), avg_daily_sales=("total_sales", "mean"), avg_order_count=("order_count", "mean"), total_sales=("total_sales", "sum"))
    )
    comparison["day_type"] = comparison["is_holiday"].map({0: "일반일", 1: "공휴일"})
    comparison = comparison[["day_type", "day_count", "avg_daily_sales", "avg_order_count", "total_sales"]]

    holiday_summary.to_csv(paths["report_dir"] / "ch15_external_data_summary.csv", index=False, encoding="utf-8-sig")
    holiday_sales.to_csv(paths["report_dir"] / "ch15_holiday_sales.csv", index=False, encoding="utf-8-sig")
    comparison.to_csv(paths["report_dir"] / "ch15_holiday_sales_comparison.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(7, 5))
    plt.bar(comparison["day_type"], comparison["avg_daily_sales"])
    plt.title("Holiday vs Normal Day Average Sales")
    plt.xlabel("Day Type")
    plt.ylabel("Average Daily Sales")
    plt.tight_layout()
    figure_path = paths["figure_dir"] / "ch15_holiday_avg_sales.png"
    plt.savefig(figure_path, dpi=150)
    plt.close()

    external_text = f"""# Chapter 15 외부 데이터 통합 기록

## 1. 사용한 외부 데이터

- 파일: `{holiday_path}`
- 데이터 유형: 공휴일/캘린더 데이터
- 연결 기준: `order_day`

## 2. 분석 질문

공휴일 여부에 따라 평균 일매출과 평균 주문 수가 다르게 나타나는지 확인했습니다.

## 3. 주요 결과

```text
{comparison.to_string(index=False)}
```

## 4. 해석 시 주의할 점

공휴일 여부와 매출 차이가 함께 관찰되더라도 이를 원인 관계로 단정할 수 없습니다. 표본 수, 월별 시즌성, 프로모션, 특정 카테고리 이벤트 등 추가 변수를 함께 확인해야 합니다.
"""
    external_path = paths["report_dir"] / "ch15_external_data_integration.md"
    external_path.write_text(external_text, encoding="utf-8")

    return {
        "holiday_path": holiday_path,
        "holiday_summary": holiday_summary,
        "holiday_sales": holiday_sales,
        "holiday_sales_comparison": comparison,
        "figure_path": figure_path,
        "external_integration_path": external_path,
    }


def build_insight_cards(tables: dict[str, pd.DataFrame], regression: pd.DataFrame, holiday_comparison: pd.DataFrame) -> pd.DataFrame:
    """최종 보고서에 사용할 인사이트 카드 표를 생성합니다."""
    category_sales = tables["category_sales"]
    monthly_sales = tables["monthly_sales"]
    customer_sales = tables["customer_sales"]
    product_sales = tables["product_sales"]
    top_category = category_sales.iloc[0]
    top_month = monthly_sales.sort_values("total_sales", ascending=False).iloc[0]
    top_product = product_sales.iloc[0]
    best_regression = regression.iloc[0]
    return pd.DataFrame(
        {
            "insight_title": [
                "매출 기여도 높은 카테고리 확인",
                "월별 매출 집중 구간 확인",
                "구매 금액 상위 고객군 확인",
                "상품별 매출 기여도 확인",
                "머신러닝 모델의 예측 가능성 확인",
                "외부 데이터 기반 공휴일 매출 비교",
            ],
            "observation": [
                f"{top_category['category']} 카테고리의 매출 비중이 가장 높게 나타났습니다.",
                f"{top_month['order_month']}의 매출이 가장 높게 나타났습니다.",
                "구매 금액 상위 고객은 전체 매출에 크게 기여하는 고객군입니다.",
                f"{top_product.get('product_name', top_product['product_id'])} 상품의 매출이 가장 높게 나타났습니다.",
                f"{best_regression['model']} 모델의 회귀 평가 결과를 확인했습니다.",
                "공휴일 여부와 평균 일매출 차이를 비교했습니다.",
            ],
            "caution": [
                "매출이 높은 이유를 고객 선호로 단정할 수 없습니다.",
                "매출 증가 원인을 프로모션이나 계절성으로 단정할 수 없습니다.",
                "총 구매 금액만으로 충성 고객 여부를 판단할 수 없습니다.",
                "상품 매출이 높은 이유는 단가 또는 판매 수량을 함께 확인해야 합니다.",
                "모델 성능은 현재 데이터와 입력 변수 범위에 한정됩니다.",
                "공휴일이 매출 차이의 원인이라고 단정할 수 없습니다.",
            ],
            "next_step": [
                "판매 수량과 평균 판매 단가를 함께 분석합니다.",
                "주문 수와 평균 주문 금액 변화를 함께 확인합니다.",
                "반복 구매 여부와 최근 구매일을 추가로 확인합니다.",
                "상품별 판매 수량과 가격대를 함께 분석합니다.",
                "외부 데이터와 추가 변수를 결합해 모델 성능을 개선합니다.",
                "월별 시즌성, 프로모션, 카테고리 이벤트 데이터를 추가로 확인합니다.",
            ],
        }
    )


def build_llm_usage_log() -> pd.DataFrame:
    """기말 프로젝트 LLM 활용 및 검증 기록 템플릿을 생성합니다."""
    return pd.DataFrame(
        {
            "step": ["분석 질문 검토", "pandas 코드 생성", "머신러닝 코드 검토", "외부 데이터 연결 검토", "오류 해결", "결과 해석", "보고서 문장 보완", "자동화 설계"],
            "input_summary": [
                "데이터셋 이름과 컬럼명",
                "분석 목적과 데이터 구조",
                "예측 대상, 입력값 후보, 평가 지표",
                "외부 데이터 컬럼과 연결 키",
                "오류 메시지와 코드 일부",
                "집계 결과표와 모델 평가 결과",
                "보고서 초안",
                "보고서 파일과 반복 실행 흐름",
            ],
            "validation_point": [
                "현재 데이터로 답할 수 있는 질문인지 확인",
                "컬럼명과 병합 기준 검증",
                "데이터 누수와 평가 지표 검증",
                "외부 데이터 출처와 병합 전후 행 수 검증",
                "수정 코드 실행 여부 확인",
                "원인 단정 여부 검토",
                "데이터에 없는 표현 수정",
                "실제 도구에서 구현 가능한지 확인",
            ],
            "used_in_final": ["수정 후 사용", "검증 후 사용", "검증 후 사용", "검증 후 사용", "검증 후 사용", "수정 후 사용", "수정 후 사용", "설계 참고"],
        }
    )


def build_automation_plan() -> str:
    """최종 프로젝트 자동화 설계서 Markdown 문자열을 생성합니다."""
    return """# Chapter 15 자동화 설계서

## 1. 자동화 목적

최종 프로젝트의 분석 과정을 반복 실행할 수 있도록 전처리, 분석, 시각화, 외부 데이터 통합, 보고서 생성, 알림 발송 흐름을 자동화합니다.

## 2. 자동화 대상 작업

1. 원본 데이터 수집 또는 업로드 확인
2. 외부 데이터 수집 또는 최신 파일 확인
3. 데이터 전처리
4. EDA 지표 계산
5. 외부 데이터 연결 분석
6. 회귀 또는 분류 모델 실행
7. 그래프 생성
8. Markdown 보고서 생성
9. 결과 파일 검증
10. 보고서 저장 및 알림 발송

## 3. 도구 구성 예시

- Python: 분석 코드 실행
- Airflow: Task 순서와 실행 로그 관리
- Google Drive: 보고서 저장
- Make 또는 n8n: 보고서 생성 후 Slack 또는 이메일 알림

## 4. 검증 항목

- 원본 CSV 파일 존재 여부
- 외부 데이터 파일 존재 여부
- 전처리 결과 파일 생성 여부
- 분석 결과 CSV 행 수 확인
- 그래프 파일 생성 여부
- 최종 보고서 생성 여부
- LLM 활용 기록 존재 여부
- 외부 데이터 출처와 사용 조건 기록 여부

## 5. 주의할 점

자동화는 분석 결과를 자동으로 옳게 만들어 주지 않습니다. 실행 성공, 산출물 생성, 분석 품질을 따로 확인해야 합니다.
"""


def build_final_report(
    dataset_summary: pd.DataFrame,
    preprocessing_comparison: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
    regression: pd.DataFrame,
    classification: pd.DataFrame,
    holiday_comparison: pd.DataFrame,
    insight_cards: pd.DataFrame,
) -> str:
    """최종 보고서 Markdown 문자열을 생성합니다."""
    category_sales = tables["category_sales"]
    monthly_sales = tables["monthly_sales"]
    customer_sales = tables["customer_sales"]
    product_sales = tables["product_sales"]
    return f"""# 온라인 쇼핑몰 데이터 분석 최종 보고서

## 1. 프로젝트 개요

이 프로젝트는 온라인 쇼핑몰 고객, 상품, 주문, 주문 상세 데이터를 활용해 매출 현황과 고객 구매 패턴을 분석하고, 간단한 머신러닝 모델과 외부 데이터 통합 분석을 통해 향후 확장 가능성을 검토하는 것을 목적으로 합니다.

## 2. 데이터 개요

```text
{dataset_summary.to_string(index=False)}
```

## 3. 전처리 기준과 결과

```text
{preprocessing_comparison.to_string(index=False)}
```

## 4. EDA 주요 결과

### 4.1 카테고리별 매출

```text
{category_sales.head(10).to_string(index=False)}
```

### 4.2 월별 매출

```text
{monthly_sales.head(12).to_string(index=False)}
```

### 4.3 구매 금액 상위 고객

```text
{customer_sales.head(10).to_string(index=False)}
```

### 4.4 상품별 매출

```text
{product_sales.head(10).to_string(index=False)}
```

## 5. 머신러닝 모델 결과

### 5.1 회귀 모델: 주문별 총금액 예측

```text
{regression.to_string(index=False)}
```

### 5.2 분류 모델: 주문 취소 여부 예측

```text
{classification.to_string(index=False)}
```

## 6. 외부 데이터 통합 분석

공휴일 예시 데이터를 일자별 매출 데이터와 연결해 공휴일 여부별 평균 일매출과 평균 주문 수를 비교했습니다.

```text
{holiday_comparison.to_string(index=False)}
```

이 결과는 공휴일 여부와 매출 차이를 함께 보여 줄 뿐이며, 공휴일이 매출 변화의 원인이라고 단정할 수 없습니다.

## 7. 인사이트 카드

```text
{insight_cards.to_string(index=False)}
```

## 8. LLM 활용 및 검증 내역

LLM은 분석 질문 보완, 코드 초안 작성, 머신러닝 코드 검토, 외부 데이터 연결 검토, 오류 해결, 해석 문장 보완, 자동화 설계에 활용했습니다. 단, 최종 산출물에는 실제 데이터 구조와 실행 결과로 검증한 내용만 반영했습니다.

## 9. 자동화 설계

반복 실행이 필요한 경우 Python 스크립트와 Airflow로 전처리, 분석, 시각화, 외부 데이터 통합, 보고서 생성, 결과 검증을 자동화할 수 있습니다. Make 또는 n8n은 생성된 보고서를 Slack, Gmail, Drive 등 외부 서비스로 전달하는 데 활용할 수 있습니다.

## 10. 결론과 한계

- 현재 데이터로 매출 현황, 카테고리별 기여도, 월별 흐름, 고객별 구매 금액, 상품별 매출을 확인했습니다.
- 머신러닝 모델은 예측 가능성을 확인하는 수준이며, 운영 적용 전 추가 데이터와 검증이 필요합니다.
- 외부 데이터 통합은 공휴일 예시 데이터로 수행했으며, 실제 원인 분석에는 날씨, 프로모션, 재고, 광고, 검색 트렌드 등 추가 데이터가 필요합니다.
- LLM은 분석 보조 도구로 유용하지만, 코드와 해석은 사람이 검증해야 합니다.

## 11. 다음 단계

1. 더 긴 기간의 주문 데이터를 확보합니다.
2. 프로모션, 광고, 재고, 반품, 방문 로그 데이터를 추가합니다.
3. 외부 데이터의 출처와 업데이트 주기를 관리합니다.
4. 모델 평가를 반복하고 데이터 누수를 점검합니다.
5. Airflow와 Make/n8n을 활용한 반복 보고 자동화 구조를 구체화합니다.
"""


def run_final_project(base_dir: str | Path = ".") -> dict[str, object]:
    """15장 기말 종합 프로젝트 전체 파이프라인을 실행합니다."""
    paths = get_project_paths(base_dir)
    raw_data = load_raw_data(base_dir)
    dataset_summary = build_dataset_summary(raw_data)
    processed, preprocessing_comparison = preprocess_project_data(raw_data)
    save_processed_data(processed, base_dir)
    tables = build_project_tables(processed)
    save_project_tables(tables, base_dir)
    figures = generate_project_figures(tables, base_dir)

    regression = train_regression_models(processed)
    classification = train_classification_models(processed)
    regression_path = paths["report_dir"] / "ch15_regression_model_comparison.csv"
    classification_path = paths["report_dir"] / "ch15_classification_model_comparison.csv"
    regression.to_csv(regression_path, index=False, encoding="utf-8-sig")
    classification.to_csv(classification_path, index=False, encoding="utf-8-sig")

    holiday_result = analyze_holiday_sales(tables, base_dir)
    insight_cards = build_insight_cards(tables, regression, holiday_result["holiday_sales_comparison"])
    insight_cards_path = paths["report_dir"] / "ch15_insight_cards.csv"
    insight_cards.to_csv(insight_cards_path, index=False, encoding="utf-8-sig")

    llm_usage_log = build_llm_usage_log()
    llm_usage_log_path = paths["report_dir"] / "ch15_llm_usage_log.csv"
    llm_usage_log.to_csv(llm_usage_log_path, index=False, encoding="utf-8-sig")
    llm_usage_text = f"""# Chapter 15 LLM 활용 및 검증 기록

## 1. LLM 활용 목적

기말 종합 프로젝트에서 LLM은 분석 질문 보완, pandas 코드 초안 작성, 머신러닝 코드 검토, 외부 데이터 연결 검토, 오류 해결, 해석 문장 작성, 자동화 설계 보조 도구로 사용했습니다.

## 2. LLM 활용 기록

```text
{llm_usage_log.to_string(index=False)}
```

## 3. 검증 원칙

- 원본 개인정보나 개별 주문 데이터를 LLM에 입력하지 않았습니다.
- 컬럼명, 데이터 구조, 집계 결과 중심으로 질문했습니다.
- LLM이 생성한 코드는 실제 데이터로 실행해 검증했습니다.
- 머신러닝 코드에서는 데이터 누수 여부를 확인했습니다.
- 외부 데이터 연결에서는 출처, 연결 키, 병합 전후 행 수를 확인했습니다.
- LLM이 작성한 해석 문장은 원인 단정 여부를 검토했습니다.
- 최종 보고서에는 검증된 코드와 문장만 반영했습니다.
"""
    llm_usage_md_path = paths["report_dir"] / "ch15_llm_usage_log.md"
    llm_usage_md_path.write_text(llm_usage_text, encoding="utf-8")

    automation_plan = build_automation_plan()
    automation_plan_path = paths["report_dir"] / "ch15_automation_plan.md"
    automation_plan_path.write_text(automation_plan, encoding="utf-8")

    final_report = build_final_report(
        dataset_summary=dataset_summary,
        preprocessing_comparison=preprocessing_comparison,
        tables=tables,
        regression=regression,
        classification=classification,
        holiday_comparison=holiday_result["holiday_sales_comparison"],
        insight_cards=insight_cards,
    )
    final_report_path = paths["report_dir"] / "ch15_final_report.md"
    final_report_path.write_text(final_report, encoding="utf-8")

    dataset_summary_path = paths["report_dir"] / "ch15_dataset_summary.csv"
    preprocessing_comparison_path = paths["report_dir"] / "ch15_preprocessing_comparison.csv"
    dataset_summary.to_csv(dataset_summary_path, index=False, encoding="utf-8-sig")
    preprocessing_comparison.to_csv(preprocessing_comparison_path, index=False, encoding="utf-8-sig")

    deliverables = pd.DataFrame(
        [
            {"deliverable": "dataset_summary", "path": str(dataset_summary_path)},
            {"deliverable": "preprocessing_comparison", "path": str(preprocessing_comparison_path)},
            {"deliverable": "category_sales", "path": str(paths["report_dir"] / "ch15_category_sales.csv")},
            {"deliverable": "monthly_sales", "path": str(paths["report_dir"] / "ch15_monthly_sales.csv")},
            {"deliverable": "customer_sales", "path": str(paths["report_dir"] / "ch15_customer_sales.csv")},
            {"deliverable": "product_sales", "path": str(paths["report_dir"] / "ch15_product_sales.csv")},
            {"deliverable": "regression_model", "path": str(regression_path)},
            {"deliverable": "classification_model", "path": str(classification_path)},
            {"deliverable": "external_integration", "path": str(holiday_result["external_integration_path"])},
            {"deliverable": "insight_cards", "path": str(insight_cards_path)},
            {"deliverable": "llm_usage_log", "path": str(llm_usage_md_path)},
            {"deliverable": "automation_plan", "path": str(automation_plan_path)},
            {"deliverable": "final_report", "path": str(final_report_path)},
        ]
    )
    deliverables_path = paths["report_dir"] / "ch15_project_deliverables.csv"
    deliverables.to_csv(deliverables_path, index=False, encoding="utf-8-sig")

    return {
        "paths": paths,
        "raw_data": raw_data,
        "processed": processed,
        "dataset_summary": dataset_summary,
        "preprocessing_comparison": preprocessing_comparison,
        "tables": tables,
        "figures": figures,
        "regression": regression,
        "classification": classification,
        "holiday_result": holiday_result,
        "insight_cards": insight_cards,
        "llm_usage_log": llm_usage_log,
        "automation_plan_path": automation_plan_path,
        "final_report_path": final_report_path,
        "deliverables": deliverables,
        "deliverables_path": deliverables_path,
    }
