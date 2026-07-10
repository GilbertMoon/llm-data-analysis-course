"""Chapter 15 최종 데이터 분석 프로젝트 실행 스크립트.

실행:
    python scripts/run_final_project.py

전제:
    python scripts/generate_sample_data.py

기본 실행은 네트워크를 호출하지 않습니다. 외부 데이터 통합은
data/external/processed/holidays.csv가 있을 때만 수행합니다.
"""

from pathlib import Path

from src.automation_pipeline import project_root_from_file
from src.final_project import run_final_project


BASE_DIR = project_root_from_file(Path(__file__))


def main() -> None:
    """15장 최종 프로젝트 전체 파이프라인을 실행합니다."""
    result = run_final_project(
        BASE_DIR,
        random_state=42,
    )

    print("15장 최종 프로젝트 완료")

    print("\n[프로젝트 검증]")
    print(result["validation"].to_string(index=False))

    print("\n[완료 주문 매출 범위]")
    print(
        result["core"]["public_tables"][
            "amount_scope_summary"
        ].to_string(index=False)
    )

    print("\n[카테고리별 완료 주문 매출]")
    print(
        result["core"]["public_tables"][
            "category_sales"
        ].head().to_string(index=False)
    )

    print("\n[분류 단계]")
    print(
        result["classification"]["status"].to_string(
            index=False
        )
    )
    if not result["classification"]["test_metrics"].empty:
        print(
            result["classification"]["test_metrics"].to_string(
                index=False
            )
        )

    print("\n[외부 데이터 단계]")
    print(
        result["external"]["status"].to_string(
            index=False
        )
    )

    print("\n[최종 보고서]")
    print(result["final_report_path"])

    print("\n[산출물 manifest]")
    print(result["deliverables_path"])

    print("\n[산출물 수]")
    print(len(result["output_paths"]))


if __name__ == "__main__":
    main()
