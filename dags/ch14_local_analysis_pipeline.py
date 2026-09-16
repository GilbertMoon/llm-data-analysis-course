"""Legacy Chapter 14 DAG path.

The canonical Airflow 3.3.0 TaskFlow DAG is:

    automation/airflow/dags/ch14_local_analysis_pipeline.py

This legacy file intentionally defines no Airflow DAG.  The previous version
used older ``airflow.operators`` imports, a naive ``datetime`` start date and a
serial dependency chain that no longer matches the current Chapter 14 lesson.
Keeping a second DAG with the same ``dag_id`` would also risk ambiguous parsing
if both directories were ever scanned by one Airflow installation.

Use the canonical Docker Compose learning environment and DAG instead.
"""

CANONICAL_DAG_PATH = "automation/airflow/dags/ch14_local_analysis_pipeline.py"
