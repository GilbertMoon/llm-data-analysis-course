"""Canonical Chapter 14 Airflow 3 TaskFlow DAG.

The DAG is manual by default and uses the same validated functions as
``scripts/run_ch14_pipeline.py``.  Deterministic data/schema failures are not
blindly retried.  Visualization has one bounded retry as a teaching example.

This Docker Compose environment is for local learning and exploration only.
It is not a production deployment template.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.sdk import dag, task, get_current_context

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
        "(입력 검증 → 전처리 → 분석 → 시각화/보고서 → 검증)"
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
        "retries": 0,
    },
    tags=[
        "chapter14",
        "docker",
        "airflow",
        "data-analysis",
    ],
)
def ch14_local_analysis_pipeline() -> None:
    """Run the Chapter 14 learning pipeline with an explicit validation gate."""

    @task(
        task_id="check_input_files",
        retries=0,
        execution_timeout=timedelta(minutes=2),
    )
    def check_inputs() -> None:
        # Missing input is deterministic: fix the file first, do not blind-retry.
        check_input_files(BASE_DIR)

    @task(
        task_id="run_preprocessing",
        retries=0,
        execution_timeout=timedelta(minutes=10),
    )
    def preprocess() -> None:
        # Schema/key/reference failures require data or code correction.
        run_preprocessing(BASE_DIR)

    @task(
        task_id="run_analysis",
        retries=0,
        execution_timeout=timedelta(minutes=10),
    )
    def analyze() -> None:
        context = get_current_context()
        run_analysis(
            BASE_DIR,
            orchestration_context={
                "airflow_dag_id": context["dag"].dag_id,
                "airflow_dag_run_id": context["dag_run"].run_id,
                "airflow_logical_date": str(context.get("logical_date", "")),
                "data_interval_start": str(context.get("data_interval_start", "")),
                "data_interval_end": str(context.get("data_interval_end", "")),
            },
        )

    @task(
        task_id="generate_visualizations",
        retries=1,
        retry_delay=timedelta(minutes=1),
        execution_timeout=timedelta(minutes=5),
    )
    def visualize() -> None:
        # One bounded retry illustrates transient artifact-write recovery.
        generate_visualizations(BASE_DIR)

    @task(
        task_id="generate_report",
        retries=0,
        execution_timeout=timedelta(minutes=5),
    )
    def report() -> None:
        generate_report(BASE_DIR)

    @task(
        task_id="validate_outputs",
        retries=0,
        execution_timeout=timedelta(minutes=5),
    )
    def validate() -> None:
        # Green upstream tasks are not enough; data validation is the final gate.
        validate_outputs(BASE_DIR)

    check_task = check_inputs()
    preprocess_task = preprocess()
    analysis_task = analyze()
    visualization_task = visualize()
    report_task = report()
    validation_task = validate()

    check_task >> preprocess_task >> analysis_task
    analysis_task >> [visualization_task, report_task]
    [visualization_task, report_task] >> validation_task


ch14_local_analysis_pipeline()
