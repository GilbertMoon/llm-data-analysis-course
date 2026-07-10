"""Chapter 13 외부 데이터 수집 준비 자료 생성 스크립트.

실행:
    python scripts/run_external_data_collection.py

이 스크립트는 네트워크를 호출하지 않습니다. 외부 데이터 폴더 구조,
환경변수 로드 상태, 수집 계획, 연결 기준, 체크리스트와 출처 로그
템플릿만 생성합니다.

출력:
    data/external/raw/
    data/external/processed/
    data/external/metadata/
    reports/ch13_external_data_plan.csv
    reports/ch13_collection_method_summary.csv
    reports/ch13_external_integration_plan.csv
    reports/ch13_external_data_checklist.csv
    reports/ch13_external_data_log.csv
    reports/ch13_env_key_status.csv
    reports/ch13_external_data_summary.md
"""

from pathlib import Path

from src.external_data_collection import (
    run_external_data_collection_setup,
)


BASE_DIR = Path(".")
REPORT_DIR = BASE_DIR / "reports"


def main() -> None:
    """13장 외부 데이터 수집 준비 자료를 생성합니다."""
    result = run_external_data_collection_setup(
        base_dir=BASE_DIR,
        report_dir=REPORT_DIR,
    )
    outputs = result["outputs"]

    print("13장 외부 데이터 수집 준비 완료")
    print("\n[생성된 폴더]")
    for name, path in result["paths"].items():
        print(f"- {name}: {path}")

    print("\n[환경변수 로드 상태: 실제 값은 출력하지 않음]")
    print(outputs["env_status"].to_string(index=False))

    print("\n[수집 방법 우선순위]")
    print(outputs["method_summary"].to_string(index=False))

    print("\n[외부 데이터 연결 기준]")
    print(outputs["integration_plan"].to_string(index=False))

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
