"""Chapter 14 산출물 검증 Task 스크립트.

실행 방법:
    python scripts/ch14_validate_outputs.py
"""

from pathlib import Path

from src.automation_pipeline import project_root_from_file, validate_outputs


BASE_DIR = project_root_from_file(Path(__file__))


if __name__ == "__main__":
    validation_log = validate_outputs(BASE_DIR)
    print("결과 파일 검증 완료")
    print(validation_log.to_string(index=False))
