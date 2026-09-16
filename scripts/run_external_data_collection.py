"""Generate Chapter 13 external-data planning and safety evidence.

Run from any working directory:

    python scripts/run_external_data_collection.py

This script intentionally performs NO network requests. It creates the external-data
folder structure and planning/review templates only.
"""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.external_data_collection import run_external_data_collection_setup  # noqa: E402


REPORT_DIR = PROJECT_ROOT / "reports"


def _print_table(title: str, value: object) -> None:
    print(f"\n[{title}]")
    if hasattr(value, "to_string"):
        print(value.to_string(index=False))
    else:
        print(value)


def main() -> None:
    result = run_external_data_collection_setup(
        base_dir=PROJECT_ROOT,
        report_dir=REPORT_DIR,
    )
    outputs = result["outputs"]

    print("13장 외부 데이터 수집 준비 완료 — 네트워크 호출 없음")
    print("\n[생성된 폴더]")
    for name, path in result["paths"].items():
        print(f"- {name}: {path}")

    _print_table("환경변수 상태 — 실제 값은 출력하지 않음", outputs["env_status"])
    _print_table("네트워크 실행 Gate — 모두 기본 비활성화", outputs["network_gate"])
    _print_table("수집 계획", outputs["data_plan"])
    _print_table("수집 방법 우선순위", outputs["method_summary"])
    _print_table("외부 데이터 연결 기준", outputs["integration_plan"])
    _print_table("API 코드 리뷰 체크리스트", outputs["api_code_review"])

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")

    print(
        "\n실제 API/HTML 수집은 이 스크립트가 수행하지 않습니다. "
        "현재 공식 문서·라이선스·이용약관·호출 제한을 확인한 뒤 "
        "Notebook의 RUN_* 플래그를 명시적으로 활성화하세요."
    )


if __name__ == "__main__":
    main()
