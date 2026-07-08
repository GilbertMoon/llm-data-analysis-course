"""Chapter 7 데이터 시각화 공통 함수 모음.

7장 노트북과 실행 스크립트에서 함께 사용할 matplotlib 기반 시각화 함수입니다.
그래프는 reports/figures 폴더에 저장할 수 있도록 구성했습니다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.eda import load_processed_sales_data, prepare_eda_data


FIGURE_FILENAMES = {
    "category_sales": "ch07_category_sales_bar.png",
    "monthly_sales": "ch07_monthly_sales_line.png",
    "product_price": "ch07_product_price_hist.png",
    "price_quantity": "ch07_price_quantity_scatter.png",
    "top_customers": "ch07_top_customers_barh.png",
    "order_status": "ch07_order_status_bar.png",
}


def setup_korean_font(font_family: str = "Malgun Gothic") -> None:
    """matplotlib 한글 폰트와 음수 기호 설정을 적용합니다.

    Windows는 Malgun Gothic, macOS는 AppleGothic, Linux는 NanumGothic 등을 사용할 수 있습니다.
    설치되지 않은 폰트를 지정하면 실행 환경에 따라 경고가 표시될 수 있습니다.
    """
    plt.rcParams["font.family"] = font_family
    plt.rcParams["axes.unicode_minus"] = False


def ensure_figure_dir(figure_dir: str | Path = "reports/figures") -> Path:
    """그래프 저장 폴더를 생성하고 Path 객체로 반환합니다."""
    path = Path(figure_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_visualization_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """전처리 데이터를 불러와 7장 시각화에 필요한 집계표를 생성합니다."""
    data = prepare_eda_data(load_processed_sales_data(processed_dir))

    customers = data["customers"]
    products = data["products"]
    orders = data["orders"]
    order_items = data["order_items"]

    sales_items = order_items.merge(products, on="product_id", how="left")

    category_sales = (
        sales_items.groupby("category", as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    category_sales["sales_ratio"] = (
        category_sales["total_sales"] / category_sales["total_sales"].sum() * 100
    ).round(2)

    order_sales = order_items.merge(orders, on="order_id", how="left")
    order_sales["order_date"] = pd.to_datetime(order_sales["order_date"], errors="coerce")
    order_sales["order_month"] = order_sales["order_date"].dt.to_period("M").astype(str)

    monthly_sales = (
        order_sales.groupby("order_month", as_index=False)
        .agg(total_sales=("line_total", "sum"), order_count=("order_id", "nunique"))
        .sort_values("order_month")
    )

    product_sales = (
        sales_items.groupby(["product_id", "product_name", "category", "price"], as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
    )

    customer_sales_base = order_sales.merge(customers, on="customer_id", how="left")
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

    order_status = orders["order_status"].value_counts(dropna=False).reset_index()
    order_status.columns = ["order_status", "order_count"]

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
        "sales_items": sales_items,
        "category_sales": category_sales,
        "order_sales": order_sales,
        "monthly_sales": monthly_sales,
        "product_sales": product_sales,
        "customer_sales": customer_sales,
        "order_status": order_status,
    }


def _save_or_show(output_path: str | Path | None = None, show: bool = True) -> None:
    """현재 matplotlib Figure를 저장하거나 화면에 표시합니다."""
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close()


def plot_category_sales(
    category_sales: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = True,
) -> None:
    """카테고리별 매출 막대그래프를 그립니다."""
    plt.figure(figsize=(10, 5))
    plt.bar(category_sales["category"], category_sales["total_sales"])
    plt.title("카테고리별 매출")
    plt.xlabel("카테고리")
    plt.ylabel("총매출")
    plt.xticks(rotation=45)
    _save_or_show(output_path, show=show)


def plot_monthly_sales(
    monthly_sales: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = True,
) -> None:
    """월별 매출 선 그래프를 그립니다."""
    plt.figure(figsize=(10, 5))
    plt.plot(monthly_sales["order_month"], monthly_sales["total_sales"], marker="o")
    plt.title("월별 매출 추이")
    plt.xlabel("주문 월")
    plt.ylabel("총매출")
    plt.xticks(rotation=45)
    _save_or_show(output_path, show=show)


def plot_product_price_hist(
    products: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = True,
    bins: int = 20,
) -> None:
    """상품 가격 분포 히스토그램을 그립니다."""
    plt.figure(figsize=(10, 5))
    plt.hist(products["price"], bins=bins)
    plt.title("상품 가격 분포")
    plt.xlabel("상품 가격")
    plt.ylabel("상품 수")
    _save_or_show(output_path, show=show)


def plot_price_quantity_scatter(
    product_sales: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = True,
) -> None:
    """상품 가격과 판매 수량의 관계를 산점도로 그립니다."""
    plt.figure(figsize=(10, 5))
    plt.scatter(product_sales["price"], product_sales["total_quantity"], alpha=0.6)
    plt.title("상품 가격과 판매 수량의 관계")
    plt.xlabel("상품 가격")
    plt.ylabel("총 판매 수량")
    _save_or_show(output_path, show=show)


def plot_top_customers(
    customer_sales: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = True,
    top_n: int = 10,
    anonymize: bool = True,
) -> None:
    """구매 금액 상위 고객을 가로 막대그래프로 그립니다.

    기본값은 개인정보 보호를 위해 고객명을 사용하지 않고 Customer ID 라벨을 사용합니다.
    """
    top_customers = customer_sales.head(top_n).copy()

    if anonymize:
        top_customers["customer_label"] = "Customer " + top_customers["customer_id"].astype(str)
    elif "name" in top_customers.columns:
        top_customers["customer_label"] = top_customers["name"]
    else:
        top_customers["customer_label"] = "Customer " + top_customers["customer_id"].astype(str)

    top_customers = top_customers.sort_values("total_sales")

    plt.figure(figsize=(10, 6))
    plt.barh(top_customers["customer_label"], top_customers["total_sales"])
    plt.title("구매 금액 상위 10명 고객")
    plt.xlabel("총 구매 금액")
    plt.ylabel("고객")
    _save_or_show(output_path, show=show)


def plot_order_status(
    order_status: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = True,
) -> None:
    """주문 상태별 주문 수 막대그래프를 그립니다."""
    plt.figure(figsize=(8, 5))
    plt.bar(order_status["order_status"], order_status["order_count"])
    plt.title("주문 상태별 주문 수")
    plt.xlabel("주문 상태")
    plt.ylabel("주문 수")
    _save_or_show(output_path, show=show)


def create_visualization_summary() -> pd.DataFrame:
    """7장에서 생성하는 그래프 목록과 해석 포인트를 반환합니다."""
    return pd.DataFrame(
        {
            "chart": [
                "카테고리별 매출 막대그래프",
                "월별 매출 선 그래프",
                "상품 가격 분포 히스토그램",
                "상품 가격과 판매 수량 산점도",
                "구매 금액 상위 고객 가로 막대그래프",
                "주문 상태별 주문 수 막대그래프",
            ],
            "question": [
                "카테고리별 매출은 어떻게 다른가?",
                "월별 매출은 어떻게 변하는가?",
                "상품 가격은 어떤 구간에 몰려 있는가?",
                "상품 가격과 판매 수량은 관계가 있는가?",
                "구매 금액이 높은 고객은 누구인가?",
                "주문 상태별 주문 수는 어떻게 다른가?",
            ],
            "interpretation_point": [
                "매출 기여도가 높은 카테고리 확인",
                "시간에 따른 증가와 감소 흐름 확인",
                "상품 가격대의 분포와 이상값 후보 확인",
                "가격과 판매 수량의 관계 탐색",
                "우수 고객 후보 확인",
                "완료, 취소 등 주문 상태 분포 확인",
            ],
            "file_name": list(FIGURE_FILENAMES.values()),
        }
    )


def create_all_figures(
    data: dict[str, pd.DataFrame],
    figure_dir: str | Path = "reports/figures",
    show: bool = False,
) -> list[Path]:
    """7장 주요 그래프 6개를 생성하고 저장 경로 목록을 반환합니다."""
    output_dir = ensure_figure_dir(figure_dir)

    paths = {
        key: output_dir / filename for key, filename in FIGURE_FILENAMES.items()
    }

    plot_category_sales(data["category_sales"], paths["category_sales"], show=show)
    plot_monthly_sales(data["monthly_sales"], paths["monthly_sales"], show=show)
    plot_product_price_hist(data["products"], paths["product_price"], show=show)
    plot_price_quantity_scatter(data["product_sales"], paths["price_quantity"], show=show)
    plot_top_customers(data["customer_sales"], paths["top_customers"], show=show)
    plot_order_status(data["order_status"], paths["order_status"], show=show)

    return list(paths.values())


def build_visualization_report(summary: pd.DataFrame) -> str:
    """시각화 결과 요약 Markdown 문자열을 생성합니다."""
    return f"""# Chapter 7 데이터 시각화 요약 보고서

