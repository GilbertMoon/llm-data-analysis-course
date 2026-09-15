"""Chapter 7 데이터 시각화 공통 함수 모음.

7장 노트북과 실행 스크립트에서 함께 사용할 matplotlib 기반 시각화 함수입니다.
금액성 시각화는 기본적으로 완료 주문(order_status == "completed") 범위를 사용하고,
그래프는 reports/figures 폴더에 저장할 수 있도록 구성합니다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

from src.eda import load_processed_sales_data, prepare_eda_data


FIGURE_FILENAMES = {
    "category_sales": "ch07_category_completed_amount_bar.png",
    "monthly_sales": "ch07_monthly_completed_amount_line.png",
    "product_price": "ch07_product_price_hist.png",
    "price_quantity": "ch07_price_completed_quantity_scatter.png",
    "top_customers": "ch07_top_customers_anonymized_barh.png",
    "order_status": "ch07_order_status_bar.png",
}

REQUIRED_COLUMNS = {
    "customers": {"customer_id"},
    "products": {"product_id", "product_name", "category", "price"},
    "orders": {"order_id", "customer_id", "order_date", "order_status"},
    "order_items": {"order_id", "product_id", "quantity", "unit_price"},
}

MONEY_FORMATTER = FuncFormatter(lambda value, position: f"{value:,.0f}")


def setup_korean_font(font_family: str | None = None) -> str | None:
    """설치된 한글 폰트를 선택하고 음수 기호 설정을 적용합니다."""
    installed = {font.name for font in font_manager.fontManager.ttflist}
    candidates = []
    if font_family:
        candidates.append(font_family)
    candidates.extend(
        ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"]
    )
    selected = next((name for name in candidates if name in installed), None)
    if selected:
        plt.rcParams["font.family"] = selected
    plt.rcParams["axes.unicode_minus"] = False
    return selected


def ensure_figure_dir(figure_dir: str | Path = "reports/figures") -> Path:
    path = Path(figure_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _require_columns(data: dict[str, pd.DataFrame]) -> None:
    for name, required in REQUIRED_COLUMNS.items():
        missing = required - set(data[name].columns)
        if missing:
            raise KeyError(f"{name}에 필요한 컬럼이 없습니다: {sorted(missing)}")


def _check_unique_key(df: pd.DataFrame, key: str, label: str) -> None:
    missing_count = int(df[key].isna().sum())
    duplicate_count = int(df[key].duplicated().sum())
    if missing_count or duplicate_count:
        raise ValueError(
            f"{label}.{key} 품질 오류: missing={missing_count}, "
            f"duplicate={duplicate_count}"
        )


def prepare_visualization_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """검증된 Chapter 7 시각화용 데이터와 집계표를 생성합니다."""
    data = prepare_eda_data(load_processed_sales_data(processed_dir))
    _require_columns(data)

    customers = data["customers"].copy()
    products = data["products"].copy()
    orders = data["orders"].copy()
    order_items = data["order_items"].copy()

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")

    for dataframe, column in [
        (products, "price"),
        (order_items, "quantity"),
        (order_items, "unit_price"),
    ]:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    if "line_total" not in order_items.columns:
        order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]
    else:
        order_items["line_total"] = pd.to_numeric(
            order_items["line_total"], errors="coerce"
        )

    numeric_failures = {
        "products.price": int(products["price"].isna().sum()),
        "order_items.quantity": int(order_items["quantity"].isna().sum()),
        "order_items.unit_price": int(order_items["unit_price"].isna().sum()),
        "order_items.line_total": int(order_items["line_total"].isna().sum()),
    }
    if any(numeric_failures.values()):
        raise ValueError(f"숫자형 변환 실패가 남아 있습니다: {numeric_failures}")

    _check_unique_key(orders, "order_id", "orders")
    _check_unique_key(products, "product_id", "products")
    _check_unique_key(customers, "customer_id", "customers")

    order_sales = order_items.merge(
        orders[["order_id", "customer_id", "order_date", "order_status"]],
        on="order_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    unmatched_orders = order_sales.loc[order_sales["_merge"].ne("both")].copy()
    if not unmatched_orders.empty:
        raise ValueError(
            "주문 정보와 연결되지 않은 주문 상세가 있습니다: "
            f"{len(unmatched_orders)}행"
        )
    order_sales = order_sales.drop(columns="_merge")

    completed_order_sales = order_sales.loc[
        order_sales["order_status"].eq("completed")
    ].copy()
    if completed_order_sales.empty:
        raise ValueError("완료 주문이 없어 금액 시각화를 생성할 수 없습니다.")

    completed_sales_items = completed_order_sales.merge(
        products[["product_id", "product_name", "category", "price"]],
        on="product_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    unmatched_products = completed_sales_items.loc[
        completed_sales_items["_merge"].ne("both")
    ].copy()
    if not unmatched_products.empty:
        raise ValueError(
            "상품 정보와 연결되지 않은 완료 주문 상세가 있습니다: "
            f"{len(unmatched_products)}행"
        )
    completed_sales_items = completed_sales_items.drop(columns="_merge")

    category_sales = (
        completed_sales_items.groupby("category", as_index=False, dropna=False)
        .agg(
            total_quantity=("quantity", "sum"),
            completed_amount=("line_total", "sum"),
        )
        .sort_values("completed_amount", ascending=False)
    )
    completed_total = float(completed_order_sales["line_total"].sum())
    category_sales["amount_ratio_pct"] = (
        category_sales["completed_amount"].div(completed_total).mul(100).round(2)
    )

    invalid_date_sales = completed_order_sales.loc[
        completed_order_sales["order_date"].isna()
    ].copy()
    valid_date_sales = completed_order_sales.dropna(subset=["order_date"]).copy()

    monthly_sales = (
        valid_date_sales.assign(
            order_month=lambda df: df["order_date"].dt.to_period("M")
        )
        .groupby("order_month", as_index=False)
        .agg(
            completed_amount=("line_total", "sum"),
            completed_order_count=("order_id", "nunique"),
        )
        .sort_values("order_month")
    )
    monthly_sales["month_start"] = monthly_sales["order_month"].dt.to_timestamp()
    monthly_sales["average_completed_order_amount"] = (
        monthly_sales["completed_amount"]
        .div(monthly_sales["completed_order_count"])
        .round(0)
    )

    product_sales = (
        completed_sales_items.groupby(
            ["product_id", "product_name", "category", "price"],
            as_index=False,
            dropna=False,
        )
        .agg(
            completed_quantity=("quantity", "sum"),
            completed_amount=("line_total", "sum"),
        )
        .sort_values("completed_amount", ascending=False)
    )

    customer_sales = (
        completed_order_sales.groupby("customer_id", as_index=False)
        .agg(
            completed_order_count=("order_id", "nunique"),
            completed_amount=("line_total", "sum"),
        )
        .sort_values("completed_amount", ascending=False)
    )
    customer_sales["average_completed_order_amount"] = (
        customer_sales["completed_amount"]
        .div(customer_sales["completed_order_count"])
        .round(0)
    )

    order_status = (
        orders["order_status"]
        .fillna("missing")
        .value_counts()
        .rename_axis("order_status")
        .reset_index(name="order_count")
    )

    valid_date_total = float(valid_date_sales["line_total"].sum())
    validation = pd.DataFrame(
        [
            {
                "check": "category_completed_amount",
                "expected": completed_total,
                "actual": float(category_sales["completed_amount"].sum()),
            },
            {
                "check": "product_completed_amount",
                "expected": completed_total,
                "actual": float(product_sales["completed_amount"].sum()),
            },
            {
                "check": "customer_completed_amount",
                "expected": completed_total,
                "actual": float(customer_sales["completed_amount"].sum()),
            },
            {
                "check": "monthly_completed_amount_valid_dates",
                "expected": valid_date_total,
                "actual": float(monthly_sales["completed_amount"].sum()),
            },
        ]
    )
    validation["difference"] = validation["actual"] - validation["expected"]
    validation["passed"] = validation["difference"].abs().le(1e-6)
    if not validation["passed"].all():
        raise ValueError(
            "시각화용 집계 총합 검증에 실패했습니다:\n"
            + validation.to_string(index=False)
        )

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
        "order_sales": order_sales,
        "completed_order_sales": completed_order_sales,
        "completed_sales_items": completed_sales_items,
        "category_sales": category_sales,
        "monthly_sales": monthly_sales,
        "product_sales": product_sales,
        "customer_sales": customer_sales,
        "order_status": order_status,
        "invalid_date_sales": invalid_date_sales,
        "visualization_validation": validation,
    }


def _save_or_show(
    fig,
    output_path: str | Path | None = None,
    *,
    show: bool = True,
    dpi: int = 150,
) -> Path | None:
    fig.tight_layout()
    saved_path = None
    if output_path is not None:
        saved_path = Path(output_path)
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(saved_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return saved_path


def plot_category_sales(category_sales, output_path=None, show=True):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(category_sales["category"], category_sales["completed_amount"])
    ax.set_title("카테고리별 완료 주문 금액")
    ax.set_xlabel("카테고리")
    ax.set_ylabel("완료 주문 금액")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(MONEY_FORMATTER)
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    return _save_or_show(fig, output_path, show=show)


def plot_monthly_sales(monthly_sales, output_path=None, show=True):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(monthly_sales["month_start"], monthly_sales["completed_amount"], marker="o")
    ax.set_title("월별 완료 주문 금액 추이")
    ax.set_xlabel("주문 월")
    ax.set_ylabel("완료 주문 금액")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(MONEY_FORMATTER)
    ax.grid(axis="y", alpha=0.3)
    fig.autofmt_xdate()
    return _save_or_show(fig, output_path, show=show)


def plot_product_price_hist(products, output_path=None, show=True, bins=20):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(products["price"].dropna(), bins=bins, edgecolor="black")
    ax.set_title("상품 가격 분포")
    ax.set_xlabel("상품 가격")
    ax.set_ylabel("상품 수")
    ax.set_xlim(left=0)
    ax.xaxis.set_major_formatter(MONEY_FORMATTER)
    return _save_or_show(fig, output_path, show=show)


def plot_price_quantity_scatter(product_sales, output_path=None, show=True):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(
        product_sales["price"],
        product_sales["completed_quantity"],
        alpha=0.6,
    )
    ax.set_title("상품 가격과 완료 주문 판매 수량의 관계")
    ax.set_xlabel("상품 가격")
    ax.set_ylabel("완료 주문 판매 수량")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(MONEY_FORMATTER)
    ax.grid(alpha=0.2)
    return _save_or_show(fig, output_path, show=show)


def plot_top_customers(customer_sales, output_path=None, show=True, top_n=10):
    top = customer_sales.head(top_n).sort_values("completed_amount").copy()
    top["customer_label"] = [
        f"고객 {rank:02d}" for rank in range(len(top), 0, -1)
    ]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top["customer_label"], top["completed_amount"])
    ax.set_title("완료 주문 구매 금액 상위 고객")
    ax.set_xlabel("완료 주문 구매 금액")
    ax.set_ylabel("익명 고객")
    ax.set_xlim(left=0)
    ax.xaxis.set_major_formatter(MONEY_FORMATTER)
    return _save_or_show(fig, output_path, show=show)


def plot_order_status(order_status, output_path=None, show=True):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(order_status["order_status"], order_status["order_count"])
    ax.set_title("주문 상태별 주문 수")
    ax.set_xlabel("주문 상태")
    ax.set_ylabel("주문 수")
    ax.set_ylim(bottom=0)
    ax.tick_params(axis="x", rotation=30)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    return _save_or_show(fig, output_path, show=show)


def create_visualization_summary() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "chart": [
                "카테고리별 완료 주문 금액",
                "월별 완료 주문 금액",
                "상품 가격 분포",
                "상품 가격과 완료 주문 판매 수량",
                "완료 주문 구매 금액 상위 고객",
                "주문 상태별 주문 수",
            ],
            "question": [
                "카테고리별 완료 주문 금액은 어떻게 다른가?",
                "월별 완료 주문 금액은 어떻게 변하는가?",
                "상품 가격은 어떤 구간에 몰려 있는가?",
                "상품 가격과 완료 주문 판매 수량은 어떤 패턴을 보이는가?",
                "완료 주문 구매 금액 상위 고객군은 어떻게 구성되는가?",
                "주문 상태별 주문 수는 어떻게 다른가?",
            ],
            "scope": [
                "completed orders",
                "completed orders + valid order_date",
                "product master",
                "completed orders aggregated by product",
                "completed orders aggregated by customer",
                "all orders",
            ],
            "interpretation_point": [
                "금액 차이는 수량·단가 등 추가 지표로 확인",
                "증감은 관찰이며 원인은 추가 데이터 필요",
                "상품 구성 분포이며 판매 선호를 의미하지 않음",
                "관계는 인과를 의미하지 않음",
                "Top N이며 충성도를 자동 의미하지 않음",
                "상태 분포만으로 취소·환불 원인을 알 수 없음",
            ],
            "file_name": list(FIGURE_FILENAMES.values()),
        }
    )


def create_all_figures(
    data: dict[str, pd.DataFrame],
    figure_dir: str | Path = "reports/figures",
    show: bool = False,
) -> list[Path]:
    output_dir = ensure_figure_dir(figure_dir)
    paths = {key: output_dir / name for key, name in FIGURE_FILENAMES.items()}
    plot_category_sales(data["category_sales"], paths["category_sales"], show=show)
    plot_monthly_sales(data["monthly_sales"], paths["monthly_sales"], show=show)
    plot_product_price_hist(data["products"], paths["product_price"], show=show)
    plot_price_quantity_scatter(
        data["product_sales"], paths["price_quantity"], show=show
    )
    plot_top_customers(data["customer_sales"], paths["top_customers"], show=show)
    plot_order_status(data["order_status"], paths["order_status"], show=show)
    return list(paths.values())


def build_visualization_report(summary: pd.DataFrame) -> str:
    return f"""# Chapter 7 데이터 시각화 요약 보고서

