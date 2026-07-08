"""Chapter 6 EDA 공통 함수 모음.

6장 노트북과 실행 스크립트에서 함께 사용할 탐색적 데이터 분석 함수입니다.
EDA의 핵심 흐름인 질문 정리, 기본 분포 확인, 매출 집계, 결과 저장, 요약 보고서 생성을 함수로 제공합니다.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROCESSED_FILENAMES = {
    "customers": "customers_clean.csv",
    "products": "products_clean.csv",
    "orders": "orders_clean.csv",
    "order_items": "order_items_clean.csv",
}


def load_processed_sales_data(data_dir: str | Path = "data/processed") -> dict[str, pd.DataFrame]:
    """5장에서 저장한 전처리 데이터 4종을 불러옵니다."""
    base_dir = Path(data_dir)
    data: dict[str, pd.DataFrame] = {}

    for name, filename in PROCESSED_FILENAMES.items():
        path = base_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"전처리 파일을 찾을 수 없습니다: {path}\n"
                "먼저 `python scripts/preprocess_data.py`를 실행하세요."
            )
        data[name] = pd.read_csv(path)

    return data


def prepare_eda_data(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """EDA 전에 날짜형과 line_total 컬럼을 점검해 보정합니다."""
    prepared = {name: df.copy() for name, df in data.items()}

    customers = prepared["customers"]
    orders = prepared["orders"]
    order_items = prepared["order_items"]

    if "signup_date" in customers.columns:
        customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="coerce")

    if "order_date" in orders.columns:
        orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
        if "order_month" not in orders.columns:
            orders["order_month"] = orders["order_date"].dt.to_period("M").astype(str)
        if "order_dayofweek" not in orders.columns:
            orders["order_dayofweek"] = orders["order_date"].dt.day_name()

    if "line_total" not in order_items.columns and {"quantity", "unit_price"}.issubset(order_items.columns):
        order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]

    return prepared


def make_eda_questions() -> pd.DataFrame:
    """6장 기본 EDA 질문과 지표를 표로 반환합니다."""
    return pd.DataFrame(
        {
            "analysis_area": ["고객", "상품", "주문", "매출", "시간", "고객 가치"],
            "question": [
                "고객은 어떤 지역과 연령대에 분포하는가?",
                "어떤 카테고리의 상품이 많은가?",
                "주문 상태와 결제수단 분포는 어떤가?",
                "카테고리별 매출은 어떻게 다른가?",
                "월별 매출과 주문 수는 어떻게 변하는가?",
                "구매 금액이 높은 고객은 누구인가?",
            ],
            "metric": [
                "고객 수, 평균 나이",
                "카테고리별 상품 수",
                "주문 수, 비율",
                "총매출, 매출 비중",
                "월별 매출, 월별 주문 수",
                "고객별 총매출, 주문 횟수",
            ],
            "required_data": [
                "customers",
                "products",
                "orders",
                "order_items, products",
                "orders, order_items",
                "customers, orders, order_items",
            ],
        }
    )


def customer_city_summary(customers: pd.DataFrame) -> pd.DataFrame:
    """도시별 고객 수를 계산합니다."""
    result = customers["city"].value_counts(dropna=False).reset_index()
    result.columns = ["city", "customer_count"]
    result["customer_ratio"] = (result["customer_count"] / result["customer_count"].sum() * 100).round(2)
    return result


def customer_gender_summary(customers: pd.DataFrame) -> pd.DataFrame:
    """성별 고객 수를 계산합니다."""
    result = customers["gender"].value_counts(dropna=False).reset_index()
    result.columns = ["gender", "customer_count"]
    result["customer_ratio"] = (result["customer_count"] / result["customer_count"].sum() * 100).round(2)
    return result


def product_category_summary(products: pd.DataFrame) -> pd.DataFrame:
    """카테고리별 상품 수를 계산합니다."""
    result = products["category"].value_counts(dropna=False).reset_index()
    result.columns = ["category", "product_count"]
    result["product_ratio"] = (result["product_count"] / result["product_count"].sum() * 100).round(2)
    return result


def category_price_summary(products: pd.DataFrame) -> pd.DataFrame:
    """카테고리별 상품 가격 요약 통계를 계산합니다."""
    return (
        products.groupby("category", as_index=False)
        .agg(
            product_count=("product_id", "count"),
            avg_price=("price", "mean"),
            min_price=("price", "min"),
            max_price=("price", "max"),
        )
        .assign(avg_price=lambda df: df["avg_price"].round(0))
        .sort_values("avg_price", ascending=False)
    )


def order_status_summary(orders: pd.DataFrame) -> pd.DataFrame:
    """주문 상태별 주문 수와 비율을 계산합니다."""
    result = orders["order_status"].value_counts(dropna=False).reset_index()
    result.columns = ["order_status", "order_count"]
    result["order_ratio"] = (result["order_count"] / result["order_count"].sum() * 100).round(2)
    return result


def payment_method_summary(orders: pd.DataFrame) -> pd.DataFrame:
    """결제수단별 주문 수와 비율을 계산합니다."""
    result = orders["payment_method"].value_counts(dropna=False).reset_index()
    result.columns = ["payment_method", "order_count"]
    result["order_ratio"] = (result["order_count"] / result["order_count"].sum() * 100).round(2)
    return result


def build_sales_items(products: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    """주문 상세와 상품 데이터를 연결해 카테고리 매출 분석용 데이터를 만듭니다."""
    items = order_items.copy()
    if "line_total" not in items.columns and {"quantity", "unit_price"}.issubset(items.columns):
        items["line_total"] = items["quantity"] * items["unit_price"]
    return items.merge(products, on="product_id", how="left")


def category_sales_summary(products: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    """카테고리별 판매 수량, 매출, 매출 비중을 계산합니다."""
    sales_items = build_sales_items(products, order_items)
    result = (
        sales_items.groupby("category", as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    result["sales_ratio"] = (result["total_sales"] / result["total_sales"].sum() * 100).round(2)
    return result


def monthly_sales_summary(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    """월별 매출, 주문 수, 평균 주문 금액을 계산합니다."""
    items = order_items.copy()
    if "line_total" not in items.columns and {"quantity", "unit_price"}.issubset(items.columns):
        items["line_total"] = items["quantity"] * items["unit_price"]

    merged = items.merge(orders, on="order_id", how="left")
    merged["order_date"] = pd.to_datetime(merged["order_date"], errors="coerce")
    merged["order_month"] = merged["order_date"].dt.to_period("M").astype(str)

    result = (
        merged.groupby("order_month", as_index=False)
        .agg(total_sales=("line_total", "sum"), order_count=("order_id", "nunique"))
        .sort_values("order_month")
    )
    result["avg_order_value"] = (result["total_sales"] / result["order_count"]).round(0)
    return result


def customer_sales_summary(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """고객별 구매 금액, 주문 횟수, 평균 주문 금액을 계산합니다."""
    items = order_items.copy()
    if "line_total" not in items.columns and {"quantity", "unit_price"}.issubset(items.columns):
        items["line_total"] = items["quantity"] * items["unit_price"]

    order_sales = items.merge(orders, on="order_id", how="left")
    base = order_sales.merge(customers, on="customer_id", how="left")

    group_cols = ["customer_id", "city"]
    if "name" in base.columns:
        group_cols = ["customer_id", "name", "city"]

    result = (
        base.groupby(group_cols, as_index=False)
        .agg(order_count=("order_id", "nunique"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    result["avg_order_value"] = (result["total_sales"] / result["order_count"]).round(0)
    return result


def eda_result_summary() -> pd.DataFrame:
    """EDA 결과를 다음 질문으로 연결하는 요약표를 반환합니다."""
    return pd.DataFrame(
        {
            "question": [
                "고객은 어느 도시에 많이 분포하는가?",
                "어떤 카테고리의 상품이 많은가?",
                "카테고리별 매출은 어떻게 다른가?",
                "월별 매출과 주문 수는 어떻게 변하는가?",
                "구매 금액이 높은 고객은 누구인가?",
            ],
            "result_table": [
                "customer_city",
                "product_category",
                "category_sales",
                "monthly_sales",
                "customer_sales",
            ],
            "next_question": [
                "도시별 구매 금액도 차이가 있는가?",
                "상품 수가 많은 카테고리가 매출도 높은가?",
                "매출 차이가 수량 때문인가 단가 때문인가?",
                "특정 월의 매출 변화는 어떤 카테고리 때문인가?",
                "고액 구매 고객은 반복 구매 고객인가?",
            ],
        }
    )


def run_basic_eda(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """6장 기본 EDA 결과표를 한 번에 생성합니다."""
    prepared = prepare_eda_data(data)
    customers = prepared["customers"]
    products = prepared["products"]
    orders = prepared["orders"]
    order_items = prepared["order_items"]

    return {
        "questions": make_eda_questions(),
        "customer_city": customer_city_summary(customers),
        "customer_gender": customer_gender_summary(customers),
        "product_category": product_category_summary(products),
        "category_price": category_price_summary(products),
        "order_status": order_status_summary(orders),
        "payment_method": payment_method_summary(orders),
        "category_sales": category_sales_summary(products, order_items),
        "monthly_sales": monthly_sales_summary(orders, order_items),
        "customer_sales": customer_sales_summary(customers, orders, order_items),
        "eda_result_summary": eda_result_summary(),
    }


def save_eda_outputs(
    results: dict[str, pd.DataFrame],
    output_dir: str | Path = "reports",
    encoding: str = "utf-8-sig",
) -> list[Path]:
    """EDA 결과표를 CSV 파일로 저장합니다."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_map = {
        "category_sales": "ch06_category_sales.csv",
        "monthly_sales": "ch06_monthly_sales.csv",
        "customer_sales": "ch06_customer_sales.csv",
        "eda_result_summary": "ch06_eda_questions.csv",
        "customer_city": "ch06_customer_city.csv",
        "product_category": "ch06_product_category.csv",
    }

    saved_paths: list[Path] = []
    for key, filename in file_map.items():
        path = output_path / filename
        results[key].to_csv(path, index=False, encoding=encoding)
        saved_paths.append(path)

    return saved_paths


