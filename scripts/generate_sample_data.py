"""실습용 가상 쇼핑몰 데이터를 생성합니다.

실행 방법:
    python scripts/generate_sample_data.py

생성 위치:
    data/raw/customers.csv
    data/raw/products.csv
    data/raw/orders.csv
    data/raw/order_items.csv
"""

from pathlib import Path
import random

from faker import Faker
import pandas as pd


SEED = 42
RAW_DATA_DIR = Path("data/raw")


def create_customers(fake: Faker, count: int = 150) -> pd.DataFrame:
    """가상의 고객 데이터를 생성합니다."""
    cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "수원", "성남", "고양"]
    genders = ["F", "M"]

    rows = []
    for customer_id in range(1, count + 1):
        rows.append(
            {
                "customer_id": customer_id,
                "name": fake.name(),
                "gender": random.choice(genders),
                "age": random.randint(18, 69),
                "city": random.choice(cities),
                "signup_date": fake.date_between(start_date="-3y", end_date="today").isoformat(),
            }
        )
    return pd.DataFrame(rows)


def create_products(count: int = 100) -> pd.DataFrame:
    """가상의 상품 데이터를 생성합니다."""
    categories = ["식품", "생활용품", "패션", "전자기기", "도서", "스포츠", "뷰티"]

    rows = []
    for product_id in range(1, count + 1):
        category = random.choice(categories)
        rows.append(
            {
                "product_id": product_id,
                "product_name": f"{category} 상품 {product_id:03d}",
                "category": category,
                "price": random.randrange(5_000, 200_001, 1_000),
            }
        )
    return pd.DataFrame(rows)


def create_orders(customer_ids: list[int], fake: Faker, count: int = 300) -> pd.DataFrame:
    """가상의 주문 데이터를 생성합니다."""
    payment_methods = ["card", "bank_transfer", "kakao_pay", "naver_pay"]
    order_statuses = ["completed", "completed", "completed", "cancelled", "refunded"]

    rows = []
    for order_id in range(1, count + 1):
        rows.append(
            {
                "order_id": order_id,
                "customer_id": random.choice(customer_ids),
                "order_date": fake.date_between(start_date="-1y", end_date="today").isoformat(),
                "payment_method": random.choice(payment_methods),
                "order_status": random.choice(order_statuses),
            }
        )
    return pd.DataFrame(rows)


def create_order_items(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """각 주문에 1개 이상 상품을 연결한 주문 상세 데이터를 생성합니다."""
    product_price_map = dict(zip(products["product_id"], products["price"], strict=True))
    product_ids = list(product_price_map.keys())

    rows = []
    order_item_id = 1
    for order_id in orders["order_id"]:
        for _ in range(random.randint(1, 4)):
            product_id = random.choice(product_ids)
            rows.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": random.randint(1, 5),
                    "unit_price": product_price_map[product_id],
                }
            )
            order_item_id += 1
    return pd.DataFrame(rows)


def main() -> None:
    """CSV 파일 4개를 data/raw 폴더에 저장합니다."""
    random.seed(SEED)
    Faker.seed(SEED)
    fake = Faker("ko_KR")

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    customers = create_customers(fake)
    products = create_products()
    orders = create_orders(customers["customer_id"].tolist(), fake)
    order_items = create_order_items(orders, products)

    customers.to_csv(RAW_DATA_DIR / "customers.csv", index=False, encoding="utf-8-sig")
    products.to_csv(RAW_DATA_DIR / "products.csv", index=False, encoding="utf-8-sig")
    orders.to_csv(RAW_DATA_DIR / "orders.csv", index=False, encoding="utf-8-sig")
    order_items.to_csv(RAW_DATA_DIR / "order_items.csv", index=False, encoding="utf-8-sig")

    print("샘플 데이터 생성 완료")
    print(f"- {RAW_DATA_DIR / 'customers.csv'}: {len(customers)} rows")
    print(f"- {RAW_DATA_DIR / 'products.csv'}: {len(products)} rows")
    print(f"- {RAW_DATA_DIR / 'orders.csv'}: {len(orders)} rows")
    print(f"- {RAW_DATA_DIR / 'order_items.csv'}: {len(order_items)} rows")


if __name__ == "__main__":
    main()
