"""Chapter 12 LLM 코드 생성과 검증 공통 함수 모음.

LLM이 만든 pandas, 시각화, 머신러닝 코드 초안을 실제 데이터 구조와 분석 목적에 맞게
검토하기 위한 유틸리티를 제공합니다. 핵심은 실행 전 컬럼/키/타깃 점검, 실행 후 행 수/총합/결측치
점검, 데이터 누수 및 평가 지표 점검, 검증 결과 기록입니다.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.eda import load_processed_sales_data


REQUIRED_COLUMNS = {
    "customers": ["customer_id", "gender", "age", "city"],
    "products": ["product_id", "product_name", "category", "price"],
    "orders": ["order_id", "customer_id", "order_date", "payment_method", "order_status"],
    "order_items": ["order_id", "product_id", "quantity", "unit_price"],
}

RELATIONSHIP_CHECKS = [
    {
        "left_dataset": "order_items",
        "right_dataset": "products",
        "key": "product_id",
        "purpose": "상품 정보와 주문 상세 연결",
    },
    {
        "left_dataset": "order_items",
        "right_dataset": "orders",
        "key": "order_id",
        "purpose": "주문 정보와 주문 상세 연결",
    },
    {
        "left_dataset": "orders",
        "right_dataset": "customers",
        "key": "customer_id",
        "purpose": "주문 정보와 고객 정보 연결",
    },
]


def load_validation_data(processed_dir: str | Path = "data/processed") -> dict[str, pd.DataFrame]:
    """검증 실습에 사용할 전처리 데이터를 불러옵니다."""
    return load_processed_sales_data(processed_dir)


def build_dataset_inventory(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """데이터셋별 실제 컬럼과 크기를 요약합니다."""
    rows = []
    for name, df in datasets.items():
        rows.append(
            {
                "dataset": name,
                "rows": df.shape[0],
                "columns": df.shape[1],
                "column_list": ", ".join(df.columns),
                "missing_values": int(df.isna().sum().sum()),
                "duplicated_rows": int(df.duplicated().sum()),
            }
        )
    return pd.DataFrame(rows)


def validate_required_columns(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """필수 컬럼 존재 여부를 점검합니다."""
    rows = []
    for dataset_name, required_cols in REQUIRED_COLUMNS.items():
        df = datasets[dataset_name]
        for col in required_cols:
            rows.append(
                {
                    "dataset": dataset_name,
                    "column": col,
                    "exists": col in df.columns,
                }
            )
    return pd.DataFrame(rows)


def validate_relationship_keys(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """병합 키가 양쪽 데이터셋에 존재하고 참조 누락이 있는지 점검합니다."""
    rows = []
    for check in RELATIONSHIP_CHECKS:
        left_name = check["left_dataset"]
        right_name = check["right_dataset"]
        key = check["key"]
        left_df = datasets[left_name]
        right_df = datasets[right_name]

        left_has_key = key in left_df.columns
        right_has_key = key in right_df.columns
        invalid_count = None
        if left_has_key and right_has_key:
            invalid_count = int((~left_df[key].isin(right_df[key])).sum())

        rows.append(
            {
                "purpose": check["purpose"],
                "left_dataset": left_name,
                "right_dataset": right_name,
                "key": key,
                "left_has_key": left_has_key,
                "right_has_key": right_has_key,
                "invalid_reference_count": invalid_count,
            }
        )
    return pd.DataFrame(rows)


def ensure_line_total(order_items: pd.DataFrame) -> pd.DataFrame:
    """line_total 컬럼이 없으면 quantity * unit_price로 생성합니다."""
    result = order_items.copy()
    if "line_total" not in result.columns:
        result["line_total"] = result["quantity"] * result["unit_price"]
    return result


def safe_category_sales(
    order_items: pd.DataFrame,
    products: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """검증 코드가 포함된 카테고리별 매출 집계표를 생성합니다."""
    items = ensure_line_total(order_items)
    before_rows = len(items)
    sales_items = items.merge(products, on="product_id", how="left")
    after_rows = len(sales_items)

    validation = pd.DataFrame(
        {
            "check_item": [
                "병합 전 order_items 행 수",
                "병합 후 sales_items 행 수",
                "병합 전후 행 수 동일 여부",
                "category 결측치 수",
                "line_total 숫자형 여부",
            ],
            "value": [
                before_rows,
                after_rows,
                before_rows == after_rows,
                int(sales_items["category"].isna().sum()),
                pd.api.types.is_numeric_dtype(sales_items["line_total"]),
            ],
        }
    )

    category_sales = (
        sales_items.groupby("category", as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    category_sales["sales_ratio"] = (
        category_sales["total_sales"] / category_sales["total_sales"].sum() * 100
    ).round(2)
    return category_sales, validation


def safe_monthly_sales(
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """검증 코드가 포함된 월별 매출 집계표를 생성합니다."""
    items = ensure_line_total(order_items)
    before_rows = len(items)
    order_sales = items.merge(orders, on="order_id", how="left")
    after_rows = len(order_sales)

    order_sales["order_date"] = pd.to_datetime(order_sales["order_date"], errors="coerce")
    order_sales["order_month"] = order_sales["order_date"].dt.to_period("M").astype(str)

    monthly_sales = (
        order_sales.groupby("order_month", as_index=False)
        .agg(total_sales=("line_total", "sum"), order_count=("order_id", "nunique"))
        .sort_values("order_month")
    )
    monthly_sales["avg_order_value"] = (
        monthly_sales["total_sales"] / monthly_sales["order_count"]
    ).round(0)

    validation = pd.DataFrame(
        {
            "check_item": [
                "병합 전 order_items 행 수",
                "병합 후 order_sales 행 수",
                "병합 전후 행 수 동일 여부",
                "order_date 변환 실패 수",
                "원본 line_total 합계",
                "월별 total_sales 합계",
                "총합 차이",
            ],
            "value": [
                before_rows,
                after_rows,
                before_rows == after_rows,
                int(order_sales["order_date"].isna().sum()),
                float(items["line_total"].sum()),
                float(monthly_sales["total_sales"].sum()),
                float(items["line_total"].sum() - monthly_sales["total_sales"].sum()),
            ],
        }
    )
    return monthly_sales, validation


def build_leakage_review_table() -> pd.DataFrame:
    """머신러닝 코드의 데이터 누수 위험 예시와 수정 방향을 정리합니다."""
    return pd.DataFrame(
        {
            "case": [
                "주문 취소 분류",
                "주문 금액 회귀",
                "고객 구매 금액 예측",
                "카테고리 매출 예측",
            ],
            "target": [
                "is_cancelled",
                "order_total",
                "customer_total_sales",
                "category_total_sales",
            ],
            "dangerous_feature": [
                "order_status",
                "order_total 또는 line_total 합계",
                "집계 이후의 총 구매 금액",
                "이미 계산된 카테고리 총매출",
            ],
            "why_dangerous": [
                "정답을 만들 때 사용한 컬럼이기 때문",
                "예측해야 할 값을 입력값으로 넣는 것이기 때문",
                "미래 또는 결과 정보를 미리 넣는 것이기 때문",
                "정답 그 자체 또는 정답에 가까운 정보를 넣는 것이기 때문",
            ],
            "safe_direction": [
                "order_status 제외, 결제수단/주문금액/고객특성 사용",
                "order_total 제외, 주문 전 또는 주문 구성 정보만 사용",
                "분석 시점 이전 행동 지표만 사용",
                "예측 시점 이전 상품 속성만 사용",
            ],
        }
    )


def build_code_review_checklist() -> pd.DataFrame:
    """LLM 코드 리뷰 체크리스트를 반환합니다."""
    return pd.DataFrame(
        {
            "category": [
                "데이터 구조",
                "데이터 구조",
                "병합",
                "병합",
                "전처리",
                "전처리",
                "머신러닝",
                "머신러닝",
                "해석",
                "보안",
            ],
            "check_item": [
                "실제 데이터셋 이름을 사용했는가?",
                "실제 컬럼명만 사용했는가?",
                "병합 기준 컬럼이 양쪽 데이터에 모두 존재하는가?",
                "병합 전후 행 수를 확인했는가?",
                "날짜와 숫자형 변환 실패를 확인했는가?",
                "결측치와 중복을 무시하지 않았는가?",
                "타깃 컬럼이 명확하게 정의되었는가?",
                "데이터 누수가 없는가?",
                "결과를 원인으로 단정하지 않았는가?",
                "개인정보나 API Key가 코드와 프롬프트에 포함되지 않았는가?",
            ],
            "status": ["미확인"] * 10,
            "memo": [""] * 10,
        }
    )


def build_error_fix_prompt_template() -> str:
    """오류 메시지를 LLM에 전달할 때 사용할 수정 프롬프트 템플릿을 반환합니다."""
    return """다음 pandas 코드에서 오류가 발생했습니다.