## 1. 시각화 목적

전처리 및 EDA 결과를 바탕으로 온라인 쇼핑몰 데이터의 주요 패턴을 그래프로 확인했습니다.

## 2. 생성한 그래프 목록

```text
{summary.to_string(index=False)}
```

## 3. 주요 해석 포인트

- 카테고리별 매출 그래프를 통해 매출 기여도가 높은 상품군을 확인할 수 있습니다.
- 월별 매출 선 그래프를 통해 시간에 따른 매출 흐름을 확인할 수 있습니다.
- 상품 가격 히스토그램을 통해 상품 가격대 분포를 확인할 수 있습니다.
- 가격과 판매 수량 산점도는 두 변수 사이의 관계를 탐색하는 데 사용합니다.
- 고객별 구매 금액 상위 그래프는 우수 고객 후보를 파악하는 데 유용합니다.
- 주문 상태별 주문 수 그래프는 완료, 취소 등 주문 상태의 분포를 확인하는 데 사용합니다.

## 4. 해석 시 주의사항

- 그래프는 데이터를 쉽게 보여주지만 원인을 자동으로 설명하지는 않습니다.
- 매출이 높은 이유는 판매 수량, 단가, 주문 수 등을 함께 확인해야 합니다.
- 고객명 등 개인정보가 포함될 수 있는 그래프는 익명화가 필요할 수 있습니다.
- 시각화 결과는 보고서에 넣기 전에 축, 제목, 단위가 명확한지 확인해야 합니다.

## 5. 다음 단계

다음 장에서는 지금까지 배운 데이터 불러오기, 전처리, EDA, 시각화를 종합하여 중간 실습 프로젝트를 수행합니다.
"""
