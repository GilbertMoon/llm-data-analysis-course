"""Chapter 11 safe LLM prompt-design artifact generator.

Run:
    python scripts/run_llm_prompt_analysis.py

Prerequisite:
    python scripts/preprocess_data.py

Input:
    data/processed/customers_clean.csv
    data/processed/products_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

This script does not call an external LLM and does not silently fall back to raw data.

Outputs:
    reports/ch11_dataset_summary_for_llm.csv
    reports/ch11_column_summary_for_llm.csv
    reports/ch11_sensitive_column_review.csv
    reports/ch11_safe_llm_context.md
    reports/ch11_safe_context_validation.csv
    reports/ch11_prompt_templates.csv
    reports/ch11_llm_review_checklist.csv
    reports/ch11_llm_usage_log.csv
    reports/ch11_llm_prompt_log.md
"""

from pathlib import Path

from src.llm_prompt_analysis import run_llm_prompt_analysis


PROCESSED_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")  # retained only for API compatibility; no automatic fallback
REPORT_DIR = Path("reports")


def main() -> None:
    """Generate Chapter 11 safe prompt/context templates without an LLM call."""
    result = run_llm_prompt_analysis(
        processed_dir=PROCESSED_DIR,
        raw_dir=RAW_DIR,
        report_dir=REPORT_DIR,
    )

    print("11장 안전 LLM 프롬프트 자료 생성 완료")
    print("사용 데이터:", result["source_type"])
    print("외부 LLM 호출: 없음")

    print("\n[데이터셋 요약]")
    print(result["dataset_summary"].to_string(index=False))

    print("\n[Safe Context 자동 검증]")
    print(result["context_validation"].to_string(index=False))

    print("\n[민감 컬럼 점검]")
    sensitive_review = result["sensitive_review"]
    if sensitive_review.empty:
        print("자동 검토 후보가 없습니다. 사람 검토는 여전히 필요합니다.")
    else:
        print(sensitive_review.to_string(index=False))

    print("\n[프롬프트 템플릿]")
    print(
        result["prompt_templates"][
            [
                "step",
                "purpose",
                "prompt_version",
                "human_review_required",
                "validation_point",
            ]
        ].to_string(index=False)
    )

    print("\n[LLM 사용 로그 상태]")
    print(
        result["usage_log"][["step", "execution_status", "final_use"]]
        .to_string(index=False)
    )
    print("※ not_executed 행은 실제 LLM 사용 증거가 아닙니다.")

    print("\n[저장된 결과 파일]")
    for name, path in result["output_paths"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
