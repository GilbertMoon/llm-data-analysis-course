"""Run the Chapter 9 leakage-aware regression analysis.

Run from the project root or any working directory:

    python scripts/run_regression_analysis.py

Prerequisite:

    python scripts/preprocess_data.py

The workflow selects the non-baseline candidate with TimeSeriesSplit on the
training period, freezes that choice, and only then evaluates the frozen model
and DummyRegressor on the final test period.
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

    print("9장 회귀 분석 완료")

    print("\n[시간 순서 분할]")
    print(result["split_summary"].to_string(index=False))

    print("\n[Feature Audit]")
    print(result["feature_audit"].to_string(index=False))

    print("\n[훈련 기간 TimeSeriesSplit 후보 비교]")
    print(result["cv_summary"].to_string(index=False))

    print("\n[훈련 CV로 고정한 모델]")
    print(result["selected_model_name"])

    print("\n[최종 테스트: Baseline vs Frozen Model]")
    print(result["model_comparison"].to_string(index=False))

    print("\n[자동 Validation]")
    print(result["validation"].to_string(index=False))

    print("\n[내부 예측 오차 상위 10건]")
    print(
        result["prediction_result"]
        .head(10)
        .to_string(index=False)
    )
    print("주의: 위 표의 order_id는 내부 진단용입니다.")

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
