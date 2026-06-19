import pandas as pd


def add_item_sales(order_items: pd.DataFrame) -> pd.DataFrame:
    """주문 상세 데이터에 판매금액 컬럼을 추가합니다."""
    result = order_items.copy()
    result["sales_amount"] = result["quantity"] * result["unit_price"]
    return result


def summarize_sales(order_items: pd.DataFrame) -> pd.DataFrame:
    """전체 주문 상세 데이터에서 총 판매수량과 총 매출을 집계합니다."""
    items = add_item_sales(order_items)
    return pd.DataFrame(
        {
            "total_quantity": [items["quantity"].sum()],
            "total_sales": [items["sales_amount"].sum()],
            "order_item_count": [len(items)],
        }
    )


def customer_sales_summary(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """고객별 구매금액과 주문 횟수를 집계합니다."""
    items = add_item_sales(order_items)
    merged = (
        orders.merge(items, on="order_id", how="left")
        .merge(customers, on="customer_id", how="left")
    )
    return (
        merged.groupby(["customer_id", "name"], as_index=False)
        .agg(order_count=("order_id", "nunique"), total_sales=("sales_amount", "sum"))
        .sort_values("total_sales", ascending=False)
    )


def category_sales_summary(
    products: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """상품 카테고리별 판매금액을 집계합니다."""
    items = add_item_sales(order_items)
    merged = items.merge(products, on="product_id", how="left")
    return (
        merged.groupby("category", as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("sales_amount", "sum"))
        .sort_values("total_sales", ascending=False)
    )
