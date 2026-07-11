"""Run the Chapter 12 LLM-generated code validation workflow.

Run from any working directory:

    python scripts/run_llm_code_validation.py

Prerequisite:

    python scripts/preprocess_data.py
"""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm_code_validation import run_llm_code_validation  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"


def _print_table(title: str, value: object) -> None:
    print(f"\n[{title}]")
    if hasattr(value, "to_string"):
        print(value.to_string(index=False))
    else:
        print(value)


def main() -> None:
    """Generate the Chapter 12 validation evidence and report files."""
    result = run_llm_code_validation(
        processed_dir=PROCESSED_DIR,
        report_dir=REPORT_DIR,
    )
    outputs = result["outputs"]

    print("12장 LLM 분석 코드 검증 완료")
    _print_table("데이터셋 인벤토리", outputs["inventory"])
    _print_table("필수 컬럼 점검", outputs["required_column_check"])
    _print_table("고유 키 점검", outputs["primary_key_check"])
    _print_table("키 관계 점검", outputs["relationship_check"])
    _print_table("카테고리 집계 검증", outputs["category_validation"])
    _print_table("월별 집계 검증", outputs["monthly_validation"])
    _print_table("생성 코드 정적 점검 예시", outputs["static_scan"])

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
