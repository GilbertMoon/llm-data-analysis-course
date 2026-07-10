"""Chapter 8 중간 프로젝트 파이프라인.

데이터 로드, 전처리, 안전한 병합, 완료 주문 기준 집계, 시각화,
보고서 생성을 하나의 재현 가능한 프로젝트 흐름으로 묶습니다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.data_loader import load_sales_data
from src.preprocessing import compare_shapes, preprocess_sales_data, validate_relationships
from src.visualization import setup_korean_font


PROJECT_QUESTIONS = [
    "카테고리별 완료 주문 매출은 어떻게 다른가?",
    "월별 완료 주문 매출과 주문 수는 어떻게 변하는가?",
    "완료 주문 기준 구매 금액 상위 고객은 누구인가?",
    "주문 상태별 주문 수는 어떻게 분포하는가?",
]


def summarize_datasets(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """데이터셋별 행/열 수와 결측치, 중복 행 수를 요약합니다."""
    return pd.DataFrame(
        [
            {
                "dataset": name,
                "rows": df.shape[0],
                "columns": df.shape[1],
                "missing_values": int(df.isna().sum().sum()),
                "duplicated_rows": int(df.duplicated().sum()),
            }
            for name, df in data.items()
        ]
    )


def build_key_duplicate_checks(
    processed_data: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """주요 키 컬럼의 중복 건수를 확인합니다."""
    key_map = {
        "customers": "customer_id",
        "products": "product_id",
        "orders": "order_id",
        "order_items": "order_item_id",
    }
    rows = []
    for dataset, key in key_map.items():
        df = processed_data[dataset]
        rows.append(
            {
                "dataset": dataset,
                "key": key,
                "duplicate_count": (
                    int(df[key].duplicated().sum())
                    if key in df.columns
                    else None
                ),
            }
        )
    return pd.DataFrame(rows)


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


def build_analysis_tables(
    processed_data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """완료 주문 기준 핵심 분석표와 병합 검증표를 생성합니다."""
    customers = processed_data["customers"].copy()
    products = processed_data["products"].copy()
    orders = processed_data["orders"].copy()
    order_items = processed_data["order_items"].copy()

    required_columns = {
        "customers": {"customer_id", "city"},
        "products": {"product_id", "product_name", "category", "price"},
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
    for name, required in required_columns.items():
        missing = sorted(required - set(processed_data[name].columns))
        if missing:
            raise KeyError(f"{name}에 필요한 컬럼이 없습니다: {missing}")

    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce",
    )
    orders = orders.dropna(
        subset=["order_id", "customer_id", "order_date", "order_status"]
    ).copy()
    orders["order_month"] = (
        orders["order_date"].dt.to_period("M").astype(str)
    )

    if "line_total" not in order_items.columns:
        order_items["line_total"] = (
            order_items["quantity"] * order_items["unit_price"]
        )

    order_sales, order_merge_check = _checked_left_merge(
        order_items,
        orders[
            [
                "order_id",
                "customer_id",
                "order_date",
                "order_month",
                "order_status",
            ]
        ],
        on="order_id",
        validate="many_to_one",
        right_label="orders",
    )

    completed_order_sales = order_sales[
        order_sales["order_status"] == "completed"
    ].copy()

    completed_sales_items, product_merge_check = _checked_left_merge(
        completed_order_sales,
        products[
            ["product_id", "product_name", "category", "price"]
        ],
        on="product_id",
        validate="many_to_one",
        right_label="products",
    )

    category_sales = (
        completed_sales_items
        .groupby("category", as_index=False)
        .agg(
            total_quantity=("quantity", "sum"),
            total_sales=("line_total", "sum"),
        )
        .sort_values("total_sales", ascending=False)
    )
    category_total = category_sales["total_sales"].sum()
    category_sales["sales_ratio"] = (
        category_sales["total_sales"] / category_total * 100
        if category_total
        else 0
    )
    category_sales["sales_ratio"] = category_sales["sales_ratio"].round(2)

    monthly_sales = (
        completed_order_sales
        .groupby("order_month", as_index=False)
        .agg(
            total_sales=("line_total", "sum"),
            order_count=("order_id", "nunique"),
        )
        .sort_values("order_month")
    )
    monthly_sales["avg_order_value"] = (
        monthly_sales["total_sales"]
        / monthly_sales["order_count"].replace(0, pd.NA)
    ).round(0)

    customer_sales = (
        completed_order_sales
        .groupby("customer_id", as_index=False)
        .agg(
            order_count=("order_id", "nunique"),
            total_sales=("line_total", "sum"),
        )
        .sort_values("total_sales", ascending=False)
    )
    customer_sales["avg_order_value"] = (
        customer_sales["total_sales"]
        / customer_sales["order_count"].replace(0, pd.NA)
    ).round(0)

    customer_sales, customer_merge_check = _checked_left_merge(
        customer_sales,
        customers[["customer_id", "city"]],
        on="customer_id",
        validate="one_to_one",
        right_label="customers",
    )
    customer_sales["customer_label"] = (
        "Customer " + customer_sales["customer_id"].astype(str)
    )
    customer_sales = customer_sales[
        [
            "customer_id",
            "customer_label",
            "city",
            "order_count",
            "total_sales",
            "avg_order_value",
        ]
    ]

    order_status_summary = (
        orders["order_status"]
        .value_counts(dropna=False)
        .rename_axis("order_status")
        .reset_index(name="order_count")
    )
    order_status_summary["order_ratio"] = (
        order_status_summary["order_count"]
        / order_status_summary["order_count"].sum()
        * 100
    ).round(2)

    amount_scope_summary = pd.DataFrame(
        {
            "scope": [
                "all_order_items",
                "completed_order_items",
                "excluded_cancelled_or_refunded",
            ],
            "amount": [
                float(order_sales["line_total"].sum()),
                float(completed_order_sales["line_total"].sum()),
                float(
                    order_sales["line_total"].sum()
                    - completed_order_sales["line_total"].sum()
                ),
            ],
            "detail_rows": [
                len(order_sales),
                len(completed_order_sales),
                len(order_sales) - len(completed_order_sales),
            ],
        }
    )

    merge_checks = pd.DataFrame(
        [
            order_merge_check,
            product_merge_check,
            customer_merge_check,
        ]
    )

    return {
        "order_sales": order_sales,
        "completed_order_sales": completed_order_sales,
        "completed_sales_items": completed_sales_items,
        "category_sales": category_sales,
        "monthly_sales": monthly_sales,
        "customer_sales": customer_sales,
        "order_status_summary": order_status_summary,
        "amount_scope_summary": amount_scope_summary,
        "merge_checks": merge_checks,
    }


def build_interpretation_notes() -> pd.DataFrame:
    """프로젝트 주요 결과의 관찰, 주의점, 다음 질문을 반환합니다."""
    return pd.DataFrame(
        {
            "analysis": [
                "카테고리별 완료 주문 매출",
                "월별 완료 주문 매출",
                "고객별 완료 주문 구매 금액",
                "주문 상태별 주문 수",
            ],
            "observation": [
                "완료 주문 매출 비중이 높은 카테고리를 확인할 수 있습니다.",
                "시간에 따른 완료 주문 매출의 증가와 감소를 확인할 수 있습니다.",
                "완료 주문 구매 금액이 높은 고객군을 확인할 수 있습니다.",
                "완료, 취소, 환불 주문의 분포를 확인할 수 있습니다.",
            ],
            "caution": [
                "매출이 높은 이유가 판매 수량인지 단가인지 구분해야 합니다.",
                "프로모션이나 계절성이 원인이라고 단정할 수 없습니다.",
                "일회성 고액 구매와 반복 구매를 구분해야 합니다.",
                "주문 상태의 정의와 처리 기준을 확인해야 합니다.",
            ],
            "next_question": [
                "카테고리별 평균 판매 단가는 어떻게 다른가?",
                "주문 수와 평균 주문 금액 중 무엇이 변했는가?",
                "최근 구매일과 구매 빈도는 어떻게 다른가?",
                "취소율과 환불률은 월별로 달라지는가?",
            ],
        }
    )


def save_project_tables(
    dataset_summary: pd.DataFrame,
    preprocessing_comparison: pd.DataFrame,
    key_duplicate_checks: pd.DataFrame,
    relationship_checks: pd.DataFrame,
    analysis_tables: dict[str, pd.DataFrame],
    interpretation_notes: pd.DataFrame,
    report_dir: str | Path = "reports",
) -> list[Path]:
    """중간 프로젝트 결과표를 CSV 파일로 저장합니다."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "ch08_dataset_summary.csv": dataset_summary,
        "ch08_preprocessing_comparison.csv": preprocessing_comparison,
        "ch08_key_duplicate_checks.csv": key_duplicate_checks,
        "ch08_relationship_checks.csv": relationship_checks,
        "ch08_merge_checks.csv": analysis_tables["merge_checks"],
        "ch08_amount_scope_summary.csv": analysis_tables[
            "amount_scope_summary"
        ],
        "ch08_category_sales.csv": analysis_tables["category_sales"],
        "ch08_monthly_sales.csv": analysis_tables["monthly_sales"],
        "ch08_customer_sales.csv": analysis_tables["customer_sales"],
        "ch08_order_status_summary.csv": analysis_tables[
            "order_status_summary"
        ],
        "ch08_interpretation_notes.csv": interpretation_notes,
    }

    saved_paths: list[Path] = []
    for filename, df in outputs.items():
        path = output_dir / filename
        df.to_csv(path, index=False, encoding="utf-8-sig")
        saved_paths.append(path)

    return saved_paths