목표:
- products와 order_items를 product_id 기준으로 병합해 카테고리별 매출을 계산하려고 합니다.

현재 데이터 컬럼:
- products: product_id, product_name, category, price
- order_items: order_id, product_id, quantity, unit_price, line_total

실행한 코드:
[여기에 코드 붙여넣기]

오류 메시지:
[여기에 오류 메시지 붙여넣기]

요청:
1. 오류 원인을 초보자도 이해할 수 있게 설명해 주세요.
2. 실제 컬럼명만 사용해 수정 코드를 제안해 주세요.
3. 병합 후 행 수와 category 결측치 확인 코드도 포함해 주세요.
4. 데이터에 없는 컬럼명은 새로 만들지 마세요.
"""


def build_validation_summary(
    inventory: pd.DataFrame,
    required_column_check: pd.DataFrame,
    relationship_check: pd.DataFrame,
    category_validation: pd.DataFrame,
    monthly_validation: pd.DataFrame,
    leakage_review: pd.DataFrame,
) -> str:
    """LLM 코드 검증 요약 Markdown 문자열을 생성합니다."""
    return f"""# Chapter 12 LLM 코드 생성과 검증 요약

## 1. 코드 생성 목적

LLM을 활용해 온라인 쇼핑몰 데이터의 카테고리별 매출, 월별 매출, 머신러닝 코드 초안을 만들고 검증했습니다.

