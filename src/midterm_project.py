"""Chapter 8 중간 프로젝트 파이프라인.

데이터 로드, 전처리, 집계, 시각화, 보고서 생성을 하나로 묶은 작은 데이터 분석 프로젝트 모듈입니다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.data_loader import load_sales_data
from src.preprocessing import compare_shapes, preprocess_sales_data, validate_relationships
from src.visualization import setup_korean_font


PROJECT_QUESTIONS = [
    "카테고리별 매출은 어떻게 다른가?",
    "월별 매출과 주문 수는 어떻게 변하는가?",
    "구매 금액 상위 고객은 누구인가?",
    "주문 상태별 주문 수는 어떻게 분포하는가?",
]


def summarize_datasets(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """데이터셋별 행/열 수와 결측치, 중복 행 수를 요약합니다."""
    rows = []
    for name, df in data.items():
        rows.append(
            {
                "dataset": name,
                "rows": df.shape[0],
                "columns": df.shape[1],
                "missing_values": int(df.isna().sum().sum()),
                "duplicated_rows": int(df.duplicated().sum()),
            }
        )
    return pd.DataFrame(rows)


def build_analysis_tables(
    processed_data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """중간 프로젝트 핵심 분석표를 생성합니다."""
    customers = processed_data["customers"].copy()
    products = processed_data["products"].copy()
    orders = processed_data["orders"].copy()
    order_items = processed_data["order_items"].copy()

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    if "order_month" not in orders.columns:
        orders["order_month"] = orders["order_date"].dt.to_period("M").astype(str)

    if "line_total" not in order_items.columns:
        order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]

    sales_items = order_items.merge(products, on="product_id", how="left")
    order_sales = order_items.merge(orders, on="order_id", how="left")
    customer_sales_base = order_sales.merge(customers, on="customer_id", how="left")

    category_sales = (
        sales_items.groupby("category", as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    category_sales["sales_ratio"] = (
        category_sales["total_sales"] / category_sales["total_sales"].sum() * 100
    ).round(2)

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

    group_columns = ["customer_id", "city"]
    if "name" in customer_sales_base.columns:
        group_columns = ["customer_id", "name", "city"]

    customer_sales = (
        customer_sales_base.groupby(group_columns, as_index=False)
        .agg(order_count=("order_id", "nunique"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    customer_sales["avg_order_value"] = (
        customer_sales["total_sales"] / customer_sales["order_count"]
    ).round(0)

    order_status_summary = orders["order_status"].value_counts(dropna=False).reset_index()
    order_status_summary.columns = ["order_status", "order_count"]
    order_status_summary["order_ratio"] = (
        order_status_summary["order_count"] / order_status_summary["order_count"].sum() * 100
    ).round(2)

    return {
        "sales_items": sales_items,
        "order_sales": order_sales,
        "customer_sales_base": customer_sales_base,
        "category_sales": category_sales,
        "monthly_sales": monthly_sales,
        "customer_sales": customer_sales,
        "order_status_summary": order_status_summary,
    }


def build_interpretation_notes() -> pd.DataFrame:
    """프로젝트 주요 결과 해석 메모를 반환합니다."""
    return pd.DataFrame(
        {
            "analysis": [
                "카테고리별 매출",
                "월별 매출",
                "고객별 구매 금액",
                "주문 상태별 주문 수",
            ],
            "observation": [
                "매출이 높은 카테고리를 확인할 수 있습니다.",
                "시간에 따른 매출 증가와 감소 흐름을 확인할 수 있습니다.",
                "구매 금액이 높은 고객 후보를 확인할 수 있습니다.",
                "주문 상태의 분포를 확인할 수 있습니다.",
            ],
            "caution": [
                "매출이 높은 이유가 판매 수량 때문인지 단가 때문인지 추가 확인이 필요합니다.",
                "매출 변화의 원인을 설명하려면 프로모션, 계절성, 주문 수 변화 확인이 필요합니다.",
                "일회성 고액 구매 고객과 반복 구매 고객을 구분해야 합니다.",
                "취소 주문이 매출 계산에 포함되었는지 확인해야 합니다.",
            ],
        }
    )


def save_project_tables(
    dataset_summary: pd.DataFrame,
    preprocessing_comparison: pd.DataFrame,
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
        "ch08_relationship_checks.csv": relationship_checks,
        "ch08_category_sales.csv": analysis_tables["category_sales"],
        "ch08_monthly_sales.csv": analysis_tables["monthly_sales"],
        "ch08_customer_sales.csv": analysis_tables["customer_sales"],
        "ch08_order_status_summary.csv": analysis_tables["order_status_summary"],
        "ch08_interpretation_notes.csv": interpretation_notes,
    }

    saved_paths: list[Path] = []
    for filename, df in outputs.items():
        path = output_dir / filename
        df.to_csv(path, index=False, encoding="utf-8-sig")
        saved_paths.append(path)

    return saved_paths


def _save_current_figure(output_path: Path, show: bool = False) -> None:
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
    """중간 프로젝트용 그래프 3개를 생성합니다."""
    setup_korean_font()
    output_dir = Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    category_sales = analysis_tables["category_sales"]
    monthly_sales = analysis_tables["monthly_sales"]
    customer_sales = analysis_tables["customer_sales"]

    category_path = output_dir / "ch08_category_sales.png"
    plt.figure(figsize=(10, 5))
    plt.bar(category_sales["category"], category_sales["total_sales"])
    plt.title("카테고리별 매출")
    plt.xlabel("카테고리")
    plt.ylabel("총매출")
    plt.xticks(rotation=45)
    _save_current_figure(category_path, show=show)

    monthly_path = output_dir / "ch08_monthly_sales.png"
    plt.figure(figsize=(10, 5))
    plt.plot(monthly_sales["order_month"], monthly_sales["total_sales"], marker="o")
    plt.title("월별 매출 추이")
    plt.xlabel("주문 월")
    plt.ylabel("총매출")
    plt.xticks(rotation=45)
    _save_current_figure(monthly_path, show=show)

    top_customers = customer_sales.head(10).copy()
    top_customers["customer_label"] = "Customer " + top_customers["customer_id"].astype(str)
    top_customers = top_customers.sort_values("total_sales")

    customer_path = output_dir / "ch08_top_customers.png"
    plt.figure(figsize=(10, 6))
    plt.barh(top_customers["customer_label"], top_customers["total_sales"])
    plt.title("구매 금액 상위 10명 고객")
    plt.xlabel("총 구매 금액")
    plt.ylabel("고객")
    _save_current_figure(customer_path, show=show)

    return [category_path, monthly_path, customer_path]


def build_midterm_report(
    dataset_summary: pd.DataFrame,
    preprocessing_comparison: pd.DataFrame,
    analysis_tables: dict[str, pd.DataFrame],
    interpretation_notes: pd.DataFrame,
) -> str:
    """중간 프로젝트 Markdown 보고서 문자열을 생성합니다."""
    category_sales = analysis_tables["category_sales"]
    monthly_sales = analysis_tables["monthly_sales"]
    customer_sales = analysis_tables["customer_sales"]
    order_status_summary = analysis_tables["order_status_summary"]

    return f"""# Chapter 8 중간 프로젝트 보고서