def build_eda_report(results: dict[str, pd.DataFrame]) -> str:
    """EDA 결과를 Markdown 보고서 문자열로 생성합니다."""
    questions = results["questions"]
    category_sales = results["category_sales"]
    monthly_sales = results["monthly_sales"]
    customer_sales = results["customer_sales"]
    summary = results["eda_result_summary"]

    return f"""# Chapter 6 EDA 요약 보고서

## 1. 분석 목적

전처리된 온라인 쇼핑몰 데이터를 사용해 고객, 상품, 주문, 매출 관점의 기본 현황을 탐색했습니다.

## 2. 주요 분석 질문

```text
{questions.to_string(index=False)}
```

## 3. 카테고리별 매출 요약

```text
{category_sales.head(10).to_string(index=False)}
```

## 4. 월별 매출 요약

```text
{monthly_sales.to_string(index=False)}
```

## 5. 고객별 구매 금액 상위 10명

```text
{customer_sales.head(10).to_string(index=False)}
```

## 6. 추가 분석 질문

```text
{summary.to_string(index=False)}
```

## 7. 해석 시 주의사항

- EDA 결과는 최종 결론이 아니라 추가 분석을 위한 관찰 결과입니다.
- 매출이 높은 카테고리가 반드시 선호도가 높은 카테고리라는 뜻은 아닙니다.
- 월별 매출 변화의 원인을 설명하려면 프로모션, 계절성, 신규 상품 등의 추가 정보가 필요합니다.
- 고객별 구매 금액은 주문 횟수와 평균 주문 금액을 함께 해석해야 합니다.
"""
