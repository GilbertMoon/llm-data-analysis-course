"""Chapter 14 Docker Compose 기반 Airflow DAG.

이 DAG는 온라인 쇼핑몰 분석 파이프라인을 다음 순서로 실행합니다.

check_input_files -> run_preprocessing -> run_analysis -> generate_visualizations -> generate_report -> validate_outputs

Docker Compose 기준 실행 흐름:
    cd automation/airflow
    cp .env.example .env
    docker compose up airflow-init
    docker compose up

Airflow 컨테이너 내부 프로젝트 경로는 기본적으로 /opt/airflow/project 입니다.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from src.automation_pipeline import check_input_files, validate_outputs


BASE_DIR = Path(os.getenv("PROJECT_ROOT", "/opt/airflow/project")).resolve()
PYTHON_BIN = os.getenv("PYTHON_BIN", "python")


def _check_input_files() -> None:
    check_input_files(BASE_DIR)


def _validate_outputs() -> None:
    validate_outputs(BASE_DIR)


def _script_command(script_name: str) -> str:
    return f"cd {BASE_DIR} && {PYTHON_BIN} scripts/{script_name}"


default_args = {
    "owner": "data-analysis-class",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="ch14_local_analysis_pipeline",
    description="Docker Compose로 실행하는 온라인 쇼핑몰 분석 파이프라인",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["chapter14", "docker", "airflow", "data-analysis"],
) as dag:
    check_input_files_task = PythonOperator(
        task_id="check_input_files",
        python_callable=_check_input_files,
    )

    run_preprocessing = BashOperator(
        task_id="run_preprocessing",
        bash_command=_script_command("ch14_preprocessing.py"),
    )

    run_analysis = BashOperator(
        task_id="run_analysis",
        bash_command=_script_command("ch14_analysis.py"),
    )

    generate_visualizations = BashOperator(
        task_id="generate_visualizations",
        bash_command=_script_command("ch14_visualization.py"),
    )

    generate_report = BashOperator(
        task_id="generate_report",
        bash_command=_script_command("ch14_report.py"),
    )

    validate_outputs_task = PythonOperator(
        task_id="validate_outputs",
        python_callable=_validate_outputs,
    )

    check_input_files_task >> run_preprocessing >> run_analysis >> generate_visualizations >> generate_report >> validate_outputs_task