## 1. 분석 목적

온라인 쇼핑몰 고객, 상품, 주문, 주문 상세 데이터를 사용해 기본 매출 현황과 고객 구매 패턴을 분석했습니다.

## 2. 데이터 개요

```text
{dataset_summary.to_string(index=False)}
```

## 3. 전처리 전후 비교

```text
{preprocessing_comparison.to_string(index=False)}
```

## 4. 주요 분석 질문

1. 카테고리별 매출은 어떻게 다른가?
2. 월별 매출과 주문 수는 어떻게 변하는가?
3. 구매 금액 상위 고객은 누구인가?
4. 주문 상태별 주문 수는 어떻게 분포하는가?

## 5. 카테고리별 매출

```text
{category_sales.to_string(index=False)}
```

## 6. 월별 매출

```text
{monthly_sales.to_string(index=False)}
```

## 7. 구매 금액 상위 고객

```text
{customer_sales.head(10).to_string(index=False)}
```

## 8. 주문 상태별 주문 수

```text
{order_status_summary.to_string(index=False)}
```

## 9. 해석 메모

```text
{interpretation_notes.to_string(index=False)}
```

## 10. 한계점

- 현재 데이터만으로 고객 만족도나 이탈 이유는 분석할 수 없습니다.
- 매출 변화의 원인을 설명하려면 프로모션, 광고, 재고, 계절성 데이터가 추가로 필요합니다.
- 구매 금액 상위 고객은 주문 횟수와 평균 주문 금액을 함께 해석해야 합니다.
- 취소 주문과 환불 주문 처리 기준에 따라 매출 결과가 달라질 수 있습니다.

## 11. 다음 단계

- 카테고리별 판매 수량과 평균 단가를 함께 비교합니다.
- 월별 매출 변동 원인을 추가 데이터와 함께 분석합니다.
- 고객별 구매 금액을 기준으로 고객 세분화를 시도합니다.
- LLM을 활용해 보고서 문장을 보완하되, 데이터에 없는 원인은 단정하지 않습니다.
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
        df.to_csv(processed_path / f"{name}_clean.csv", index=False, encoding="utf-8-sig")

    preprocessing_comparison = compare_shapes(raw_data, processed_data)
    relationship_checks = validate_relationships(processed_data)
    analysis_tables = build_analysis_tables(processed_data)
    interpretation_notes = build_interpretation_notes()

    saved_tables = save_project_tables(
        dataset_summary,
        preprocessing_comparison,
        relationship_checks,
        analysis_tables,
        interpretation_notes,
        report_dir,
    )
    saved_figures = create_project_figures(analysis_tables, figure_dir, show=show_figures)

    output_report_dir = Path(report_dir)
    output_report_dir.mkdir(parents=True, exist_ok=True)
    report_text = build_midterm_report(
        dataset_summary,
        preprocessing_comparison,
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
        "relationship_checks": relationship_checks,
        "analysis_tables": analysis_tables,
        "interpretation_notes": interpretation_notes,
        "saved_tables": saved_tables,
        "saved_figures": saved_figures,
        "report_path": report_path,
    }
