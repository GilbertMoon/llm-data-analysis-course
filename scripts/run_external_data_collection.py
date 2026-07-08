"""Chapter 13 외부 데이터 수집 준비 실행 스크립트.

실행 방법:
    python scripts/run_external_data_collection.py

출력:
    data/external/ 폴더 생성
    reports/ch13_external_data_plan.csv
    reports/ch13_collection_method_summary.csv
    reports/ch13_external_integration_plan.csv
    reports/ch13_external_data_checklist.csv
    reports/ch13_external_data_log.csv
    reports/ch13_env_key_status.csv
    reports/ch13_external_data_summary.md
"""

from pathlib import Path

from src.external_data_collection import run_external_data_collection_setup


BASE_DIR = Path(".")
REPORT_DIR = Path("reports")


def main() -> None:
    """13장 외부 데이터 수집 실습용 기본 산출물을 생성합니다."""
    result = run_external_data_collection_setup(
        base_dir=BASE_DIR,
        report_dir=REPORT_DIR,
    )
    outputs = result["outputs"]

    print("13장 외부 데이터 수집 준비 완료")
    print("\n[외부 데이터 폴더]")
    print(result["external_dir"])

    print("\n[환경변수 로드 여부: 실제 Key 값은 출력하지 않음]")
    print(outputs["env_status"].to_string(index=False))

    print("\n[외부 데이터 후보]")
    print(outputs["data_plan"].to_string(index=False))

    print("\n[수집 방법 비교]")
    print(outputs["method_summary"].to_string(index=False))

    print("\n[연결 기준]")
    print(outputs["integration_plan"].to_string(index=False))

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
