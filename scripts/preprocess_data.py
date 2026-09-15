"""Chapter 5 데이터 전처리 실행 스크립트.

실행 방법:
    python scripts/preprocess_data.py

입력(Chapter 05 전용 전처리 전 데이터):
    practice/chapter05/data/raw/customers.csv
    practice/chapter05/data/raw/products.csv
    practice/chapter05/data/raw/orders.csv
    practice/chapter05/data/raw/order_items.csv

출력:
    data/processed/customers_clean.csv
    data/processed/products_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv
    reports/ch05_preprocessing_summary.md

주의:
    프로젝트 공통 data/raw는 변경하지 않습니다. Chapter 05 실습에서는 문자열 표기,
    타입 변환 실패, 결측, 중복, 이상값 후보, PK/FK 관계 문제 등이 의도적으로 포함된
    전용 Raw Dataset을 사용합니다.
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


RAW_DIR = Path("practice/chapter05/data/raw")
PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")
REPORT_PATH = REPORT_DIR / "ch05_preprocessing_summary.md"


def main() -> None:
    """Chapter 05 전용 Raw 데이터를 전처리하고 결과 파일과 요약 보고서를 저장합니다."""
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
    print(f"입력 Raw 경로: {RAW_DIR}")
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
