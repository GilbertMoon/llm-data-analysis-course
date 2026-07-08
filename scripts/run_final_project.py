"""Chapter 15 기말 종합 프로젝트 실행 스크립트.

실행 방법:
    python scripts/run_final_project.py

전제 조건:
    python scripts/generate_sample_data.py

출력:
    reports/ch15_dataset_summary.csv
    reports/ch15_preprocessing_comparison.csv
    reports/ch15_category_sales.csv
    reports/ch15_monthly_sales.csv
    reports/ch15_customer_sales.csv
    reports/ch15_product_sales.csv
    reports/figures/ch15_*.png
    reports/ch15_regression_model_comparison.csv
    reports/ch15_classification_model_comparison.csv
    reports/ch15_holiday_sales_comparison.csv
    reports/ch15_external_data_integration.md
    reports/ch15_insight_cards.csv
    reports/ch15_llm_usage_log.md
    reports/ch15_automation_plan.md
    reports/ch15_final_report.md
    reports/ch15_project_deliverables.csv
"""

from pathlib import Path

from src.automation_pipeline import project_root_from_file
from src.final_project import run_final_project


BASE_DIR = project_root_from_file(Path(__file__))


def main() -> None:
    """15장 기말 종합 프로젝트 전체 파이프라인을 실행합니다."""
    result = run_final_project(BASE_DIR)

    print("15장 기말 종합 프로젝트 완료")

    print("\n[데이터 개요]")
    print(result["dataset_summary"].to_string(index=False))

    print("\n[전처리 전후 비교]")
    print(result["preprocessing_comparison"].to_string(index=False))

    print("\n[카테고리별 매출 상위]")
    print(result["tables"]["category_sales"].head().to_string(index=False))

    print("\n[월별 매출]")
    print(result["tables"]["monthly_sales"].head(12).to_string(index=False))

    print("\n[회귀 모델 비교]")
    print(result["regression"].to_string(index=False))

    print("\n[분류 모델 비교]")
    print(result["classification"].to_string(index=False))

    print("\n[공휴일 매출 비교]")
    print(result["holiday_result"]["holiday_sales_comparison"].to_string(index=False))

    print("\n[인사이트 카드]")
    print(result["insight_cards"].to_string(index=False))

    print("\n[최종 보고서]")
    print(result["final_report_path"])

    print("\n[산출물 목록]")
    print(result["deliverables"].to_string(index=False))


if __name__ == "__main__":
    main()
