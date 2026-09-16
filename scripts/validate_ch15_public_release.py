"""Chapter 15 public-release QA.

The validator executes the complete local final-project pipeline in temporary
workspaces. It performs no external network collection, no Airflow startup and
no external delivery. Optional external-data behavior is tested with local
synthetic contract fixtures only.
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

from src.final_project import (  # noqa: E402
    LLM_LOG_COLUMNS,
    build_submission_status,
    run_final_project,
)


QA_DIR = ROOT / "tmp" / "ch15_public_qa"
WORKSPACE = QA_DIR / "workspace"
EXTERNAL_BAD_WORKSPACE = QA_DIR / "external_bad_workspace"
REPORT_PATH = QA_DIR / "qa_report.json"
SOURCE_RAW = ROOT / "data" / "raw"
RAW_NAMES = ["customers.csv", "products.csv", "orders.csv", "order_items.csv"]
PRIVATE_CUSTOMER_COLUMNS = {"customer_id", "name", "email", "phone", "address", "city"}


def prepare_workspace(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    raw_dir = path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name in RAW_NAMES:
        source = SOURCE_RAW / name
        if not source.is_file() or source.stat().st_size == 0:
            raise FileNotFoundError(f"QA 원본 파일이 없거나 비어 있습니다: {source}")
        shutil.copy2(source, raw_dir / name)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def main() -> None:
    if QA_DIR.exists():
        shutil.rmtree(QA_DIR)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, object]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append({
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        })

    overall_pass = False

    try:
        syntax_paths = [
            ROOT / "src" / "final_project.py",
            ROOT / "scripts" / "run_final_project.py",
            ROOT / "scripts" / "validate_ch15_public_release.py",
        ]
        for path in syntax_paths:
            py_compile.compile(str(path), doraise=True)
        record("python_syntax", True)

        prepare_workspace(WORKSPACE)
        first = run_final_project(WORKSPACE, random_state=42)
        report_dir = WORKSPACE / "reports"
        run_id1 = str(first["project_run_id"])

        validation = first["validation"]
        core_fail = validation.loc[
            validation["check"].isin([
                "required_primary_keys",
                "required_foreign_keys",
                "safe_merge_contract",
                "core_validation_gate",
                "completed_amount_consistency",
                "customer_public_privacy",
                "required_figures",
                "automation_plan_design_artifact",
            ])
            & validation["status"].ne("PASS")
        ]
        record("required_core_validation", core_fail.empty, repr(core_fail.to_dict(orient="records")))

        public_customer = first["core"]["public_tables"]["customer_sales"]
        exposed = sorted(PRIVATE_CUSTOMER_COLUMNS.intersection(public_customer.columns))
        record("public_customer_privacy", not exposed, f"exposed={exposed}")

        scope = first["core"]["public_tables"]["amount_scope_summary"].set_index("scope")
        completed_total = float(scope.loc["completed_order_items", "amount"])
        public = first["core"]["public_tables"]
        totals = {
            "category": float(public["category_sales"]["total_sales"].sum()),
            "monthly": float(public["monthly_sales"]["total_sales"].sum()),
            "customer": float(public["customer_sales"]["total_sales"].sum()),
            "product": float(public["product_sales"]["total_sales"].sum()),
        }
        totals_ok = all(abs(value - completed_total) <= 1e-6 for value in totals.values())
        record("five_total_invariant", totals_ok, f"source={completed_total}; totals={totals}")

        external_status = str(first["external"]["status"].iloc[0]["status"])
        llm_actual = first["llm_usage_validation"].loc[
            first["llm_usage_validation"]["check"].eq("actual_llm_usage")
        ]
        llm_not_executed = bool(
            not llm_actual.empty
            and int(llm_actual.iloc[0]["value"]) == 0
            and str(llm_actual.iloc[0]["status"]) == "SKIP"
        )
        record(
            "optional_stage_truthfulness",
            external_status == "skipped" and llm_not_executed,
            f"external={external_status}; llm={llm_actual.to_dict(orient='records')}",
        )

        template_path = report_dir / "ch15_holidays_template.csv"
        template = read_csv(template_path)
        template_ok = bool(
            template.empty
            and set(template.columns)
            >= {
                "date", "holiday_name", "is_holiday", "provider",
                "source_url", "data_reference_date", "license_or_terms",
            }
        )
        record("no_fake_external_data", template_ok)

        # Book contract: optional SKIP is a visible limitation, not silent READY.
        submission = first["submission_status"]
        submission_value = str(submission.iloc[0]["status"])
        skip_count = int(submission.iloc[0]["skip_count"])
        expected_status = "READY_WITH_WARNINGS" if skip_count > 0 else "READY"
        record(
            "submission_status_reflects_optional_skip",
            submission_value == expected_status,
            f"actual={submission_value}; expected={expected_status}; skip_count={skip_count}",
        )

        validation_file = read_csv(report_dir / "ch15_project_validation.csv")
        metadata = read_csv(report_dir / "ch15_project_run_metadata.csv")
        reproducibility = read_csv(report_dir / "ch15_reproducibility_manifest.csv")
        manifest = read_csv(report_dir / "ch15_project_deliverables.csv")
        submission_file = read_csv(report_dir / "ch15_submission_status.csv")
        report_text = (report_dir / "ch15_final_report.md").read_text(encoding="utf-8")

        run_id_evidence_ok = bool(
            validation_file["project_run_id"].eq(run_id1).all()
            and metadata["project_run_id"].eq(run_id1).all()
            and reproducibility["project_run_id"].eq(run_id1).all()
            and manifest["project_run_id"].eq(run_id1).all()
            and submission_file["project_run_id"].eq(run_id1).all()
            and f"`{run_id1}`" in report_text
        )
        record("project_run_id_consistency", run_id_evidence_ok, run_id1)

        required_missing = manifest.loc[
            manifest["required"] & (~manifest["exists"] | ~manifest["nonempty"])
        ]
        manifest_ok = bool(
            required_missing.empty
            and manifest.loc[manifest["nonempty"], "sha256"].astype(str).str.len().eq(64).all()
            and not manifest["path"].astype(str).str.match(r"^[A-Za-z]:[\\/]").any()
            and not manifest["path"].astype(str).str.startswith("/").any()
        )
        record("deliverable_manifest", manifest_ok, f"required_missing={required_missing['deliverable'].tolist()}")

        input_rows = reproducibility.loc[reproducibility["record_type"].eq("input_file")]
        env_rows = reproducibility.loc[reproducibility["record_type"].eq("environment")]
        reproducibility_ok = bool(
            len(input_rows) == 4
            and input_rows["sha256"].astype(str).str.len().eq(64).all()
            and set(env_rows["input_file"])
            >= {"python_version", "pandas_version", "scikit_learn_version", "matplotlib_version", "platform"}
            and reproducibility["random_state"].eq(42).all()
        )
        record("reproducibility_manifest", reproducibility_ok)

        # Human-edited LLM usage evidence must survive a rerun.
        llm_path = report_dir / "ch15_llm_usage_log.csv"
        llm_log = read_csv(llm_path, dtype=str).fillna("")
        llm_log.loc[0, LLM_LOG_COLUMNS] = [
            "executed",
            "2026-09-16T00:00:00+00:00",
            "QA Provider",
            "QA Model",
            "qa-v1",
            "분석 질문 검토",
            "비식별 집계 구조만 사용",
            "질문 범위 제안",
            "사람이 계산 범위와 논리를 재검증",
            "표현을 수정함",
            "partial",
        ]
        llm_log.to_csv(llm_path, index=False, encoding="utf-8-sig")

        second = run_final_project(WORKSPACE, random_state=42)
        run_id2 = str(second["project_run_id"])
        second_llm = read_csv(llm_path, dtype=str).fillna("")
        preserved = bool(
            run_id2 != run_id1
            and second_llm.iloc[0]["execution_status"] == "executed"
            and second_llm.iloc[0]["provider"] == "QA Provider"
            and second["llm_usage_validation"].loc[
                second["llm_usage_validation"]["check"].eq("actual_llm_usage"), "status"
            ].eq("PASS").all()
        )
        record("llm_usage_log_preserved_on_rerun", preserved, f"first={run_id1}; second={run_id2}")

        second_scope = second["core"]["public_tables"]["amount_scope_summary"].set_index("scope")
        second_completed = float(second_scope.loc["completed_order_items", "amount"])
        record(
            "rerun_same_input_core_total",
            abs(second_completed - completed_total) <= 1e-6,
            f"first={completed_total}; second={second_completed}",
        )

        # Optional malformed external file must warn and never fabricate analysis output.
        prepare_workspace(EXTERNAL_BAD_WORKSPACE)
        bad_external_dir = EXTERNAL_BAD_WORKSPACE / "data" / "external" / "processed"
        bad_external_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({
            "date": ["2026-01-01", "bad-date"],
            "holiday_name": ["테스트", "오류"],
            "is_holiday": [1, 3],
        }).to_csv(bad_external_dir / "holidays.csv", index=False, encoding="utf-8-sig")
        bad_external = run_final_project(EXTERNAL_BAD_WORKSPACE, random_state=42)
        bad_status = str(bad_external["external"]["status"].iloc[0]["status"])
        bad_quality = bad_external["external"]["quality_checks"]
        record(
            "invalid_external_contract_warns_not_fakes",
            bad_status == "warning" and bad_quality["status"].eq("FAIL").any(),
            f"status={bad_status}; quality={bad_quality.to_dict(orient='records')}",
        )

        # Submission helper must BLOCK on a required FAIL.
        synthetic_validation = pd.DataFrame([
            {"check": "required_core", "status": "FAIL", "detail": "qa"}
        ])
        synthetic_manifest = pd.DataFrame([
            {
                "deliverable": "required_file", "required": True,
                "exists": True, "nonempty": True,
            }
        ])
        blocked = build_submission_status(
            synthetic_validation,
            synthetic_manifest,
            project_run_id="qa-blocked",
            manifest_path=report_dir / "ch15_project_deliverables.csv",
            base_dir=WORKSPACE,
        )
        record(
            "required_fail_blocks_submission",
            str(blocked.iloc[0]["status"]) == "BLOCKED"
            and not bool(blocked.iloc[0]["can_submit"]),
        )

        notebook_text = json.dumps(
            json.loads((ROOT / "notebooks" / "ch15_final_project.ipynb").read_text(encoding="utf-8")),
            ensure_ascii=False,
        )
        notebook_markers = [
            "Submission Gate",
            "order_item_id",
            "completed_total = category_total = monthly_total = customer_total = product_total",
            "execution_status=not_executed",
            "provenance",
            "SHA-256",
            "BLOCKED",
        ]
        missing_notebook = [marker for marker in notebook_markers if marker not in notebook_text]
        record("notebook_contract", not missing_notebook, f"missing={missing_notebook}")

        docs = (
            ROOT / "practice" / "chapter15" / "chapter15.md"
        ).read_text(encoding="utf-8") + "\n" + (
            ROOT / "practice" / "chapter15" / "templates" / "chapter15_assignment.md"
        ).read_text(encoding="utf-8")
        doc_markers = [
            "Project Run ID",
            "order_items.order_item_id",
            "Reproducibility Manifest",
            "Deliverable Manifest",
            "Automation Plan",
            "READY_WITH_WARNINGS",
            "운영 배포 승인",
            "city",
        ]
        missing_docs = [marker for marker in doc_markers if marker not in docs]
        record("practice_document_contract", not missing_docs, f"missing={missing_docs}")

    except Exception as exc:
        record("unexpected_exception", False, repr(exc))
    finally:
        overall_pass = bool(checks) and all(item["status"] == "PASS" for item in checks)
        report = {
            "chapter": 15,
            "network_collection_performed": False,
            "airflow_started": False,
            "external_delivery_performed": False,
            "status": "PASS" if overall_pass else "FAIL",
            "checks": checks,
        }
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
