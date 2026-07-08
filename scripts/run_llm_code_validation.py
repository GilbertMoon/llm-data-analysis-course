"""Chapter 12 LLM 코드 생성과 검증 실행 스크립트.

실행 방법:
    python scripts/run_llm_code_validation.py

전제 조건:
    python scripts/preprocess_data.py

입력:
    data/processed/customers_clean.csv
    data/processed/products_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

출력:
    reports/ch12_dataset_inventory.csv
    reports/ch12_required_column_check.csv
    reports/ch12_relationship_key_check.csv
    reports/ch12_category_sales_validated.csv
    reports/ch12_category_sales_validation.csv
    reports/ch12_monthly_sales_validated.csv
    reports/ch12_monthly_sales_validation.csv
    reports/ch12_ml_leakage_review.csv
    reports/ch12_llm_code_review_checklist.csv
    reports/ch12_error_fix_prompt_template.md
    reports/ch12_code_validation_summary.md
"""

from pathlib import Path

from src.llm_code_validation import run_llm_code_validation


PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")


def main() -> None:
    """12장 LLM 코드 생성과 검증 자료를 생성합니다."""
    result = run_llm_code_validation(
        processed_dir=PROCESSED_DIR,
        report_dir=REPORT_DIR,
    )
    outputs = result["outputs"]

    print("12장 LLM 코드 생성과 검증 자료 생성 완료")
    print("\n[데이터셋 인벤토리]")
    print(outputs["inventory"].to_string(index=False))

    print("\n[필수 컬럼 점검]")
    print(outputs["required_column_check"].to_string(index=False))

    print("\n[키 관계 점검]")
    print(outputs["relationship_check"].to_string(index=False))

    print("\n[카테고리별 매출 검증]")
    print(outputs["category_validation"].to_string(index=False))

    print("\n[월별 매출 검증]")
    print(outputs["monthly_validation"].to_string(index=False))

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