## 2. 데이터셋 인벤토리

```text
{inventory.to_string(index=False)}
```

## 3. 필수 컬럼 점검

```text
{required_column_check.to_string(index=False)}
```

## 4. 키 관계 점검

```text
{relationship_check.to_string(index=False)}
```

## 5. 카테고리별 매출 코드 검증

```text
{category_validation.to_string(index=False)}
```

## 6. 월별 매출 코드 검증

```text
{monthly_validation.to_string(index=False)}
```

## 7. 머신러닝 데이터 누수 검토

```text
{leakage_review.to_string(index=False)}
```

## 8. 검토 기준

- 실제 데이터셋 이름과 컬럼명을 사용했는지 확인했습니다.
- 병합 기준과 병합 전후 행 수를 확인했습니다.
- 날짜형과 숫자형 변환 여부를 확인했습니다.
- 머신러닝 코드에서는 데이터 누수가 없는지 확인했습니다.
- 분류 모델에서는 accuracy 외 precision, recall, f1-score를 함께 확인해야 합니다.
- 보고서 해석에서는 데이터에 없는 원인을 단정하지 않도록 수정해야 합니다.

## 9. 주의할 점

LLM이 만든 코드는 초안으로만 사용해야 하며, 최종 코드는 실제 데이터 구조와 실행 결과를 기준으로 사람이 검증해야 합니다.
"""


def save_validation_outputs(
    outputs: dict[str, pd.DataFrame | str],
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """12장 코드 검증 결과물을 저장합니다."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_map = {
        "inventory": "ch12_dataset_inventory.csv",
        "required_column_check": "ch12_required_column_check.csv",
        "relationship_check": "ch12_relationship_key_check.csv",
        "category_sales": "ch12_category_sales_validated.csv",
        "category_validation": "ch12_category_sales_validation.csv",
        "monthly_sales": "ch12_monthly_sales_validated.csv",
        "monthly_validation": "ch12_monthly_sales_validation.csv",
        "leakage_review": "ch12_ml_leakage_review.csv",
        "code_review_checklist": "ch12_llm_code_review_checklist.csv",
    }

    paths: dict[str, Path] = {}
    for key, filename in file_map.items():
        path = output_dir / filename
        value = outputs[key]
        if isinstance(value, pd.DataFrame):
            value.to_csv(path, index=False, encoding="utf-8-sig")
        paths[key] = path

    prompt_path = output_dir / "ch12_error_fix_prompt_template.md"
    prompt_path.write_text(str(outputs["error_fix_prompt"]), encoding="utf-8")
    paths["error_fix_prompt"] = prompt_path

    summary_path = output_dir / "ch12_code_validation_summary.md"
    summary_path.write_text(str(outputs["validation_summary"]), encoding="utf-8")
    paths["validation_summary"] = summary_path
    return paths


def run_llm_code_validation(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
) -> dict[str, object]:
    """12장 LLM 코드 검증 자료 생성 파이프라인을 실행합니다."""
    datasets = load_validation_data(processed_dir)
    inventory = build_dataset_inventory(datasets)
    required_column_check = validate_required_columns(datasets)
    relationship_check = validate_relationship_keys(datasets)

    category_sales, category_validation = safe_category_sales(
        order_items=datasets["order_items"],
        products=datasets["products"],
    )
    monthly_sales, monthly_validation = safe_monthly_sales(
        order_items=datasets["order_items"],
        orders=datasets["orders"],
    )
    leakage_review = build_leakage_review_table()
    code_review_checklist = build_code_review_checklist()
    error_fix_prompt = build_error_fix_prompt_template()
    validation_summary = build_validation_summary(
        inventory=inventory,
        required_column_check=required_column_check,
        relationship_check=relationship_check,
        category_validation=category_validation,
        monthly_validation=monthly_validation,
        leakage_review=leakage_review,
    )

    outputs: dict[str, pd.DataFrame | str] = {
        "inventory": inventory,
        "required_column_check": required_column_check,
        "relationship_check": relationship_check,
        "category_sales": category_sales,
        "category_validation": category_validation,
        "monthly_sales": monthly_sales,
        "monthly_validation": monthly_validation,
        "leakage_review": leakage_review,
        "code_review_checklist": code_review_checklist,
        "error_fix_prompt": error_fix_prompt,
        "validation_summary": validation_summary,
    }
    output_paths = save_validation_outputs(outputs, report_dir)

    return {
        "datasets": datasets,
        "outputs": outputs,
        "output_paths": output_paths,
    }
