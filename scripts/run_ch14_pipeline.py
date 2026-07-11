"""Run the Chapter 14 validated local analysis pipeline.

Run from any working directory:

    python scripts/run_ch14_pipeline.py

The same functions are used by the Airflow TaskFlow Dag.
"""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.automation_pipeline import run_local_pipeline  # noqa: E402


def main() -> None:
    """Run the local pipeline and print the validation summary."""
    result = run_local_pipeline(PROJECT_ROOT)

    print("14장 로컬 분석 파이프라인 완료")
    print("\n[입력 파일 확인]")
    print(result["input_check"].to_string(index=False))

    print("\n[생성된 전처리 파일]")
    for name, path in result["preprocessing_outputs"].items():
        print(f"- {name}: {path}")

    print("\n[생성된 분석 파일]")
    for name, path in result["analysis_outputs"].items():
        print(f"- {name}: {path}")

    print("\n[생성된 그래프]")
    for name, path in result["figure_outputs"].items():
        print(f"- {name}: {path}")

    print("\n[보고서]")
    print(result["report_path"])

    print("\n[검증 결과]")
    print(result["validation_log"].to_string(index=False))

    failed = result["validation_log"].loc[
        result["validation_log"]["status"].ne("ok")
    ]
    if not failed.empty:
        raise SystemExit("검증 실패 항목이 있습니다.")

    print("\n모든 검증 항목이 ok입니다.")


if __name__ == "__main__":
    main()
