"""Generate Chapter 12 LLM-code validation evidence.

Run:
    python scripts/run_llm_code_validation.py

Prerequisite:
    python scripts/preprocess_data.py

Important: the default risky-code example is parsed as a string only. It is never
executed by this script. The strengthened policy layer distinguishes REVIEW from
BLOCKED findings and keeps ML leakage, sandbox, package, and human approval in the
final execution gate.
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm_code_validation_policy import run_llm_code_validation  # noqa: E402

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"


def _print_table(title: str, value: object) -> None:
    print(f"\n[{title}]")
    if hasattr(value, "to_string"):
        print(value.to_string(index=False))
    else:
        print(value)


def main() -> None:
    result = run_llm_code_validation(
        processed_dir=PROCESSED_DIR,
        report_dir=REPORT_DIR,
    )
    outputs = result["outputs"]

    print("12장 LLM 분석 코드 검증 Evidence 생성 완료")
    print("주의: 정적 스캔 대상 예시는 실행하지 않고 문자열 AST만 검사했습니다.")

    _print_table("데이터셋 인벤토리", outputs["inventory"])
    _print_table("필수 컬럼", outputs["required_column_check"])
    _print_table("PK", outputs["primary_key_check"])
    _print_table("관계", outputs["relationship_check"])
    _print_table("카테고리 집계 검증", outputs["category_validation"])
    _print_table("월별 집계 검증", outputs["monthly_validation"])
    _print_table("문제별 ML 누수 계약", outputs["leakage_review"])
    _print_table("생성 코드 정적 스캔 예시", outputs["static_scan"])
    _print_table("실행 Gate", outputs["execution_gate"])

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")

    print("\n자동 PASS는 실행 승인이 아닙니다. sandbox/package/human review를 별도로 완료하세요.")


if __name__ == "__main__":
    main()
