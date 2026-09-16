"""Chapter 8 중간 프로젝트 파이프라인.

데이터 로드, 전처리, 키/관계 검증, 안전한 병합, 완료 주문 기준 집계,
총합 검증, 시각화, 보고서 생성을 하나의 재현 가능한 프로젝트 흐름으로 묶습니다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data_loader import load_sales_data
from src.preprocessing import compare_shapes, preprocess_sales_data, validate_relationships
from src.visualization import setup_korean_font


PROJECT_QUESTIONS = [
    "카테고리별 completed 주문 기준 금액은 어떻게 다른가?",
    "월별 completed 주문 기준 금액과 주문 수는 어떻게 변하는가?",
    "completed 주문 기준 구매 금액이 높은 고객은 누구인가?",
    "주문 상태별 주문 수는 어떻게 분포하는가?",
]

PUBLIC_CUSTOMER_COLUMNS = [
    "customer_label",
    "city",
    "order_count",
    "total_sales",
    "avg_order_value",
]

FORBIDDEN_CUSTOMER_COLUMNS = {
    "customer_id",
    "name",
    "email",
    "phone",
    "address",
}


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
    """주요 PK의 결측·중복 건수와 PASS/FAIL을 확인합니다."""
    key_map = {
        "customers": "customer_id",
        "products": "product_id",
        "orders": "order_id",
        "order_items": "order_item_id",
    }

    rows: list[dict[str, object]] = []
    for dataset, key in key_map.items():
        df = processed_data[dataset]
        if key not in df.columns:
            rows.append(
                {
                    "dataset": dataset,
                    "key": key,
                    "missing_count": None,
                    "duplicate_count": None,
                    "status": "FAIL",
                    "detail": "key column missing",
                }
            )
            continue

        missing_count = int(df[key].isna().sum())
        duplicate_count = int(df[key].dropna().duplicated().sum())
        passed = missing_count == 0 and duplicate_count == 0

        rows.append(
            {
                "dataset": dataset,
                "key": key,
                "missing_count": missing_count,
                "duplicate_count": duplicate_count,
                "status": "PASS" if passed else "FAIL",
                "detail": "" if passed else "PK missing or duplicate values found",
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
    """left merge를 실행하고 행 수·미매칭·PASS/FAIL을 반환합니다."""
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
    row_count_preserved = before_rows == after_rows
    passed = row_count_preserved and unmatched_count == 0

    check = {
        "merge": f"{on} → {right_label}",
        "validate": validate,
        "before_rows": before_rows,
        "after_rows": after_rows,
        "row_count_preserved": row_count_preserved,
        "unmatched_count": unmatched_count,
        "status": "PASS" if passed else "FAIL",
    }
    return merged.drop(columns="_merge"), check


def _build_line_total_check(order_items: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """line_total이 quantity × unit_price와 일치하는지 확인합니다."""
    expected = order_items["quantity"] * order_items["unit_price"]

    if "line_total" not in order_items.columns:
        actual = expected.copy()
        source = "calculated"
    else:
        actual = order_items["line_total"]
        source = "existing"

    matches = pd.Series(
        np.isclose(
            actual.astype(float),
            expected.astype(float),
            equal_nan=False,
        ),
        index=order_items.index,
    )
    mismatch_count = int((~matches).sum())

    check = pd.DataFrame(
        [
            {
                "check": "line_total = quantity × unit_price",
                "source": source,
                "row_count": len(order_items),
                "mismatch_count": mismatch_count,
                "status": "PASS" if mismatch_count == 0 else "FAIL",
            }
        ]
    )
    return check, expected


def _build_total_consistency_check(
    completed_order_sales: pd.DataFrame,
    category_sales: pd.DataFrame,
    monthly_sales: pd.DataFrame,
    customer_sales: pd.DataFrame,
) -> pd.DataFrame:
    """같은 completed 범위에서 만든 금액 총합이 일치하는지 확인합니다."""
    completed_total = float(completed_order_sales["line_total"].sum())

    totals = [
        ("completed_source", completed_total),
        ("category", float(category_sales["total_sales"].sum())),
        ("monthly", float(monthly_sales["total_sales"].sum())),
        ("customer", float(customer_sales["total_sales"].sum())),
    ]

    rows = []
    for source, amount in totals:
        difference = amount - completed_total
        matches = bool(np.isclose(amount, completed_total, rtol=1e-9, atol=1e-6))
        rows.append(
            {
                "source": source,
                "amount": amount,
                "difference_from_completed": difference,
                "matches_completed": matches,
                "status": "PASS" if matches else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def build_analysis_tables(
    processed_data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """완료 주문 기준 핵심 분석표와 검증 Evidence를 생성합니다."""
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

    # 날짜 오류를 조용히 제거하지 않습니다. NaT를 유지한 뒤 Validation에서 실패로 처리합니다.
    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce",
    )
    orders["order_month"] = orders["order_date"].dt.to_period("M").astype("string")

    # 저장된 line_total이 있더라도 계산 관계를 다시 검증합니다.
    line_total_check, expected_line_total = _build_line_total_check(order_items)
    if line_total_check.loc[0, "status"] != "PASS":
        raise ValueError(
            "line_total 검증 실패: quantity × unit_price와 일치하지 않는 행이 있습니다."
        )
    order_items["line_total"] = expected_line_total

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

    completed_order_sales = order_sales.loc[
        order_sales["order_status"].eq("completed")
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
        .groupby("category", as_index=False, dropna=False)
        .agg(
            total_quantity=("quantity", "sum"),
            total_sales=("line_total", "sum"),
        )
        .sort_values("total_sales", ascending=False)
        .reset_index(drop=True)
    )
    category_total = float(category_sales["total_sales"].sum())
    if category_total:
        category_sales["sales_ratio"] = (
            category_sales["total_sales"] / category_total * 100
        ).round(2)
    else:
        category_sales["sales_ratio"] = 0.0

    monthly_sales = (
        completed_order_sales.dropna(subset=["order_month"])
        .groupby("order_month", as_index=False)
        .agg(
            total_sales=("line_total", "sum"),
            order_count=("order_id", "nunique"),
        )
        .sort_values("order_month")
        .reset_index(drop=True)
    )
    monthly_sales["avg_order_value"] = (
        monthly_sales["total_sales"]
        / monthly_sales["order_count"].replace(0, pd.NA)
    ).round(0)

    customer_sales = (
        completed_order_sales
        .groupby("customer_id", as_index=False, dropna=False)
        .agg(
            order_count=("order_id", "nunique"),
            total_sales=("line_total", "sum"),
        )
        .sort_values("total_sales", ascending=False)
        .reset_index(drop=True)
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
    customer_sales = customer_sales.sort_values(
        "total_sales",
        ascending=False,
    ).reset_index(drop=True)
    customer_sales["customer_label"] = [
        f"Customer {rank:02d}"
        for rank in range(1, len(customer_sales) + 1)
    ]
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
    customer_sales_public = customer_sales[PUBLIC_CUSTOMER_COLUMNS].copy()

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
                "excluded_non_completed",
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

    invalid_date_mask = completed_order_sales["order_date"].isna()
    date_checks = pd.DataFrame(
        [
            {
                "check": "completed rows with invalid order_date",
                "invalid_count": int(invalid_date_mask.sum()),
                "affected_amount": float(
                    completed_order_sales.loc[
                        invalid_date_mask,
                        "line_total",
                    ].sum()
                ),
                "status": "PASS" if int(invalid_date_mask.sum()) == 0 else "FAIL",
            }
        ]
    )

    total_consistency_check = _build_total_consistency_check(
        completed_order_sales,
        category_sales,
        monthly_sales,
        customer_sales,
    )

    return {
        "order_sales": order_sales,
        "completed_order_sales": completed_order_sales,
        "completed_sales_items": completed_sales_items,
        "category_sales": category_sales,
        "monthly_sales": monthly_sales,
        "customer_sales": customer_sales,
        "customer_sales_public": customer_sales_public,
        "order_status_summary": order_status_summary,
        "amount_scope_summary": amount_scope_summary,
        "merge_checks": merge_checks,
        "line_total_check": line_total_check,
        "date_checks": date_checks,
        "total_consistency_check": total_consistency_check,
    }


def build_project_validation(
    key_duplicate_checks: pd.DataFrame,
    relationship_checks: pd.DataFrame,
    analysis_tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """핵심 Gate를 하나의 PASS/FAIL 표로 정리합니다."""
    merge_checks = analysis_tables["merge_checks"]
    line_total_check = analysis_tables["line_total_check"]
    total_consistency = analysis_tables["total_consistency_check"]
    date_checks = analysis_tables["date_checks"]
    customer_public = analysis_tables["customer_sales_public"]
    category_sales = analysis_tables["category_sales"]
    completed_total = float(
        analysis_tables["completed_order_sales"]["line_total"].sum()
    )

    pk_pass = bool(key_duplicate_checks["status"].eq("PASS").all())
    fk_pass = bool(
        not relationship_checks.empty
        and relationship_checks["invalid_count"].fillna(1).eq(0).all()
    )
    merge_pass = bool(merge_checks["status"].eq("PASS").all())
    line_total_pass = bool(line_total_check["status"].eq("PASS").all())
    total_pass = bool(total_consistency["matches_completed"].all())
    date_pass = bool(date_checks["status"].eq("PASS").all())

    forbidden = sorted(
        FORBIDDEN_CUSTOMER_COLUMNS.intersection(customer_public.columns)
    )
    privacy_pass = len(forbidden) == 0

    ratio_sum = float(category_sales["sales_ratio"].sum())
    if np.isclose(completed_total, 0.0):
        ratio_pass = bool(np.isclose(ratio_sum, 0.0, atol=0.05))
        ratio_expected = 0.0
    else:
        ratio_pass = bool(np.isclose(ratio_sum, 100.0, atol=0.05))
        ratio_expected = 100.0

    rows = [
        {
            "check": "pk_integrity",
            "value": "all PASS" if pk_pass else "FAIL present",
            "expected": "all PASS",
            "status": "PASS" if pk_pass else "FAIL",
        },
        {
            "check": "fk_integrity",
            "value": int(relationship_checks["invalid_count"].sum())
            if not relationship_checks.empty
            else None,
            "expected": 0,
            "status": "PASS" if fk_pass else "FAIL",
        },
        {
            "check": "merge_checks_pass",
            "value": "all PASS" if merge_pass else "FAIL present",
            "expected": "all PASS",
            "status": "PASS" if merge_pass else "FAIL",
        },
        {
            "check": "line_total_consistency",
            "value": int(line_total_check["mismatch_count"].sum()),
            "expected": 0,
            "status": "PASS" if line_total_pass else "FAIL",
        },
        {
            "check": "completed_total_consistency",
            "value": "all match" if total_pass else "mismatch",
            "expected": "all match",
            "status": "PASS" if total_pass else "FAIL",
        },
        {
            "check": "category_sales_ratio_pct_sum",
            "value": ratio_sum,
            "expected": ratio_expected,
            "status": "PASS" if ratio_pass else "FAIL",
        },
        {
            "check": "completed_rows_with_invalid_order_date",
            "value": int(date_checks["invalid_count"].sum()),
            "expected": 0,
            "status": "PASS" if date_pass else "FAIL",
        },
        {
            "check": "public_customer_columns_safe",
            "value": ", ".join(forbidden) if forbidden else "no forbidden columns",
            "expected": "no forbidden columns",
            "status": "PASS" if privacy_pass else "FAIL",
        },
    ]
    return pd.DataFrame(rows)


def build_interpretation_notes() -> pd.DataFrame:
    """프로젝트 주요 결과의 관찰, 주의점, 다음 질문을 반환합니다."""
    return pd.DataFrame(
        {
            "analysis": [
                "카테고리별 completed 주문 기준 금액",
                "월별 completed 주문 기준 금액",
                "고객별 completed 주문 구매 금액",
                "주문 상태별 주문 수",
            ],
            "observation": [
                "completed 주문 기준 금액 비중이 높은 카테고리를 확인할 수 있습니다.",
                "시간에 따른 completed 주문 기준 금액의 증가와 감소를 확인할 수 있습니다.",
                "completed 주문 기준 구매 금액이 높은 고객군을 확인할 수 있습니다.",
                "완료, 취소, 환불 주문의 분포를 확인할 수 있습니다.",
            ],
            "caution": [
                "금액이 높은 이유가 판매 수량인지 단가인지 구분해야 합니다.",
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
    """중간 프로젝트 결과표와 검증 Evidence를 CSV 파일로 저장합니다."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    project_validation = build_project_validation(
        key_duplicate_checks,
        relationship_checks,
        analysis_tables,
    )

    outputs = {
        "ch08_dataset_summary.csv": dataset_summary,
        "ch08_preprocessing_comparison.csv": preprocessing_comparison,
        "ch08_key_duplicate_checks.csv": key_duplicate_checks,
        "ch08_relationship_checks.csv": relationship_checks,
        "ch08_merge_checks.csv": analysis_tables["merge_checks"],
        "ch08_line_total_check.csv": analysis_tables["line_total_check"],
        "ch08_date_checks.csv": analysis_tables["date_checks"],
        "ch08_amount_scope_summary.csv": analysis_tables[
            "amount_scope_summary"
        ],
        "ch08_total_consistency_check.csv": analysis_tables[
            "total_consistency_check"
        ],
        "ch08_project_validation.csv": project_validation,
        "ch08_category_sales.csv": analysis_tables["category_sales"],
        "ch08_monthly_sales.csv": analysis_tables["monthly_sales"],
        "ch08_customer_sales.csv": analysis_tables["customer_sales_public"],
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


def _save_figure(
    fig: plt.Figure,
    output_path: Path,
    show: bool = False,
) -> None:
    """Figure를 저장하고 필요하면 표시합니다."""
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def create_project_figures(
    analysis_tables: dict[str, pd.DataFrame],
    figure_dir: str | Path = "reports/figures",
    show: bool = False,
) -> list[Path]:
    """검증된 집계표에서 프로젝트 그래프 3개를 생성합니다."""
    setup_korean_font()
    output_dir = Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    category_sales = analysis_tables["category_sales"]
    monthly_sales = analysis_tables["monthly_sales"]
    customer_sales_public = analysis_tables["customer_sales_public"]

    category_path = output_dir / "ch08_category_sales.png"
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(
        category_sales["category"],
        category_sales["total_sales"],
    )
    ax.set_title("카테고리별 completed 주문 기준 금액")
    ax.set_xlabel("카테고리")
    ax.set_ylabel("금액")
    ax.set_ylim(bottom=0)
    ax.tick_params(axis="x", rotation=45)
    _save_figure(fig, category_path, show=show)

    monthly_path = output_dir / "ch08_monthly_sales.png"
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(
        monthly_sales["order_month"].astype(str),
        monthly_sales["total_sales"],
        marker="o",
    )
    ax.set_title("월별 completed 주문 기준 금액")
    ax.set_xlabel("주문 월")
    ax.set_ylabel("금액")
    ax.tick_params(axis="x", rotation=45)
    _save_figure(fig, monthly_path, show=show)

    top_customers = customer_sales_public.head(10).sort_values(
        "total_sales"
    )
    customer_path = output_dir / "ch08_top_customers.png"
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(
        top_customers["customer_label"],
        top_customers["total_sales"],
    )
    ax.set_title("completed 주문 기준 구매 금액 상위 익명 고객")
    ax.set_xlabel("금액")
    ax.set_ylabel("익명 고객")
    _save_figure(fig, customer_path, show=show)

    return [category_path, monthly_path, customer_path]


def build_midterm_report(
    dataset_summary: pd.DataFrame,
    preprocessing_comparison: pd.DataFrame,
    key_duplicate_checks: pd.DataFrame,
    relationship_checks: pd.DataFrame,
    analysis_tables: dict[str, pd.DataFrame],
    interpretation_notes: pd.DataFrame,
) -> str:
    """개인정보를 최소화하고 검증 Evidence를 포함한 Markdown 보고서를 생성합니다."""
    category_sales = analysis_tables["category_sales"]
    monthly_sales = analysis_tables["monthly_sales"]
    customer_report = analysis_tables["customer_sales_public"].head(10)
    order_status_summary = analysis_tables["order_status_summary"]
    amount_scope_summary = analysis_tables["amount_scope_summary"]
    merge_checks = analysis_tables["merge_checks"]
    line_total_check = analysis_tables["line_total_check"]
    date_checks = analysis_tables["date_checks"]
    total_consistency = analysis_tables["total_consistency_check"]
    project_validation = build_project_validation(
        key_duplicate_checks,
        relationship_checks,
        analysis_tables,
    )

    return f"""# Chapter 8 중간 프로젝트 보고서

## 1. 분석 목적

온라인 쇼핑몰 데이터를 사용해 completed 주문 기준 금액과 고객 구매 패턴을 분석했습니다.

## 2. 분석 기준

- 금액성 분석은 `order_status == \"completed\"`인 주문만 포함했습니다.
- `line_total = quantity × unit_price` 관계를 검증했습니다.
- 취소·환불 등 non-completed 주문을 포함한 금액은 전체 주문 상세 금액으로 구분했습니다.
- 공개 고객 결과에서는 이름·연락처·원본 고객 ID를 제외하고 순위 기반 익명 라벨을 사용했습니다.
- 병합은 관계 검증, `validate`, 행 수, 미매칭을 확인했습니다.
- 같은 completed 범위의 카테고리·월·고객 총합을 source total과 대조했습니다.

## 3. 데이터 개요

```text
{dataset_summary.to_string(index=False)}
```

## 4. 전처리 전후 비교

```text
{preprocessing_comparison.to_string(index=False)}
```

## 5. 키와 관계 점검

### PK

```text
{key_duplicate_checks.to_string(index=False)}
```

### FK

```text
{relationship_checks.to_string(index=False)}
```

### 병합

```text
{merge_checks.to_string(index=False)}
```

## 6. line_total과 날짜 검증

```text
{line_total_check.to_string(index=False)}
```

```text
{date_checks.to_string(index=False)}
```

## 7. 전체 주문 상세 금액과 completed 주문 기준 금액

```text
{amount_scope_summary.to_string(index=False)}
```

## 8. total consistency

```text
{total_consistency.to_string(index=False)}
```

## 9. 최종 Validation

```text
{project_validation.to_string(index=False)}
```

## 10. 카테고리별 completed 주문 기준 금액

```text
{category_sales.to_string(index=False)}
```

## 11. 월별 completed 주문 기준 금액

```text
{monthly_sales.to_string(index=False)}
```

## 12. completed 주문 구매 금액 상위 익명 고객

```text
{customer_report.to_string(index=False)}
```

## 13. 주문 상태별 주문 수

```text
{order_status_summary.to_string(index=False)}
```

## 14. 해석 메모

```text
{interpretation_notes.to_string(index=False)}
```

## 15. 한계점

- 현재 데이터만으로 고객 만족도나 이탈 이유를 분석할 수 없습니다.
- 금액 변동의 원인을 설명하려면 프로모션, 광고, 재고, 계절성 데이터가 필요합니다.
- completed 주문 기준 금액은 실제 회계상 순매출과 같은 의미라고 단정하지 않습니다.
- 고객별 결과는 익명화된 분석용 요약이며 개인을 평가하는 용도로 사용하면 안 됩니다.
- 자동 Validation PASS는 정해 둔 구조·수치 검증을 통과했다는 뜻이며 해석의 타당성은 사람이 별도로 확인해야 합니다.

## 16. 다음 단계

- 카테고리별 판매 수량과 평균 판매 단가를 함께 비교합니다.
- 월별 주문 수와 평균 주문 금액의 변화를 분리해 확인합니다.
- 고객별 최근 구매일과 구매 빈도를 추가합니다.
- 주문 취소율과 환불률의 월별 변화를 분석합니다.
"""


def _validate_saved_public_customer_csv(path: Path) -> None:
    """저장된 공개 고객 CSV에 금지 컬럼이 없는지 다시 확인합니다."""
    saved = pd.read_csv(path)
    forbidden = sorted(
        FORBIDDEN_CUSTOMER_COLUMNS.intersection(saved.columns)
    )
    if forbidden:
        raise ValueError(
            "저장된 공개 고객 CSV에 금지 컬럼이 있습니다: "
            f"{forbidden}"
        )


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
    key_duplicate_checks = build_key_duplicate_checks(processed_data)
    relationship_checks = validate_relationships(processed_data).copy()
    if not relationship_checks.empty:
        relationship_checks["status"] = relationship_checks[
            "invalid_count"
        ].eq(0).map({True: "PASS", False: "FAIL"})

    # PK/FK 오류를 정상 완료로 처리하지 않습니다.
    if not key_duplicate_checks["status"].eq("PASS").all():
        raise ValueError("PK Validation 실패")
    if (
        relationship_checks.empty
        or not relationship_checks["invalid_count"].eq(0).all()
    ):
        raise ValueError("FK Validation 실패")

    analysis_tables = build_analysis_tables(processed_data)
    project_validation = build_project_validation(
        key_duplicate_checks,
        relationship_checks,
        analysis_tables,
    )
    analysis_tables["project_validation"] = project_validation

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

    output_report_dir = Path(report_dir)
    customer_csv = output_report_dir / "ch08_customer_sales.csv"
    _validate_saved_public_customer_csv(customer_csv)

    saved_figures = create_project_figures(
        analysis_tables,
        figure_dir,
        show=show_figures,
    )

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

    failed_checks = project_validation.loc[
        project_validation["status"].eq("FAIL"),
        "check",
    ].tolist()
    if failed_checks:
        raise ValueError(
            "Chapter 08 프로젝트 Validation 실패: "
            + ", ".join(failed_checks)
        )

    return {
        "raw_data": raw_data,
        "processed_data": processed_data,
        "dataset_summary": dataset_summary,
        "preprocessing_comparison": preprocessing_comparison,
        "key_duplicate_checks": key_duplicate_checks,
        "relationship_checks": relationship_checks,
        "analysis_tables": analysis_tables,
        "project_validation": project_validation,
        "interpretation_notes": interpretation_notes,
        "saved_tables": saved_tables,
        "saved_figures": saved_figures,
        "report_path": report_path,
    }
