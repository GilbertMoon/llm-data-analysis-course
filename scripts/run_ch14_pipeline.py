"""Chapter 14 로컬 분석 파이프라인 통합 실행 스크립트.

Airflow에 연결하기 전에 Python 스크립트만으로 전체 흐름이 정상 실행되는지 확인합니다.

실행 방법:
    python scripts/run_ch14_pipeline.py

출력:
    data/processed/*_clean.csv
    reports/ch14_daily_sales.csv
    reports/ch14_category_sales.csv
    reports/ch14_pipeline_task_summary.csv
    reports/figures/ch14_daily_sales.png
    reports/ch14_airflow_report.md
    reports/ch14_airflow_validation_log.csv
    reports/ch14_airflow_setup_guide.csv
"""

from pathlib import Path

from src.automation_pipeline import project_root_from_file, run_local_pipeline


BASE_DIR = project_root_from_file(Path(__file__))


def main() -> None:
    """14장 로컬 분석 파이프라인을 순서대로 실행합니다."""
    result = run_local_pipeline(BASE_DIR)

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

    print("\n[검증 로그]")
    print(result["validation_log"].to_string(index=False))

    print("\n[Airflow 설정 가이드]")
    print(result["setup_guide_path"])


if __name__ == "__main__":
    main()