def _save_current_figure(
    output_path: Path,
    show: bool = False,
) -> None:
    """현재 matplotlib Figure를 저장하고 필요하면 표시합니다."""
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close()


def create_project_figures(
    analysis_tables: dict[str, pd.DataFrame],
    figure_dir: str | Path = "reports/figures",
    show: bool = False,
) -> list[Path]:
    """완료 주문 기준 프로젝트 그래프 3개를 생성합니다."""
    setup_korean_font()
    output_dir = Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    category_sales = analysis_tables["category_sales"]
    monthly_sales = analysis_tables["monthly_sales"]
    customer_sales = analysis_tables["customer_sales"]

    category_path = output_dir / "ch08_category_sales.png"
    plt.figure(figsize=(10, 5))
    plt.bar(
        category_sales["category"],
        category_sales["total_sales"],
    )
    plt.title("카테고리별 완료 주문 매출")
    plt.xlabel("카테고리")
    plt.ylabel("매출")
    plt.xticks(rotation=45)
    _save_current_figure(category_path, show=show)

    monthly_path = output_dir / "ch08_monthly_sales.png"
    plt.figure(figsize=(10, 5))
    plt.plot(
        monthly_sales["order_month"],
        monthly_sales["total_sales"],
        marker="o",
    )
    plt.title("월별 완료 주문 매출 추이")
    plt.xlabel("주문 월")
    plt.ylabel("매출")
    plt.xticks(rotation=45)
    _save_current_figure(monthly_path, show=show)

    top_customers = customer_sales.head(10).sort_values(
        "total_sales"
    )
    customer_path = output_dir / "ch08_top_customers.png"
    plt.figure(figsize=(10, 6))
    plt.barh(
        top_customers["customer_label"],
        top_customers["total_sales"],
    )
    plt.title("완료 주문 구매 금액 상위 10명")
    plt.xlabel("총 구매 금액")
    plt.ylabel("익명화 고객")
    _save_current_figure(customer_path, show=show)

    return [category_path, monthly_path, customer_path]


