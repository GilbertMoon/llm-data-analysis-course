"""Chapter 5 데이터 전처리 공통 함수 모음.

이 모듈은 5장 노트북과 스크립트에서 함께 사용할 수 있는 전처리 함수를 제공합니다.
원본 DataFrame을 직접 수정하지 않고 항상 복사본을 반환하도록 작성했습니다.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


STATUS_MAP = {
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


def check_missing_values(df: pd.DataFrame) -> pd.Series:
    """각 컬럼의 결측치 개수를 확인합니다."""
    return df.isna().sum()


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """중복 행을 제거한 새 DataFrame을 반환합니다."""
    return df.drop_duplicates().reset_index(drop=True)


def convert_date_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """문자열 날짜 컬럼을 datetime 형식으로 변환합니다."""
    result = df.copy()
    result[column] = pd.to_datetime(result[column], errors="coerce")
    return result


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼별 결측치 개수와 비율을 반환합니다."""
    summary = pd.DataFrame(
        {
            "missing_count": df.isna().sum(),
            "missing_ratio": (df.isna().mean() * 100).round(2),
        }
    )
    return summary.sort_values("missing_count", ascending=False)


def shape_summary(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """여러 DataFrame의 행/열 개수를 요약합니다."""
    rows = []
    for name, df in data.items():
        rows.append({"dataset": name, "rows": df.shape[0], "columns": df.shape[1]})
    return pd.DataFrame(rows)


def compare_shapes(
    raw_data: dict[str, pd.DataFrame],
    processed_data: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """전처리 전후 데이터 크기를 비교합니다."""
    raw_shapes = shape_summary(raw_data).rename(
        columns={"rows": "rows_raw", "columns": "columns_raw"}
    )
    processed_shapes = shape_summary(processed_data).rename(
        columns={"rows": "rows_processed", "columns": "columns_processed"}
    )
    return raw_shapes.merge(processed_shapes, on="dataset", how="outer")


def duplicate_summary(
    data: dict[str, pd.DataFrame],
    key_columns: dict[str, str] | None = None,
) -> pd.DataFrame:
    """전체 행 중복과 주요 키 컬럼 중복을 요약합니다."""
    key_columns = key_columns or {}
    rows = []

    for name, df in data.items():
        key_col = key_columns.get(name)
        key_duplicate_count = None
        if key_col and key_col in df.columns:
            key_duplicate_count = int(df[key_col].duplicated().sum())

        rows.append(
            {
                "dataset": name,
                "row_duplicate_count": int(df.duplicated().sum()),
                "key_column": key_col,
                "key_duplicate_count": key_duplicate_count,
            }
        )

    return pd.DataFrame(rows)


def strip_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """문자열 컬럼의 앞뒤 공백을 제거합니다.

    결측치를 문자열 'nan'으로 바꾸지 않기 위해 결측치는 그대로 유지합니다.
    """
    result = df.copy()
    string_columns = result.select_dtypes(include="object").columns

    for col in string_columns:
        result[col] = result[col].where(
            result[col].isna(),
            result[col].astype(str).str.strip(),
        )

    return result


def to_number(series: pd.Series) -> pd.Series:
    """쉼표가 포함된 문자열 숫자를 숫자형으로 변환합니다."""
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )


def normalize_order_status(series: pd.Series) -> pd.Series:
    """주문 상태값의 대표 표기를 통일합니다."""
    return series.replace(STATUS_MAP)


def preprocess_customers(df: pd.DataFrame) -> pd.DataFrame:
    """고객 데이터 전처리.

    처리 내용:
    - 문자열 앞뒤 공백 제거
    - age 숫자형 변환 및 중앙값 대체
    - city 결측치 Unknown 처리
    - signup_date 날짜형 변환
    - 완전 중복 행 제거
    """
    result = strip_string_columns(df)

    if "age" in result.columns:
        result["age"] = pd.to_numeric(result["age"], errors="coerce")
        if result["age"].notna().any():
            result["age"] = result["age"].fillna(result["age"].median())

    if "city" in result.columns:
        result["city"] = result["city"].fillna("Unknown")

    if "signup_date" in result.columns:
        result["signup_date"] = pd.to_datetime(result["signup_date"], errors="coerce")

    return result.drop_duplicates()


def preprocess_products(df: pd.DataFrame) -> pd.DataFrame:
    """상품 데이터 전처리.

    처리 내용:
    - 문자열 앞뒤 공백 제거
    - price 숫자형 변환
    - price가 0 이하인 행 제외
    - 완전 중복 행 제거
    """
    result = strip_string_columns(df)

    if "price" in result.columns:
        result["price"] = to_number(result["price"])
        result = result[result["price"] > 0]

    return result.drop_duplicates()


def preprocess_orders(df: pd.DataFrame) -> pd.DataFrame:
    """주문 데이터 전처리.

    처리 내용:
    - 문자열 앞뒤 공백 제거
    - order_status 대표 표기 통일
    - order_date 날짜형 변환
    - order_month, order_dayofweek 파생 컬럼 생성
    - 완전 중복 행 제거
    """
    result = strip_string_columns(df)

    if "order_status" in result.columns:
        result["order_status"] = normalize_order_status(result["order_status"])

    if "order_date" in result.columns:
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result["order_month"] = result["order_date"].dt.to_period("M").astype(str)
        result["order_dayofweek"] = result["order_date"].dt.day_name()

    return result.drop_duplicates()


def preprocess_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """주문 상세 데이터 전처리.

    처리 내용:
    - 문자열 앞뒤 공백 제거
    - quantity, unit_price 숫자형 변환
    - quantity와 unit_price가 0 이하인 행 제외
    - line_total 파생 컬럼 생성
    - 완전 중복 행 제거
    """
    result = strip_string_columns(df)

    if "quantity" in result.columns:
        result["quantity"] = to_number(result["quantity"])
        result = result[result["quantity"] > 0]

    if "unit_price" in result.columns:
        result["unit_price"] = to_number(result["unit_price"])
        result = result[result["unit_price"] > 0]

    if {"quantity", "unit_price"}.issubset(result.columns):
        result["line_total"] = result["quantity"] * result["unit_price"]

    return result.drop_duplicates()


def preprocess_sales_data(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """쇼핑몰 실습 데이터 4종을 한 번에 전처리합니다."""
    return {
        "customers": preprocess_customers(data["customers"]),
        "products": preprocess_products(data["products"]),
        "orders": preprocess_orders(data["orders"]),
        "order_items": preprocess_order_items(data["order_items"]),
    }


def validate_relationships(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """전처리 후 파일 간 키 관계가 유지되는지 확인합니다."""
    customers = data["customers"]
    products = data["products"]
    orders = data["orders"]
    order_items = data["order_items"]

    checks = []

    if {"customer_id"}.issubset(customers.columns) and {"customer_id"}.issubset(orders.columns):
        invalid_customers = orders[~orders["customer_id"].isin(customers["customer_id"])]
        checks.append(
            {
                "check": "orders.customer_id exists in customers.customer_id",
                "invalid_count": len(invalid_customers),
            }
        )

    if {"order_id"}.issubset(orders.columns) and {"order_id"}.issubset(order_items.columns):
        invalid_orders = order_items[~order_items["order_id"].isin(orders["order_id"])]
        checks.append(
            {
                "check": "order_items.order_id exists in orders.order_id",
                "invalid_count": len(invalid_orders),
            }
        )

    if {"product_id"}.issubset(products.columns) and {"product_id"}.issubset(order_items.columns):
        invalid_products = order_items[
            ~order_items["product_id"].isin(products["product_id"])
        ]
        checks.append(
            {
                "check": "order_items.product_id exists in products.product_id",
                "invalid_count": len(invalid_products),
            }
        )

    return pd.DataFrame(checks)


def save_processed_data(
    data: dict[str, pd.DataFrame],
    output_dir: str | Path = "data/processed",
    encoding: str = "utf-8-sig",
) -> list[Path]:
    """전처리 결과를 CSV 파일로 저장하고 저장 경로 목록을 반환합니다."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_map = {
        "customers": "customers_clean.csv",
        "products": "products_clean.csv",
        "orders": "orders_clean.csv",
        "order_items": "order_items_clean.csv",
    }

    saved_paths: list[Path] = []
    for name, filename in file_map.items():
        path = output_path / filename
        data[name].to_csv(path, index=False, encoding=encoding)
        saved_paths.append(path)

    return saved_paths


def build_preprocessing_report(
    raw_data: dict[str, pd.DataFrame],
    processed_data: dict[str, pd.DataFrame],
    relationship_checks: pd.DataFrame,
) -> str:
    """전처리 결과 요약 Markdown 문자열을 생성합니다."""
    comparison = compare_shapes(raw_data, processed_data)
    duplicate_checks = duplicate_summary(
        processed_data,
        key_columns={
            "customers": "customer_id",
            "products": "product_id",
            "orders": "order_id",
            "order_items": "order_item_id",
        },
    )

    return f"""# Chapter 5 데이터 전처리 요약

## 전처리 결과 파일

- customers_clean.csv
- products_clean.csv
- orders_clean.csv
- order_items_clean.csv

## 전처리 전후 데이터 크기

```text
{comparison.to_string(index=False)}
```

## 중복 점검 결과

```text
{duplicate_checks.to_string(index=False)}
```

## 파일 간 관계 점검 결과

```text
{relationship_checks.to_string(index=False)}
```

## 주요 처리 내용

- 원본 데이터는 직접 수정하지 않고 복사본을 사용했습니다.
- 문자열 컬럼의 앞뒤 공백을 제거했습니다.
- 고객 나이 결측치는 중앙값으로 대체했습니다.
- 고객 도시 결측치는 Unknown으로 처리했습니다.
- 주문 상태값 표기를 completed, cancelled, refunded 중심으로 통일했습니다.
- 날짜 컬럼을 날짜형으로 변환하고 주문 월/요일 파생 컬럼을 만들었습니다.
- 가격, 수량, 단가를 숫자형으로 변환했습니다.
- 0 이하 가격, 수량, 단가는 정상 분석 대상에서 제외했습니다.
- 주문 상세 금액 line_total 파생 컬럼을 생성했습니다.
- 전처리 후 파일 간 키 관계를 다시 확인했습니다.

## 주의 사항

이 전처리 기준은 실습용 예시입니다. 실제 업무에서는 결측치와 이상값을 삭제하거나 대체하기 전에 원본 시스템, 수집 과정, 업무 담당자 확인이 필요합니다.
"""
