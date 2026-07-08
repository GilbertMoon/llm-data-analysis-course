"""Chapter 14 시각화 Task 스크립트.

실행 방법:
    python scripts/ch14_visualization.py
"""

from pathlib import Path

from src.automation_pipeline import generate_visualizations, project_root_from_file


BASE_DIR = project_root_from_file(Path(__file__))


if __name__ == "__main__":
    outputs = generate_visualizations(BASE_DIR)
    print("시각화 완료")
    for name, path in outputs.items():
        print(f"- {name}: {path}")