def build_midterm_report(
    dataset_summary: pd.DataFrame,
    preprocessing_comparison: pd.DataFrame,
    key_duplicate_checks: pd.DataFrame,
    relationship_checks: pd.DataFrame,
    analysis_tables: dict[str, pd.DataFrame],
    interpretation_notes: pd.DataFrame,
) -> str:
    """개인정보를 최소화한 중간 프로젝트 Markdown 보고서를 생성합니다."""
    category_sales = analysis_tables["category_sales"]
    monthly_sales = analysis_tables["monthly_sales"]
    customer_report = analysis_tables["customer_sales"][
        [
            "customer_label",
            "city",
            "order_count",
            "total_sales",
            "avg_order_value",
        ]
    ].head(10)
    order_status_summary = analysis_tables["order_status_summary"]
    amount_scope_summary = analysis_tables["amount_scope_summary"]
    merge_checks = analysis_tables["merge_checks"]

    return f"""# Chapter 8 중간 프로젝트 보고서

## 1. 분석 목적

온라인 쇼핑몰 데이터를 사용해 완료 주문 기준 매출 현황과 고객 구매 패턴을 분석했습니다.

## 2. 분석 기준

- 매출은 `order_status == "completed"`인 주문만 포함했습니다.
- 취소·환불 주문을 포함한 금액은 전체 주문 상세 금액으로 구분했습니다.
- 고객 이름은 결과와 보고서에서 제외하고 익명화 라벨을 사용했습니다.
- 병합은 관계 검증과 행 수·미매칭 확인을 수행했습니다.

## 3. 데이터 개요

```text
{dataset_summary.to_string(index=False)}
```

## 4. 전처리 전후 비교

```text
{preprocessing_comparison.to_string(index=False)}
```

## 5. 키와 관계 점검

### 키 중복

```text
{key_duplicate_checks.to_string(index=False)}
```

### 외래키 관계

```text
{relationship_checks.to_string(index=False)}
```

### 병합 검증

```text
{merge_checks.to_string(index=False)}
```

## 6. 전체 주문 금액과 완료 주문 매출 구분

```text
{amount_scope_summary.to_string(index=False)}
```

## 7. 카테고리별 완료 주문 매출

```text
{category_sales.to_string(index=False)}
```

## 8. 월별 완료 주문 매출

```text
{monthly_sales.to_string(index=False)}
```

## 9. 완료 주문 구매 금액 상위 고객

```text
{customer_report.to_string(index=False)}
```

## 10. 주문 상태별 주문 수

```text
{order_status_summary.to_string(index=False)}
```

## 11. 해석 메모

```text
{interpretation_notes.to_string(index=False)}
```

## 12. 한계점

- 현재 데이터만으로 고객 만족도나 이탈 이유를 분석할 수 없습니다.
- 매출 변동의 원인을 설명하려면 프로모션, 광고, 재고, 계절성 데이터가 필요합니다.
- 완료 주문만 매출로 정의했으며 실제 회계 매출은 결제·배송·반품 정책에 따라 다를 수 있습니다.
- 고객별 결과는 익명화된 분석용 요약이며 개인을 평가하는 용도로 사용하면 안 됩니다.

## 13. 다음 단계

- 카테고리별 판매 수량과 평균 판매 단가를 함께 비교합니다.
- 월별 주문 수와 평균 주문 금액의 변화를 분리해 확인합니다.
- 고객별 최근 구매일과 구매 빈도를 추가합니다.
- 주문 취소율과 환불률의 월별 변화를 분석합니다.
"""


