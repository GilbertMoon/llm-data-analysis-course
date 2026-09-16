"""Chapter 10 분류 분석 실행 스크립트.

실행 방법:
    python scripts/prepare_ch10_data.py
    python scripts/run_classification_analysis.py

입력:
    data/processed/customers_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

주요 출력:
    reports/ch10_classification_model_data_internal.csv
    reports/ch10_target_distribution.csv
    reports/ch10_feature_audit.csv
    reports/ch10_merge_checks.csv
    reports/ch10_data_quality_checks.csv
    reports/ch10_split_summary.csv
    reports/ch10_validation_model_comparison.csv
    reports/ch10_validation_threshold_metrics.csv
    reports/ch10_test_metrics.csv
    reports/ch10_classification_predictions_internal.csv
    reports/ch10_classification_predictions.csv
    reports/ch10_confusion_matrix.csv
    reports/ch10_classification_report.csv
    reports/ch10_classification_validation.csv
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

    print("Chapter10 분류 분석 완료")

    print("\n[모델링 데이터]")
    print(result["model_data"].shape)

    print("\n[타깃 분포]")
    print(result["target_distribution"].to_string(index=False))

    print("\n[Feature Audit]")
    print(result["feature_audit"].to_string(index=False))

    print("\n[병합 검증]")
    print(result["merge_checks"].to_string(index=False))

    print("\n[데이터 분할]")
    print(result["split_summary"].to_string(index=False))

    print("\n[Validation 모델 비교]")
    print(result["validation_model_comparison"].to_string(index=False))

    print("\n[Validation에서 고정한 모델과 Threshold]")
    print("모델:", result["selected_model_name"])
    print("Threshold:", result["selected_threshold"])

    print("\n[Validation Threshold 비교]")
    print(result["threshold_metrics"].to_string(index=False))

    print("\n[Final Test 성능]")
    print(result["test_metrics"].to_string(index=False))

    print("\n[Final Test 혼동행렬]")
    print(result["confusion_matrix"].to_string())

    print("\n[자동 Validation Evidence]")
    print(result["validation"].to_string(index=False))

    print("\n[공개 Prediction 컬럼]")
    print(result["prediction_result"].columns.tolist())

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
