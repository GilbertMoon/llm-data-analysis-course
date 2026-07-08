"""Chapter 14 분석 Task 스크립트.

실행 방법:
    python scripts/ch14_analysis.py
"""

from pathlib import Path

from src.automation_pipeline import project_root_from_file, run_analysis


BASE_DIR = project_root_from_file(Path(__file__))


if __name__ == "__main__":
    outputs = run_analysis(BASE_DIR)
    print("분석 완료")
    for name, path in outputs.items():
        print(f"- {name}: {path}")
