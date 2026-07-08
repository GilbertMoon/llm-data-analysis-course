"""Chapter 14 보고서 생성 Task 스크립트.

실행 방법:
    python scripts/ch14_report.py
"""

from pathlib import Path

from src.automation_pipeline import generate_report, project_root_from_file


BASE_DIR = project_root_from_file(Path(__file__))


if __name__ == "__main__":
    report_path = generate_report(BASE_DIR)
    print("보고서 생성 완료:", report_path)
