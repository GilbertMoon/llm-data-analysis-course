"""Chapter 15 최종 데이터 분석 프로젝트 실행 스크립트.

실행:
    python scripts/run_final_project.py

전제:
    python scripts/generate_sample_data.py

기본 실행은 네트워크를 호출하지 않습니다. 외부 데이터는 승인된 실제 파일이
있을 때만 검증 후 연결합니다. 프로젝트 산출물이 생성되어도 submission status가
BLOCKED이면 제출 완료로 처리하지 않습니다.
"""
from pathlib import Path

from src.automation_pipeline import project_root_from_file
from src.final_project import run_final_project


BASE_DIR = project_root_from_file(Path(__file__))


def main() -> None:
    """15장 최종 프로젝트를 실행하고 최종 제출 Gate를 확인합니다."""
    result = run_final_project(BASE_DIR, random_state=42)

    print("15장 최종 프로젝트 파이프라인 실행 종료")

    print("\n[제출 Gate]")
    print(result["submission_status"].to_string(index=False))

    print("\n[프로젝트 검증]")
    print(result["validation"].to_string(index=False))

    print("\n[완료 주문 금액 범위]")
    print(
        result["core"]["public_tables"]["amount_scope_summary"].to_string(
            index=False
        )
    )

    print("\n[카테고리별 완료 주문 기준 금액]")
    print(
        result["core"]["public_tables"]["category_sales"]
        .head()
        .to_string(index=False)
    )

    print("\n[분류 선택 단계]")
    print(result["classification"]["status"].to_string(index=False))
    if not result["classification"]["test_metrics"].empty:
        print(result["classification"]["test_metrics"].to_string(index=False))

    print("\n[외부 데이터 선택 단계]")
    print(result["external"]["status"].to_string(index=False))

    print("\n[LLM 사용 Evidence]")
    print(result["llm_usage_validation"].to_string(index=False))

    print("\n[최종 보고서]")
    print(result["final_report_path"])

    print("\n[산출물 manifest]")
    print(result["deliverables_path"])

    print("\n[산출물 수]")
    print(len(result["output_paths"]))

    status = str(result["submission_status"].iloc[0]["status"])
    if status == "BLOCKED":
        raise SystemExit(
            "제출 Gate가 BLOCKED입니다. FAIL 또는 필수 산출물 누락을 수정한 뒤 다시 실행하세요."
        )

    if status == "READY_WITH_WARNINGS":
        print("\n제출 가능 상태이지만 WARN 사유와 해석 제한을 보고서에 포함해야 합니다.")
    else:
        print("\n필수 검증과 산출물 기준을 충족했습니다.")


if __name__ == "__main__":
    main()
