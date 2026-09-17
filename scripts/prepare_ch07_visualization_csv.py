"""Chapter 07 시각화용 통합 CSV 생성 스크립트.

입력:
    data/processed/customers_clean.csv
    data/processed/products_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

출력:
    data/processed/visualization.csv

정의:
- 한 행 = order_item_id 1건
- 고객 이름(name)은 공개 시각화용 통합 파일에서 제외
- 주문/상품/고객 병합 성공 여부를 별도 컬럼으로 기록
- 관계 오류를 조용히 제거하지 않고 left merge로 보존
"""

from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")
OUTPUT_PATH = PROCESSED_DIR / "visualization.csv"


REQUIRED_FILES = {
    "customers": "customers_clean.csv",
    "products": "products_clean.csv",
    "orders": "orders_clean.csv",
    "order_items": "order_items_clean.csv",
}


def load_processed_data() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for name, filename in REQUIRED_FILES.items():
        path = PROCESSED_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"필수 processed 파일이 없습니다: {path}\n"
                "먼저 python scripts/preprocess_data.py 를 실행하세요."
            )
        data[name] = pd.read_csv(path)
    return data


def require_columns(df: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise KeyError(f"{label}에 필요한 컬럼이 없습니다: {missing}")


def build_visualization_dataset(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    customers = data["customers"].copy()
    products = data["products"].copy()
    orders = data["orders"].copy()
    order_items = data["order_items"].copy()

    require_columns(
        customers,
        ["customer_id", "gender", "age", "city", "signup_date"],
        "customers",
    )
    require_columns(
        products,
        ["product_id", "product_name", "category", "price"],
        "products",
    )
    require_columns(
        orders,
        [
            "order_id",
            "customer_id",
            "order_date",
            "payment_method",
            "order_status",
            "order_month",
            "order_dayofweek",
        ],
        "orders",
    )
    require_columns(
        order_items,
        [
            "order_item_id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "line_total",
        ],
        "order_items",
    )

    if order_items["order_item_id"].isna().any() or order_items["order_item_id"].duplicated().any():
        raise ValueError("order_items.order_item_id는 결측/중복 없이 고유해야 합니다.")

    merged = order_items.merge(
        orders[
            [
                "order_id",
                "customer_id",
                "order_date",
                "payment_method",
                "order_status",
                "order_month",
                "order_dayofweek",
            ]
        ],
        on="order_id",
        how="left",
        validate="many_to_one",
        indicator="_order_merge",
    )
    merged["order_match"] = merged["_order_merge"].eq("both")
    merged = merged.drop(columns="_order_merge")

    merged = merged.merge(
        products[["product_id", "product_name", "category", "price"]],
        on="product_id",
        how="left",
        validate="many_to_one",
        indicator="_product_merge",
    )
    merged["product_match"] = merged["_product_merge"].eq("both")
    merged = merged.drop(columns="_product_merge")

    merged = merged.merge(
        customers[["customer_id", "gender", "age", "city", "signup_date"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
        indicator="_customer_merge",
    )
    merged["customer_match"] = merged["_customer_merge"].eq("both")
    merged = merged.drop(columns="_customer_merge")

    merged["merge_valid"] = (
        merged["order_match"]
        & merged["product_match"]
        & merged["customer_match"]
    )

    output_columns = [
        "order_item_id",
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
        "order_month",
        "order_dayofweek",
        "payment_method",
        "order_status",
        "gender",
        "age",
        "city",
        "signup_date",
        "product_name",
        "category",
        "price",
        "quantity",
        "unit_price",
        "line_total",
        "order_match",
        "product_match",
        "customer_match",
        "merge_valid",
    ]

    result = merged[output_columns].copy()

    if len(result) != len(order_items):
        raise ValueError(
            "통합 후 행 수가 order_items와 다릅니다: "
            f"order_items={len(order_items)}, visualization={len(result)}"
        )

    return result


def main() -> None:
    data = load_processed_data()
    visualization = build_visualization_dataset(data)
    visualization.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("Chapter 07 visualization.csv 생성 완료")
    print("출력:", OUTPUT_PATH)
    print("shape:", visualization.shape)
    print("grain: 1 row = 1 order_item_id")
    print("order_match 실패:", int((~visualization["order_match"]).sum()))
    print("product_match 실패:", int((~visualization["product_match"]).sum()))
    print("customer_match 실패:", int((~visualization["customer_match"]).sum()))
    print("merge_valid=False:", int((~visualization["merge_valid"]).sum()))


if __name__ == "__main__":
    main()
