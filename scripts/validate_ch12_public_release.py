"""Chapter 12 Public release QA.

공통 data/raw를 QA 임시 폴더에서 전처리한 뒤 Chapter 12 Generated-Code
Validation pipeline을 실행한다. 정적 스캔 대상 코드는 문자열 AST로만 분석하며
절대 실행하지 않는다.
"""

from __future__ import annotations

import json
import py_compile
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_sales_data  # noqa: E402
from src.llm_code_validation import (  # noqa: E402
    build_feature_audit,
    validate_feature_list,
)
from src.llm_code_validation_policy import run_llm_code_validation  # noqa: E402
from src.preprocessing import preprocess_sales_data, save_processed_data  # noqa: E402


QA_DIR = ROOT / "tmp" / "ch12_public_qa"
PROCESSED_DIR = QA_DIR / "processed"
REPORT_DIR = QA_DIR / "reports"
REPORT_PATH = QA_DIR / "qa_report.json"
RAW_DIR = ROOT / "data" / "raw"


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
        python_paths = [
            ROOT / "src" / "llm_code_validation.py",
            ROOT / "src" / "llm_code_validation_policy.py",
            ROOT / "scripts" / "run_llm_code_validation.py",
            ROOT / "scripts" / "validate_ch12_public_release.py",
        ]
        for path in python_paths:
            py_compile.compile(str(path), doraise=True)
        record("python_syntax", True)

        raw_data = load_sales_data(RAW_DIR)
        processed_data = preprocess_sales_data(raw_data)
        saved_paths = save_processed_data(processed_data, PROCESSED_DIR)
        processed_ready = bool(saved_paths) and all(
            path.exists() and path.stat().st_size > 0 for path in saved_paths
        )
        record(
            "processed_prerequisite",
            processed_ready,
            f"files={[path.name for path in saved_paths]}",
        )

        result = run_llm_code_validation(
            processed_dir=PROCESSED_DIR,
            report_dir=REPORT_DIR,
        )
        outputs = result["outputs"]
        record("pipeline_execution", True)

        required = outputs["required_column_check"]
        order_item_id_row = required.loc[
            required["dataset"].eq("order_items")
            & required["column"].eq("order_item_id")
        ]
        required_pass = bool(
            not required.empty
            and required["status"].eq("PASS").all()
            and len(order_item_id_row) == 1
            and order_item_id_row["status"].eq("PASS").all()
        )
        record(
            "required_columns_and_order_item_id",
            required_pass,
            repr(order_item_id_row.to_dict(orient="records")),
        )

        primary = outputs["primary_key_check"]
        relationships = outputs["relationship_check"]
        record(
            "primary_keys",
            bool(not primary.empty and primary["status"].eq("PASS").all()),
            repr(primary.to_dict(orient="records")),
        )
        record(
            "relationship_keys",
            bool(
                not relationships.empty
                and relationships["status"].eq("PASS").all()
            ),
            repr(relationships.to_dict(orient="records")),
        )

        category_validation = outputs["category_validation"]
        monthly_validation = outputs["monthly_validation"]
        aggregate_pass = bool(
            not category_validation["status"].eq("FAIL").any()
            and not monthly_validation["status"].eq("FAIL").any()
        )
        record(
            "completed_aggregate_validation",
            aggregate_pass,
            "category/monthly validation contains no FAIL",
        )

        category_diff = float(
            category_validation.loc[
                category_validation["check_item"].eq("category_total_difference"),
                "value",
            ].iloc[0]
        )
        monthly_diff = float(
            monthly_validation.loc[
                monthly_validation["check_item"].eq("monthly_total_difference"),
                "value",
            ].iloc[0]
        )
        record(
            "source_group_total_reconciliation",
            abs(category_diff) <= 1e-6 and abs(monthly_diff) <= 1e-6,
            f"category_diff={category_diff}, monthly_diff={monthly_diff}",
        )

        static_scan = outputs["static_scan"]
        blocking = static_scan["severity"].astype(str).str.lower().isin(
            ["critical", "high"]
        )
        default_gate = outputs["execution_gate"]
        default_decision = default_gate.loc[
            default_gate["gate"].eq("execution_decision"), "status"
        ].iloc[0]
        record(
            "risky_example_is_blocked",
            bool(blocking.any() and default_decision == "DO_NOT_EXECUTE"),
            f"decision={default_decision}, findings={len(static_scan)}",
        )

        clean_result = run_llm_code_validation(
            processed_dir=PROCESSED_DIR,
            report_dir=QA_DIR / "reports_clean_scan",
            code_for_static_scan="values = [1, 2, 3]\nresult = sum(values)",
        )
        clean_scan = clean_result["outputs"]["static_scan"]
        clean_gate = clean_result["outputs"]["execution_gate"]
        clean_static_status = clean_gate.loc[
            clean_gate["gate"].eq("static_scan"), "status"
        ].iloc[0]
        clean_decision = clean_gate.loc[
            clean_gate["gate"].eq("execution_decision"), "status"
        ].iloc[0]
        record(
            "clean_scan_still_requires_human_review",
            bool(
                clean_scan.empty
                and clean_static_status == "REVIEW"
                and clean_decision == "HUMAN_REVIEW_REQUIRED"
            ),
            (
                f"static={clean_static_status}, "
                f"decision={clean_decision}, findings={len(clean_scan)}"
            ),
        )

        regression_safe = [
            "payment_method",
            "order_month",
            "order_dayofweek",
            "gender",
            "age",
            "city",
        ]
        classification_safe = [
            "payment_method",
            "item_count",
            "total_quantity",
            "order_amount",
            "age",
            "city",
        ]
        validate_feature_list(regression_safe, problem="regression")
        validate_feature_list(classification_safe, problem="classification")
        classification_audit = build_feature_audit(
            classification_safe,
            problem="classification",
        )
        conditional_review = classification_audit.loc[
            classification_audit["feature"].isin(
                ["item_count", "total_quantity", "order_amount"]
            )
        ]
        record(
            "problem_specific_feature_contract",
            bool(
                len(conditional_review) == 3
                and conditional_review["status"].eq("REVIEW").all()
            ),
            repr(conditional_review.to_dict(orient="records")),
        )

        regression_blocked = False
        try:
            validate_feature_list(
                ["payment_method", "item_count"],
                problem="regression",
            )
        except ValueError:
            regression_blocked = True
        record("regression_target_material_fail_fast", regression_blocked)

        classification_blocked = False
        try:
            validate_feature_list(
                ["payment_method", "order_status"],
                problem="classification",
            )
        except ValueError:
            classification_blocked = True
        record("classification_target_leakage_fail_fast", classification_blocked)

        expected_names = {
            "ch12_dataset_inventory.csv",
            "ch12_required_column_check.csv",
            "ch12_primary_key_check.csv",
            "ch12_relationship_key_check.csv",
            "ch12_category_sales_validated.csv",
            "ch12_category_sales_validation.csv",
            "ch12_monthly_sales_validated.csv",
            "ch12_monthly_sales_validation.csv",
            "ch12_ml_leakage_review.csv",
            "ch12_generated_code_static_scan.csv",
            "ch12_execution_gate.csv",
            "ch12_sandbox_execution_checklist.csv",
            "ch12_package_install_review.csv",
            "ch12_human_revision_log.csv",
            "ch12_llm_code_review_checklist.csv",
            "ch12_error_fix_prompt_template.md",
            "ch12_code_validation_summary.md",
        }
        missing_outputs = sorted(
            name
            for name in expected_names
            if not (REPORT_DIR / name).exists()
            or (REPORT_DIR / name).stat().st_size == 0
        )
        record("required_outputs", not missing_outputs, f"missing={missing_outputs}")

        notebook = json.loads(
            (ROOT / "notebooks" / "ch12_report_generation.ipynb")
            .read_text(encoding="utf-8")
        )
        notebook_text = json.dumps(notebook, ensure_ascii=False)
        notebook_markers = [
            "order_items.order_item_id",
            "problem='regression'",
            "problem='classification'",
            "execution_gate",
            "DO_NOT_EXECUTE",
            "정적 스캔",
            "사람 승인",
        ]
        missing_notebook = [m for m in notebook_markers if m not in notebook_text]
        record(
            "notebook_contract",
            not missing_notebook,
            f"missing={missing_notebook}",
        )

        practice_text = (
            ROOT / "practice" / "chapter12" / "chapter12.md"
        ).read_text(encoding="utf-8")
        assignment_text = (
            ROOT / "practice" / "chapter12" / "templates" / "chapter12_assignment.md"
        ).read_text(encoding="utf-8")
        doc_text = practice_text + "\n" + assignment_text
        document_markers = [
            "order_items.order_item_id",
            "DO_NOT_EXECUTE",
            "HUMAN_REVIEW_REQUIRED",
            "Prediction Time",
            "Sandbox",
            "Package",
            "APPROVE",
            "REVISE",
            "BLOCK",
            "Post-execution",
        ]
        missing_docs = [m for m in document_markers if m not in doc_text]
        record(
            "practice_document_contract",
            not missing_docs,
            f"missing={missing_docs}",
        )

        runner_text = (
            ROOT / "scripts" / "run_llm_code_validation.py"
        ).read_text(encoding="utf-8")
        record(
            "runner_uses_strengthened_policy",
            "llm_code_validation_policy" in runner_text
            and "자동 PASS는 실행 승인이 아닙니다" in runner_text,
        )

    except Exception as exc:
        record("unexpected_exception", False, repr(exc))
    finally:
        overall_pass = bool(checks) and all(
            item["status"] == "PASS" for item in checks
        )
        report = {
            "chapter": 12,
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
