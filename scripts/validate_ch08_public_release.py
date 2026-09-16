"""Chapter 08 Public release QA.

실제 data/raw를 사용해 Chapter 08 전체 파이프라인을 임시 출력 폴더에서 실행하고,
검증 Evidence·공개 고객 CSV·Notebook·실습 문서 계약을 확인합니다.
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

from src.midterm_project import (  # noqa: E402
    FORBIDDEN_CUSTOMER_COLUMNS,
    PUBLIC_CUSTOMER_COLUMNS,
    run_midterm_project,
)


QA_DIR = ROOT / "tmp" / "ch08_public_qa"
PROCESSED_DIR = QA_DIR / "processed"
REPORT_DIR = QA_DIR / "reports"
FIGURE_DIR = REPORT_DIR / "figures"
REPORT_PATH = QA_DIR / "qa_report.json"


def main() -> None:
    """Chapter 08 공개 실습 계약을 end-to-end로 검증합니다."""
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

    try:
        py_compile.compile(
            str(ROOT / "src" / "midterm_project.py"),
            doraise=True,
        )
        py_compile.compile(
            str(ROOT / "scripts" / "run_midterm_project.py"),
            doraise=True,
        )
        record("python_syntax", True)

        result = run_midterm_project(
            raw_dir=ROOT / "data" / "raw",
            processed_dir=PROCESSED_DIR,
            report_dir=REPORT_DIR,
            figure_dir=FIGURE_DIR,
            show_figures=False,
        )
        record("pipeline_execution", True)

        validation = result["project_validation"]
        validation_pass = bool(validation["status"].eq("PASS").all())
        record(
            "project_validation",
            validation_pass,
            validation.to_dict(orient="records").__repr__(),
        )

        total_check = result["analysis_tables"]["total_consistency_check"]
        total_pass = bool(total_check["matches_completed"].all())
        record(
            "total_consistency",
            total_pass,
            total_check.to_dict(orient="records").__repr__(),
        )

        customer_path = REPORT_DIR / "ch08_customer_sales.csv"
        customer_public = pd.read_csv(customer_path)
        forbidden = sorted(
            FORBIDDEN_CUSTOMER_COLUMNS.intersection(customer_public.columns)
        )
        columns_match = customer_public.columns.tolist() == PUBLIC_CUSTOMER_COLUMNS
        record(
            "public_customer_privacy",
            not forbidden and columns_match,
            f"columns={customer_public.columns.tolist()}, forbidden={forbidden}",
        )

        expected_outputs = [
            REPORT_DIR / "ch08_dataset_summary.csv",
            REPORT_DIR / "ch08_preprocessing_comparison.csv",
            REPORT_DIR / "ch08_key_duplicate_checks.csv",
            REPORT_DIR / "ch08_relationship_checks.csv",
            REPORT_DIR / "ch08_merge_checks.csv",
            REPORT_DIR / "ch08_line_total_check.csv",
            REPORT_DIR / "ch08_date_checks.csv",
            REPORT_DIR / "ch08_amount_scope_summary.csv",
            REPORT_DIR / "ch08_total_consistency_check.csv",
            REPORT_DIR / "ch08_project_validation.csv",
            REPORT_DIR / "ch08_category_sales.csv",
            REPORT_DIR / "ch08_monthly_sales.csv",
            REPORT_DIR / "ch08_customer_sales.csv",
            REPORT_DIR / "ch08_order_status_summary.csv",
            REPORT_DIR / "ch08_interpretation_notes.csv",
            FIGURE_DIR / "ch08_category_sales.png",
            FIGURE_DIR / "ch08_monthly_sales.png",
            FIGURE_DIR / "ch08_top_customers.png",
            REPORT_DIR / "ch08_midterm_report.md",
        ]
        missing = [
            str(path.relative_to(QA_DIR))
            for path in expected_outputs
            if not path.exists() or path.stat().st_size == 0
        ]
        record("required_outputs", not missing, f"missing={missing}")

        notebook_path = ROOT / "notebooks" / "ch08_midterm_project.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        notebook_text = json.dumps(notebook, ensure_ascii=False)
        notebook_markers = [
            "build_project_validation",
            "total_consistency_check",
            "FORBIDDEN_CUSTOMER_COLUMNS",
            "ch08_project_validation.csv",
            "ch08_total_consistency_check.csv",
        ]
        missing_notebook_markers = [
            marker for marker in notebook_markers if marker not in notebook_text
        ]
        record(
            "notebook_contract",
            not missing_notebook_markers,
            f"missing_markers={missing_notebook_markers}",
        )

        practice_text = (
            ROOT / "practice" / "chapter08" / "chapter08.md"
        ).read_text(encoding="utf-8")
        assignment_text = (
            ROOT
            / "practice"
            / "chapter08"
            / "templates"
            / "chapter08_assignment.md"
        ).read_text(encoding="utf-8")
        doc_markers = [
            "ch08_total_consistency_check.csv",
            "ch08_project_validation.csv",
            "public_customer_columns_safe",
        ]
        missing_doc_markers = [
            marker
            for marker in doc_markers
            if marker not in practice_text + assignment_text
        ]
        record(
            "practice_document_contract",
            not missing_doc_markers,
            f"missing_markers={missing_doc_markers}",
        )

    except Exception as exc:  # QA 결과를 남긴 뒤 실패시킵니다.
        record("unexpected_exception", False, f"{type(exc).__name__}: {exc}")

    overall = all(item["status"] == "PASS" for item in checks)
    payload = {
        "status": "PASS" if overall else "FAIL",
        "checks": checks,
    }
    REPORT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if not overall:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
