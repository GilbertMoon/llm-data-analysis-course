"""Run the Chapter 9 leakage-aware regression analysis.

Run from any working directory:

    python scripts/run_regression_analysis.py

Prerequisite:

    python scripts/preprocess_data.py

Inputs:

    data/processed/customers_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

Outputs:

    reports/ch09_regression_model_data_internal.csv
    reports/ch09_regression_model_comparison.csv
    reports/ch09_regression_cv_summary.csv
    reports/ch09_regression_predictions_internal.csv
    reports/ch09_regression_checklist.csv
    reports/ch09_regression_report.md
    reports/figures/ch09_actual_vs_predicted.png
    reports/figures/ch09_residual_histogram.png
"""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.regression import run_regression_analysis  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"


def main() -> None:
    """Run the synchronized Chapter 9 regression workflow."""
    result = run_regression_analysis(
        processed_dir=PROCESSED_DIR,
        report_dir=REPORT_DIR,
        test_size=0.2,
        random_state=42,
    )

    train_data = result["train_data"]
    test_data = result["test_data"]

    print("9장 회귀 분석 완료")
    print("\n[모델링 데이터]")
    print(result["model_data"].shape)

    print("\n[훈련·테스트 기간]")
    print(
        "훈련:",
        train_data["order_date"].min(),
        "~",
        train_data["order_date"].max(),
        f"({len(train_data)}행)",
    )
    print(
        "테스트:",
        test_data["order_date"].min(),
        "~",
        test_data["order_date"].max(),
        f"({len(test_data)}행)",
    )

    print("\n[모델 비교 결과]")
    print(
        result["model_comparison"].to_string(
            index=False
        )
    )

    print("\n[시간 순서 교차검증]")
    print(
        result["cv_summary"].to_string(
            index=False
        )
    )

    print("\n[진단 모델]")
    print(result["selected_model_name"])

    print("\n[내부 예측 오차 상위 10건]")
    print(
        result["prediction_result"]
        .head(10)
        .to_string(index=False)
    )

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
