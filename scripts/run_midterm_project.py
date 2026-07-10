"""Chapter 8 중간 프로젝트 실행 스크립트.

실행 방법:
    python scripts/run_midterm_project.py

입력:
    data/raw/customers.csv
    data/raw/products.csv
    data/raw/orders.csv
    data/raw/order_items.csv

출력:
    data/processed/*_clean.csv
    reports/ch08_dataset_summary.csv
    reports/ch08_preprocessing_comparison.csv
    reports/ch08_key_duplicate_checks.csv
    reports/ch08_relationship_checks.csv
    reports/ch08_merge_checks.csv
    reports/ch08_amount_scope_summary.csv
    reports/ch08_category_sales.csv
    reports/ch08_monthly_sales.csv
    reports/ch08_customer_sales.csv
    reports/ch08_order_status_summary.csv
    reports/ch08_interpretation_notes.csv
    reports/figures/ch08_category_sales.png
    reports/figures/ch08_monthly_sales.png
    reports/figures/ch08_top_customers.png
    reports/ch08_midterm_report.md
"""

from pathlib import Path

from src.midterm_project import run_midterm_project


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")
FIGURE_DIR = REPORT_DIR / "figures"


def main() -> None:
    """8장 중간 프로젝트 전체 파이프라인을 실행합니다."""
    result = run_midterm_project(
        raw_dir=RAW_DIR,
        processed_dir=PROCESSED_DIR,
        report_dir=REPORT_DIR,
        figure_dir=FIGURE_DIR,
        show_figures=False,
    )

    print("8장 중간 프로젝트 완료")
    print("\n[데이터 개요]")
    print(result["dataset_summary"].to_string(index=False))

    print("\n[전처리 전후 비교]")
    print(result["preprocessing_comparison"].to_string(index=False))

    print("\n[키 중복 점검]")
    print(result["key_duplicate_checks"].to_string(index=False))

    print("\n[병합 검증]")
    print(result["analysis_tables"]["merge_checks"].to_string(index=False))

    print("\n[전체 주문 금액과 완료 주문 매출 구분]")
    print(result["analysis_tables"]["amount_scope_summary"].to_string(index=False))

    print("\n[카테고리별 완료 주문 매출 상위 5개]")
    print(result["analysis_tables"]["category_sales"].head().to_string(index=False))

    print("\n[월별 완료 주문 매출]")
    print(result["analysis_tables"]["monthly_sales"].to_string(index=False))

    print("\n[저장된 결과표]")
    for path in result["saved_tables"]:
        print(f"- {path}")

    print("\n[저장된 그래프]")
    for path in result["saved_figures"]:
        print(f"- {path}")

    print(f"\n[최종 보고서] {result['report_path']}")


if __name__ == "__main__":
    main()