## 1. 시각화 목적

전처리된 온라인 쇼핑몰 데이터를 사용해 질문에 맞는 그래프를 만들고 축·범위·해석을 검증했습니다.

## 2. 생성한 그래프 목록

```text
{summary.to_string(index=False)}
```

## 3. 분석 범위

- 카테고리·월·상품·고객 금액성 그래프는 `order_status == "completed"` 범위를 사용합니다.
- 상품 가격 히스토그램은 주문 상태와 무관한 상품 마스터 가격 분포입니다.
- 주문 상태별 주문 수 그래프는 전체 주문을 사용합니다.
- `line_total`은 주문 상세의 `quantity × unit_price`이며 회계상 순매출로 단정하지 않습니다.

## 4. 주요 해석 원칙

- 카테고리별 완료 주문 금액 차이는 판매 수량·단가 등 추가 지표와 함께 봅니다.
- 월별 증감은 관찰이며 프로모션·계절성 같은 원인은 추가 데이터가 필요합니다.
- 가격 분포는 상품 구성을 보여 주며 고객 선호를 직접 의미하지 않습니다.
- 가격과 판매 수량의 관계는 인과관계를 의미하지 않습니다.
- 상위 고객 그래프는 Top N 일부이며 익명 라벨을 사용합니다.
- 주문 상태별 건수만으로 취소·환불 원인을 알 수 없습니다.

## 5. 다음 단계

다음 장에서는 검증된 집계표와 그래프를 작은 데이터 분석 프로젝트로 연결합니다.
"""