def run_midterm_project(
    raw_dir: str | Path = "data/raw",
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    figure_dir: str | Path = "reports/figures",
    show_figures: bool = False,
) -> dict[str, object]:
    """8장 중간 프로젝트 전체 파이프라인을 실행합니다."""
    raw_data = load_sales_data(raw_dir)
    dataset_summary = summarize_datasets(raw_data)

    processed_data = preprocess_sales_data(raw_data)
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)
    for name, df in processed_data.items():
        df.to_csv(
            processed_path / f"{name}_clean.csv",
            index=False,
            encoding="utf-8-sig",
        )

    preprocessing_comparison = compare_shapes(
        raw_data,
        processed_data,
    )
    key_duplicate_checks = build_key_duplicate_checks(
        processed_data
    )
    relationship_checks = validate_relationships(
        processed_data
    )
    analysis_tables = build_analysis_tables(processed_data)
    interpretation_notes = build_interpretation_notes()

    saved_tables = save_project_tables(
        dataset_summary,
        preprocessing_comparison,
        key_duplicate_checks,
        relationship_checks,
        analysis_tables,
        interpretation_notes,
        report_dir,
    )
    saved_figures = create_project_figures(
        analysis_tables,
        figure_dir,
        show=show_figures,
    )

    output_report_dir = Path(report_dir)
    output_report_dir.mkdir(parents=True, exist_ok=True)
    report_text = build_midterm_report(
        dataset_summary,
        preprocessing_comparison,
        key_duplicate_checks,
        relationship_checks,
        analysis_tables,
        interpretation_notes,
    )
    report_path = output_report_dir / "ch08_midterm_report.md"
    report_path.write_text(report_text, encoding="utf-8")

    return {
        "raw_data": raw_data,
        "processed_data": processed_data,
        "dataset_summary": dataset_summary,
        "preprocessing_comparison": preprocessing_comparison,
        "key_duplicate_checks": key_duplicate_checks,
        "relationship_checks": relationship_checks,
        "analysis_tables": analysis_tables,
        "interpretation_notes": interpretation_notes,
        "saved_tables": saved_tables,
        "saved_figures": saved_figures,
        "report_path": report_path,
    }
