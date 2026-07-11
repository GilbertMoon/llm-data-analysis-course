"""Chapter 14 Docker Compose based Airflow TaskFlow Dag.

The Dag is manual by default. It runs the same validated functions used by
``scripts/run_ch14_pipeline.py`` and writes deterministic files to the mounted
project directory.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.sdk import dag, task

from src.automation_pipeline import (
    check_input_files,
    generate_report,
    generate_visualizations,
    run_analysis,
    run_preprocessing,
    validate_outputs,
)


BASE_DIR = Path(
    os.getenv(
        "PROJECT_ROOT",
        "/opt/airflow/project",
    )
).resolve()

DAG_TIMEZONE = os.getenv(
    "AIRFLOW_DAG_TIMEZONE",
    "Asia/Seoul",
)


@dag(
    dag_id="ch14_local_analysis_pipeline",
    description=(
        "완료 주문 기준 쇼핑몰 분석 파이프라인 "
        "(입력 검증 → 전처리 → 분석 → 시각화 → 보고서 → 검증)"
    ),
    schedule=None,
    start_date=pendulum.datetime(
        2026,
        1,
        1,
        tz=DAG_TIMEZONE,
    ),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=2,
    default_args={
        "owner": "data-analysis-class",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    tags=[
        "chapter14",
        "docker",
        "airflow",
        "data-analysis",
    ],
)
def ch14_local_analysis_pipeline() -> None:
    """Run the Chapter 14 learning pipeline.

    This Docker Compose environment is for local learning and exploration.
    It is not a production deployment template.
    """

    @task(
        task_id="check_input_files",
        execution_timeout=timedelta(minutes=2),
    )
    def check_inputs() -> None:
        check_input_files(BASE_DIR)

    @task(
        task_id="run_preprocessing",
        execution_timeout=timedelta(minutes=10),
    )
    def preprocess() -> None:
        run_preprocessing(BASE_DIR)

    @task(
        task_id="run_analysis",
        execution_timeout=timedelta(minutes=10),
    )
    def analyze() -> None:
        run_analysis(BASE_DIR)

    @task(
        task_id="generate_visualizations",
        execution_timeout=timedelta(minutes=5),
    )
    def visualize() -> None:
        generate_visualizations(BASE_DIR)

    @task(
        task_id="generate_report",
        execution_timeout=timedelta(minutes=5),
    )
    def report() -> None:
        generate_report(BASE_DIR)

    @task(
        task_id="validate_outputs",
        execution_timeout=timedelta(minutes=5),
    )
    def validate() -> None:
        validate_outputs(BASE_DIR)

    (
        check_inputs()
        >> preprocess()
        >> analyze()
        >> visualize()
        >> report()
        >> validate()
    )


ch14_local_analysis_pipeline()
