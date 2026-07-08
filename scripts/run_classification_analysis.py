"""Chapter 10 분류 분석 실행 스크립트.

실행 방법:
    python scripts/run_classification_analysis.py

전제 조건:
    python scripts/preprocess_data.py

입력:
    data/processed/customers_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

출력:
    reports/ch10_classification_model_data.csv
    reports/ch10_target_distribution.csv
    reports/ch10_classification_model_comparison.csv
    reports/ch10_classification_predictions.csv
    reports/ch10_confusion_matrix.csv
    reports/ch10_classification_report.csv
    reports/ch10_threshold_metrics.csv
    reports/ch10_classification_checklist.csv
    reports/ch10_classification_summary.md
"""

from pathlib import Path

from src.classification import run_classification_analysis


PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")


def main() -> None:
    """10장 분류 분석 전체 파이프라인을 실행합니다."""
    result = run_classification_analysis(
        processed_dir=PROCESSED_DIR,
        report_dir=REPORT_DIR,
        random_state=42,
    )

    print("10장 분류 분석 완료")
    print("\n[모델링 데이터]")
    print(result["model_data"].shape)

    print("\n[타깃 분포]")
    print(result["target_distribution"].to_string(index=False))

    print("\n[사용 입력값]")
    print(result["features"])

    print("\n[모델 비교 결과]")
    print(result["model_comparison"].to_string(index=False))

    print("\n[선택 모델]")
    print(result["best_model_name"])

    print("\n[혼동행렬]")
    print(result["confusion_matrix"].to_string())

    print("\n[임계값별 성능]")
    print(result["threshold_metrics"].to_string(index=False))

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
