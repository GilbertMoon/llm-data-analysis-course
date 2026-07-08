"""Chapter 9 회귀 분석 실행 스크립트.

실행 방법:
    python scripts/run_regression_analysis.py

전제 조건:
    python scripts/preprocess_data.py

입력:
    data/processed/customers_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

출력:
    reports/ch09_regression_model_data.csv
    reports/ch09_regression_model_comparison.csv
    reports/ch09_regression_predictions.csv
    reports/ch09_regression_checklist.csv
    reports/ch09_regression_report.md
"""

from pathlib import Path

from src.regression import run_regression_analysis


PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")


def main() -> None:
    """9장 회귀 분석 전체 파이프라인을 실행합니다."""
    result = run_regression_analysis(
        processed_dir=PROCESSED_DIR,
        report_dir=REPORT_DIR,
        random_state=42,
    )

    print("9장 회귀 분석 완료")
    print("\n[모델링 데이터]")
    print(result["model_data"].shape)

    print("\n[모델 비교 결과]")
    print(result["model_comparison"].to_string(index=False))

    print("\n[선택 모델]")
    print(result["best_model_name"])

    print("\n[예측 오차 상위 10건]")
    print(result["prediction_result"].head(10).to_string(index=False))

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
