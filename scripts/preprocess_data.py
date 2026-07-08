"""Chapter 5 데이터 전처리 실행 스크립트.

실행 방법:
    python scripts/preprocess_data.py

입력:
    data/raw/customers.csv
    data/raw/products.csv
    data/raw/orders.csv
    data/raw/order_items.csv

출력:
    data/processed/customers_clean.csv
    data/processed/products_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv
    reports/ch05_preprocessing_summary.md
"""

from pathlib import Path

from src.data_loader import load_sales_data
from src.preprocessing import (
    build_preprocessing_report,
    compare_shapes,
    duplicate_summary,
    preprocess_sales_data,
    save_processed_data,
    validate_relationships,
)


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")
REPORT_PATH = REPORT_DIR / "ch05_preprocessing_summary.md"


def main() -> None:
    """원본 쇼핑몰 데이터를 전처리하고 결과 파일과 요약 보고서를 저장합니다."""
    REPORT_DIR.mkdir(exist_ok=True)

    raw_data = load_sales_data(RAW_DIR)
    processed_data = preprocess_sales_data(raw_data)

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
    relationship_checks = validate_relationships(processed_data)

    saved_paths = save_processed_data(processed_data, PROCESSED_DIR)
    report_text = build_preprocessing_report(
        raw_data=raw_data,
        processed_data=processed_data,
        relationship_checks=relationship_checks,
    )
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    print("전처리 완료")
    print("\n[전처리 전후 데이터 크기]")
    print(comparison.to_string(index=False))
    print("\n[중복 점검 결과]")
    print(duplicate_checks.to_string(index=False))
    print("\n[파일 간 관계 점검 결과]")
    print(relationship_checks.to_string(index=False))
    print("\n[저장된 전처리 파일]")
    for path in saved_paths:
        print(f"- {path}")
    print(f"\n[요약 보고서] {REPORT_PATH}")


if __name__ == "__main__":
    main()
