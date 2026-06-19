"""초보자용 Airflow DAG 예제입니다.

이 파일은 실제 운영용 DAG가 아니라, 데이터 분석 파이프라인이 어떤 단계로
나뉘는지 보여주기 위한 수업용 예시입니다.
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="sales_analysis_practice",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["practice", "sales-analysis"],
)
def sales_analysis_practice():
    """CSV 읽기, 전처리, 분석, 보고서 생성을 순서대로 실행하는 예제 DAG입니다."""

    @task
    def read_csv_data() -> str:
        """CSV 데이터를 읽는 단계입니다."""
        print("data/raw 폴더에서 CSV 파일을 읽습니다.")
        return "raw_data_loaded"

    @task
    def preprocess_data(previous_step: str) -> str:
        """결측치 확인, 중복 제거, 날짜 변환 같은 전처리 단계입니다."""
        print(f"이전 단계 결과: {previous_step}")
        print("데이터 전처리를 실행합니다.")
        return "data_preprocessed"

    @task
    def run_analysis(previous_step: str) -> str:
        """매출 집계와 고객별 구매금액 분석을 실행하는 단계입니다."""
        print(f"이전 단계 결과: {previous_step}")
        print("매출 분석을 실행합니다.")
        return "analysis_completed"

    @task
    def generate_report(previous_step: str) -> None:
        """분석 결과를 보고서로 저장하는 단계입니다."""
        print(f"이전 단계 결과: {previous_step}")
        print("보고서를 생성합니다.")

    raw_data = read_csv_data()
    clean_data = preprocess_data(raw_data)
    analysis_result = run_analysis(clean_data)
    generate_report(analysis_result)


sales_analysis_practice()
