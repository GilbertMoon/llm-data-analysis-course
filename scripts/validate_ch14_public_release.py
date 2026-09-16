"""Chapter 14 public-release QA.

The validator runs the local Python pipeline only. It does NOT start Docker,
Airflow, or any external-delivery service. Repository raw CSVs are copied into
a temporary workspace so failure tests never mutate the checked-in data.
"""

from __future__ import annotations

import json
import py_compile
import shutil
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.automation_pipeline import (  # noqa: E402
    ARTIFACT_MANIFEST,
    PRIMARY_KEYS,
    check_input_files,
    run_local_pipeline,
    run_preprocessing,
    validate_outputs,
)


QA_DIR = ROOT / "tmp" / "ch14_public_qa"
WORKSPACE = QA_DIR / "workspace"
BAD_WORKSPACE = QA_DIR / "bad_workspace"
REPORT_PATH = QA_DIR / "qa_report.json"
SOURCE_RAW = ROOT / "data" / "raw"
RAW_NAMES = ["customers.csv", "products.csv", "orders.csv", "order_items.csv"]


def _prepare_workspace(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    raw_dir = path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name in RAW_NAMES:
        source = SOURCE_RAW / name
        if not source.is_file() or source.stat().st_size == 0:
            raise FileNotFoundError(f"QA 원본 파일이 없거나 비어 있습니다: {source}")
        shutil.copy2(source, raw_dir / name)


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def main() -> None:
    if QA_DIR.exists():
        shutil.rmtree(QA_DIR)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, object]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append(
            {
                "check": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    overall_pass = False

    try:
        # Syntax/static contracts. py_compile parses the DAG without importing Airflow.
        syntax_paths = [
            ROOT / "src" / "automation_pipeline.py",
            ROOT / "scripts" / "run_ch14_pipeline.py",
            ROOT / "scripts" / "validate_ch14_public_release.py",
            ROOT / "automation" / "airflow" / "dags" / "ch14_local_analysis_pipeline.py",
            ROOT / "dags" / "ch14_local_analysis_pipeline.py",
        ]
        for path in syntax_paths:
            py_compile.compile(str(path), doraise=True)
        record("python_syntax", True)

        required_primary_keys = {
            "customers": "customer_id",
            "products": "product_id",
            "orders": "order_id",
            "order_items": "order_item_id",
        }
        record(
            "primary_key_contract",
            PRIMARY_KEYS == required_primary_keys,
            repr(PRIMARY_KEYS),
        )

        # First complete local run.
        _prepare_workspace(WORKSPACE)
        input_check = check_input_files(WORKSPACE)
        record(
            "input_files",
            bool(len(input_check) == 4 and input_check["status"].eq("ok").all()),
            repr(input_check.to_dict(orient="records")),
        )

        first = run_local_pipeline(WORKSPACE)
        first_validation = first["validation_log"]
        first_ok = bool(
            not first_validation.empty
            and first_validation["status"].eq("ok").all()
        )
        record("first_local_pipeline", first_ok, first["pipeline_run_id"])

        report_dir = WORKSPACE / "reports"
        daily1 = _read(report_dir / "ch14_daily_sales.csv")
        category1 = _read(report_dir / "ch14_category_sales.csv")
        metadata1 = _read(report_dir / "ch14_pipeline_run_metadata.csv")
        run_id1 = str(first["pipeline_run_id"])
        run_ids_ok = bool(
            daily1["pipeline_run_id"].nunique() == 1
            and category1["pipeline_run_id"].nunique() == 1
            and metadata1["pipeline_run_id"].nunique() == 1
            and daily1["pipeline_run_id"].iloc[0] == run_id1
            and category1["pipeline_run_id"].iloc[0] == run_id1
            and metadata1["pipeline_run_id"].iloc[0] == run_id1
        )
        record("first_run_id_consistency", run_ids_ok, run_id1)

        totals_ok = bool(
            abs(
                float(daily1["completed_order_amount"].sum())
                - float(category1["completed_order_amount"].sum())
            )
            <= 0.01
            and abs(float(category1["amount_ratio_pct"].sum()) - 100.0) <= 0.1
        )
        record("completed_aggregate_reconciliation", totals_ok)

        manifest_path = report_dir / ARTIFACT_MANIFEST
        manifest = _read(manifest_path)
        manifest_ok = bool(
            len(manifest) == 4
            and manifest["pipeline_run_id"].eq(run_id1).all()
            and manifest["sha256"].astype(str).str.len().eq(64).all()
            and manifest["size_bytes"].gt(0).all()
            and manifest["sha256_scope"]
            .eq("byte_integrity_not_analysis_validity")
            .all()
        )
        record("artifact_manifest", manifest_ok, repr(manifest.to_dict(orient="records")))

        first_counts = {
            "daily": len(daily1),
            "category": len(category1),
        }
        first_totals = {
            "daily": float(daily1["completed_order_amount"].sum()),
            "category": float(category1["completed_order_amount"].sum()),
        }

        # Second run on the same input: no append accumulation; new run id.
        second = run_local_pipeline(WORKSPACE)
        daily2 = _read(report_dir / "ch14_daily_sales.csv")
        category2 = _read(report_dir / "ch14_category_sales.csv")
        run_id2 = str(second["pipeline_run_id"])
        idempotent = bool(
            run_id2 != run_id1
            and len(daily2) == first_counts["daily"]
            and len(category2) == first_counts["category"]
            and abs(float(daily2["completed_order_amount"].sum()) - first_totals["daily"]) <= 0.01
            and abs(float(category2["completed_order_amount"].sum()) - first_totals["category"]) <= 0.01
            and second["validation_log"]["status"].eq("ok").all()
        )
        record(
            "idempotent_second_run",
            idempotent,
            f"first={run_id1}, second={run_id2}, rows={first_counts}",
        )

        # Deterministic PK failure: duplicate one order_item_id in a separate workspace.
        _prepare_workspace(BAD_WORKSPACE)
        bad_items_path = BAD_WORKSPACE / "data" / "raw" / "order_items.csv"
        bad_items = _read(bad_items_path)
        bad_items = pd.concat([bad_items, bad_items.iloc[[0]]], ignore_index=True)
        bad_items.to_csv(bad_items_path, index=False, encoding="utf-8-sig")
        duplicate_blocked = False
        try:
            run_preprocessing(BAD_WORKSPACE)
        except ValueError:
            duplicate_blocked = True
        record("duplicate_order_item_id_fail_fast", duplicate_blocked)

        # Mixed-run validation must fail but still leave validation evidence.
        category_mixed_path = report_dir / "ch14_category_sales.csv"
        category_mixed = _read(category_mixed_path)
        category_mixed["pipeline_run_id"] = "stale-mixed-run"
        category_mixed.to_csv(category_mixed_path, index=False, encoding="utf-8-sig")
        mixed_run_blocked = False
        try:
            validate_outputs(WORKSPACE)
        except RuntimeError:
            mixed_run_blocked = True
        validation_after_failure = _read(report_dir / "ch14_airflow_validation_log.csv")
        evidence_written = bool(
            mixed_run_blocked
            and validation_after_failure["status"].eq("error").any()
            and validation_after_failure["target"]
            .astype(str)
            .str.contains("pipeline_run_id")
            .any()
        )
        record("mixed_run_fail_fast_with_evidence", evidence_written)

        # Canonical DAG contract; no Docker/Airflow startup occurs here.
        dag_text = (
            ROOT / "automation" / "airflow" / "dags" / "ch14_local_analysis_pipeline.py"
        ).read_text(encoding="utf-8")
        dag_markers = [
            "from airflow.sdk import dag, task, get_current_context",
            "schedule=None",
            "catchup=False",
            "max_active_runs=1",
            "max_active_tasks=2",
            '"retries": 0',
            'task_id="generate_visualizations"',
            "retries=1",
            "analysis_task >> [visualization_task, report_task]",
            "[visualization_task, report_task] >> validation_task",
            "data_interval_start",
            "data_interval_end",
        ]
        missing_dag = [marker for marker in dag_markers if marker not in dag_text]
        record("canonical_dag_contract", not missing_dag, f"missing={missing_dag}")

        legacy_text = (
            ROOT / "dags" / "ch14_local_analysis_pipeline.py"
        ).read_text(encoding="utf-8")
        legacy_safe = bool(
            "CANONICAL_DAG_PATH" in legacy_text
            and "from airflow" not in legacy_text
            and "with DAG(" not in legacy_text
            and "@dag(" not in legacy_text
        )
        record("legacy_duplicate_dag_retired", legacy_safe)

        env_example = (
            ROOT / "automation" / "airflow" / ".env.example"
        ).read_text(encoding="utf-8")
        env_values = {
            line.split("=", 1)[0]: line.split("=", 1)[1]
            for line in env_example.splitlines()
            if line and not line.startswith("#") and "=" in line
        }
        secret_names = [
            "AIRFLOW_DB_PASSWORD",
            "AIRFLOW_API_JWT_SECRET",
            "_AIRFLOW_WWW_USER_PASSWORD",
        ]
        secrets_empty = all(env_values.get(name) == "" for name in secret_names)
        record("env_example_has_no_secret_values", secrets_empty)

        dockerfile = (
            ROOT / "automation" / "airflow" / "Dockerfile"
        ).read_text(encoding="utf-8")
        compose = (
            ROOT / "automation" / "airflow" / "docker-compose.yml"
        ).read_text(encoding="utf-8")
        container_contract = bool(
            "ARG AIRFLOW_VERSION=3.3.0" in dockerfile
            and "pip check" in dockerfile
            and "AIRFLOW_VERSION:-3.3.0" in compose
            and "AIRFLOW_API_JWT_SECRET" in compose
            and "service_completed_successfully" in compose
            and "production deployment template" in compose
        )
        record("docker_airflow_static_contract", container_contract)

        notebook = json.loads(
            (ROOT / "notebooks" / "ch14_airflow_pipeline.ipynb").read_text(
                encoding="utf-8"
            )
        )
        notebook_text = json.dumps(notebook, ensure_ascii=False)
        notebook_markers = [
            "order_items.order_item_id",
            "pipeline_run_id",
            "run_local_pipeline",
            "validate_outputs",
            "Airflow 3 public SDK",
            "visual/report branch",
            "Validation PASS",
            "docker compose down --volumes --remove-orphans",
        ]
        missing_notebook = [m for m in notebook_markers if m not in notebook_text]
        record("notebook_contract", not missing_notebook, f"missing={missing_notebook}")

        practice = (
            ROOT / "practice" / "chapter14" / "chapter14.md"
        ).read_text(encoding="utf-8")
        assignment = (
            ROOT / "practice" / "chapter14" / "templates" / "chapter14_assignment.md"
        ).read_text(encoding="utf-8")
        docs = practice + "\n" + assignment
        doc_markers = [
            "order_items.order_item_id",
            "Pipeline Run ID",
            "Artifact Manifest",
            "Task Green",
            "Validation PASS",
            "delivery idempotency key",
            "docker compose down --volumes --remove-orphans",
            "운영 환경",
        ]
        missing_docs = [m for m in doc_markers if m not in docs]
        record("practice_document_contract", not missing_docs, f"missing={missing_docs}")

    except Exception as exc:
        record("unexpected_exception", False, repr(exc))
    finally:
        overall_pass = bool(checks) and all(
            item["status"] == "PASS" for item in checks
        )
        report = {
            "chapter": 14,
            "docker_started": False,
            "airflow_started": False,
            "external_delivery_performed": False,
            "status": "PASS" if overall_pass else "FAIL",
            "checks": checks,
        }
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
