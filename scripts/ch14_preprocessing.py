"""Chapter 14 전처리 Task 스크립트.

실행 방법:
    python scripts/ch14_preprocessing.py
"""

from pathlib import Path

from src.automation_pipeline import project_root_from_file, run_preprocessing


BASE_DIR = project_root_from_file(Path(__file__))


if __name__ == "__main__":
    outputs = run_preprocessing(BASE_DIR)
    print("전처리 완료")
    for name, path in outputs.items():
        print(f"- {name}: {path}")
