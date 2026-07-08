"""Chapter 6 EDA 실행 스크립트.

실행 방법:
    python scripts/run_eda.py

전제 조건:
    python scripts/preprocess_data.py

입력:
    data/processed/customers_clean.csv
    data/processed/products_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

출력:
    reports/ch06_category_sales.csv
    reports/ch06_monthly_sales.csv
    reports/ch06_customer_sales.csv
    reports/ch06_eda_questions.csv
    reports/ch06_customer_city.csv
    reports/ch06_product_category.csv
    reports/ch06_eda_summary.md
"""

from pathlib import Path

from src.eda import (
    build_eda_report,
    load_processed_sales_data,
    run_basic_eda,
    save_eda_outputs,
)


PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")
REPORT_PATH = REPORT_DIR / "ch06_eda_summary.md"


def main() -> None:
    """전처리된 데이터를 불러와 6장 기본 EDA 결과와 요약 보고서를 저장합니다."""
    REPORT_DIR.mkdir(exist_ok=True)

    data = load_processed_sales_data(PROCESSED_DIR)
    results = run_basic_eda(data)
    saved_paths = save_eda_outputs(results, REPORT_DIR)

    report_text = build_eda_report(results)
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    print("6장 EDA 완료")
    print("\n[카테고리별 매출 상위 5개]")
    print(results["category_sales"].head().to_string(index=False))
    print("\n[월별 매출]")
    print(results["monthly_sales"].to_string(index=False))
    print("\n[고객별 구매 금액 상위 5명]")
    print(results["customer_sales"].head().to_string(index=False))
    print("\n[저장된 CSV 파일]")
    for path in saved_paths:
        print(f"- {path}")
    print(f"\n[요약 보고서] {REPORT_PATH}")


if __name__ == "__main__":
    main()
