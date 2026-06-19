"""간단한 Word 보고서 생성 예제 스크립트입니다."""

from src.report_generator import create_word_report


def main() -> None:
    create_word_report(
        title="쇼핑몰 매출 분석 보고서",
        summary="샘플 데이터를 활용해 매출 현황과 주요 인사이트를 정리했습니다.",
        insights=[
            "카테고리별 매출 차이를 확인합니다.",
            "고객별 구매금액 상위 그룹을 파악합니다.",
            "분석 결과를 바탕으로 다음 액션을 제안합니다.",
        ],
    )
    print("reports/outputs/analysis_report.docx 파일을 생성했습니다.")


if __name__ == "__main__":
    main()
