"""Chapter 11 LLM 프롬프트 분석 보조 실행 스크립트.

실행 방법:
    python scripts/run_llm_prompt_analysis.py

전제 조건:
    python scripts/preprocess_data.py

입력:
    data/processed/*_clean.csv 또는 data/raw/*.csv

출력:
    reports/ch11_dataset_summary_for_llm.csv
    reports/ch11_column_summary_for_llm.csv
    reports/ch11_safe_llm_context.md
    reports/ch11_prompt_templates.csv
    reports/ch11_llm_review_checklist.csv
    reports/ch11_llm_usage_log.csv
    reports/ch11_llm_prompt_log.md
"""

from pathlib import Path

from src.llm_prompt_analysis import run_llm_prompt_analysis


PROCESSED_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")
REPORT_DIR = Path("reports")


def main() -> None:
    """11장 LLM 프롬프트 분석 보조 자료를 생성합니다."""
    result = run_llm_prompt_analysis(
        processed_dir=PROCESSED_DIR,
        raw_dir=RAW_DIR,
        report_dir=REPORT_DIR,
    )

    print("11장 LLM 프롬프트 분석 보조 자료 생성 완료")
    print("\n[데이터셋 요약]")
    print(result["dataset_summary"].to_string(index=False))

    print("\n[프롬프트 템플릿 목록]")
    print(result["prompt_templates"][["step", "purpose", "validation_point"]].to_string(index=False))

    print("\n[검증 체크리스트]")
    print(result["checklist"].head().to_string(index=False))

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
