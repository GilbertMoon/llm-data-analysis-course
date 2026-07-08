"""Chapter 14 로컬 Airflow DAG 예시.

사용 방법:
1. 이 파일을 `.airflow/dags/ch14_local_analysis_pipeline.py`로 복사하거나,
2. Airflow의 DAG 폴더를 이 저장소의 `dags/` 폴더로 설정합니다.

주의:
- `.airflow/` 폴더는 실행 환경 파일이 생성되므로 일반적으로 Git에 올리지 않습니다.
- Airflow 실행 전 `python scripts/run_ch14_pipeline.py`로 Python 스크립트가 정상 실행되는지 먼저 확인하세요.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from src.automation_pipeline import check_input_files, validate_outputs


BASE_DIR = Path(__file__).resolve().parents[1]


def _check_input_files() -> None:
    check_input_files(BASE_DIR)


def _validate_outputs() -> None:
    validate_outputs(BASE_DIR)


default_args = {
    "owner": "data-analysis-class",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="ch14_local_analysis_pipeline",
    description="Docker 없이 로컬에서 실행하는 온라인 쇼핑몰 분석 파이프라인",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["chapter14", "local", "data-analysis"],
) as dag:
    check_input_files_task = PythonOperator(
        task_id="check_input_files",
        python_callable=_check_input_files,
    )

    run_preprocessing = BashOperator(
        task_id="run_preprocessing",
        bash_command=f"python {BASE_DIR / 'scripts' / 'ch14_preprocessing.py'}",
    )

    run_analysis = BashOperator(
        task_id="run_analysis",
        bash_command=f"python {BASE_DIR / 'scripts' / 'ch14_analysis.py'}",
    )

    generate_visualizations = BashOperator(
        task_id="generate_visualizations",
        bash_command=f"python {BASE_DIR / 'scripts' / 'ch14_visualization.py'}",
    )

    generate_report = BashOperator(
        task_id="generate_report",
        bash_command=f"python {BASE_DIR / 'scripts' / 'ch14_report.py'}",
    )

    validate_outputs_task = PythonOperator(
        task_id="validate_outputs",
        python_callable=_validate_outputs,
    )

    check_input_files_task >> run_preprocessing >> run_analysis >> generate_visualizations >> generate_report >> validate_outputs_task
