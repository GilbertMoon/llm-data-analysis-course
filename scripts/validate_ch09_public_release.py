"""Chapter 09 Public release QA.

공통 data/raw를 QA 임시 폴더에 전처리한 뒤 회귀 파이프라인을 실행하고,
Train-only 모델 선택, Final Test 보호, Evidence, Notebook, 실습 문서 계약을 확인합니다.
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

from src.data_loader import load_sales_data  # noqa: E402
from src.preprocessing import (  # noqa: E402
    preprocess_sales_data,
    save_processed_data,
    validate_relationships,
)
from src.regression import (  # noqa: E402
    FORBIDDEN_FEATURES,
    public_prediction_result,
    run_regression_analysis,
)


QA_DIR = ROOT / "tmp" / "ch09_public_qa"
PROCESSED_DIR = QA_DIR / "processed"
REPORT_DIR = QA_DIR / "reports"
FIGURE_DIR = REPORT_DIR / "figures"
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

    try:
        py_compile.compile(str(ROOT / "src" / "regression.py"), doraise=True)
        py_compile.compile(
            str(ROOT / "scripts" / "prepare_ch09_data.py"),
            doraise=True,
        )
        py_compile.compile(
            str(ROOT / "scripts" / "run_regression_analysis.py"),
            doraise=True,
        )
        record("python_syntax", True)

        raw_data = load_sales_data(RAW_DIR)
        processed_data = preprocess_sales_data(raw_data)
        relationship_checks = validate_relationships(processed_data)
        relationships_pass = bool(
            relationship_checks.empty
            or relationship_checks["invalid_count"].eq(0).all()
        )
        record(
            "common_raw_relationships",
            relationships_pass,
            repr(relationship_checks.to_dict(orient="records")),
        )
        if not relationships_pass:
            raise ValueError(
                "공통 data/raw 관계 검증에 실패했습니다:\n"
                + relationship_checks.to_string(index=False)
            )

        saved_paths = save_processed_data(processed_data, PROCESSED_DIR)
        processed_ready = all(
            path.exists() and path.stat().st_size > 0
            for path in saved_paths
        )
        record(
            "regression_processed_prerequisite",
            processed_ready,
            f"files={[path.name for path in saved_paths]}",
        )

        result = run_regression_analysis(
            processed_dir=PROCESSED_DIR,
            report_dir=REPORT_DIR,
            test_size=0.2,
            random_state=42,
        )
        record("pipeline_execution", True)

        validation = result["validation"]
        validation_pass = bool(validation["status"].eq("PASS").all())
        record(
            "regression_validation",
            validation_pass,
            repr(validation.to_dict(orient="records")),
        )

        train_data = result["train_data"]
        test_data = result["test_data"]
        strict_time = bool(
            train_data["order_date"].max().normalize()
            < test_data["order_date"].min().normalize()
        )
        record(
            "strict_time_split",
            strict_time,
            f"train_max={train_data['order_date'].max()}, "
            f"test_min={test_data['order_date'].min()}",
        )

        cv_summary = result["cv_summary"]
        selected = result["selected_model_name"]
        non_baseline = cv_summary.loc[
            ~cv_summary["model"].eq("Baseline Mean")
        ].sort_values(["cv_MAE_mean", "model"])
        expected_selected = str(non_baseline.iloc[0]["model"])
        selection_pass = (
            selected == expected_selected
            and selected != "Baseline Mean"
        )
        record(
            "train_cv_model_selection",
            selection_pass,
            f"selected={selected}, expected={expected_selected}",
        )

        comparison = result["model_comparison"]
        expected_models = {"Baseline Mean", selected}
        actual_models = set(comparison["model"])
        roles = dict(
            zip(comparison["model"], comparison["selection_role"])
        )
        final_test_pass = (
            actual_models == expected_models
            and len(comparison) == 2
            and roles.get("Baseline Mean") == "baseline"
            and roles.get(selected) == "selected_by_train_cv"
        )
        record(
            "final_test_frozen_model_only",
            final_test_pass,
            f"models={sorted(actual_models)}, roles={roles}",
        )

        feature_audit = result["feature_audit"]
        selected_features = set(
            feature_audit.loc[
                feature_audit["selected"].eq(True),
                "column",
            ]
        )
        leaked = sorted(selected_features & FORBIDDEN_FEATURES)
        record(
            "feature_leakage_contract",
            not leaked,
            f"leaked={leaked}",
        )

        expected_outputs = [
            REPORT_DIR / "ch09_regression_model_data_internal.csv",
            REPORT_DIR / "ch09_regression_split_summary.csv",
            REPORT_DIR / "ch09_regression_feature_audit.csv",
            REPORT_DIR / "ch09_regression_cv_summary.csv",
            REPORT_DIR / "ch09_regression_model_comparison.csv",
            REPORT_DIR / "ch09_regression_predictions_internal.csv",
            REPORT_DIR / "ch09_regression_validation.csv",
            REPORT_DIR / "ch09_regression_checklist.csv",
            REPORT_DIR / "ch09_regression_report.md",
            FIGURE_DIR / "ch09_actual_vs_predicted.png",
            FIGURE_DIR / "ch09_residual_histogram.png",
        ]
        missing = [
            str(path.relative_to(QA_DIR))
            for path in expected_outputs
            if not path.exists() or path.stat().st_size == 0
        ]
        record("required_outputs", not missing, f"missing={missing}")

        internal_predictions = pd.read_csv(
            REPORT_DIR / "ch09_regression_predictions_internal.csv"
        )
        public_errors = public_prediction_result(
            result["prediction_result"]
        )
        internal_public_pass = (
            "order_id" in internal_predictions.columns
            and "order_id" not in public_errors.columns
        )
        record(
            "internal_public_separation",
            internal_public_pass,
            "internal_columns="
            f"{internal_predictions.columns.tolist()}, "
            "public_columns="
            f"{public_errors.columns.tolist()}",
        )

        notebook_path = ROOT / "notebooks" / "ch09_regression_analysis.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        notebook_text = json.dumps(notebook, ensure_ascii=False)
        notebook_markers = [
            "cv_summary = cross_validate_regression_models",
            "selected_model_name = select_diagnostic_model(cv_summary)",
            "model_comparison, predictions = train_and_evaluate_models",
            "build_regression_validation",
            "Final Test에서는 Baseline과 Frozen Model만",
            "prepare_ch09_data.py",
        ]
        missing_notebook = [
            marker
            for marker in notebook_markers
            if marker not in notebook_text
        ]
        order_pass = (
            notebook_text.find(
                "cv_summary = cross_validate_regression_models"
            )
            < notebook_text.find(
                "selected_model_name = select_diagnostic_model(cv_summary)"
            )
            < notebook_text.find(
                "model_comparison, predictions = train_and_evaluate_models"
            )
        )
        record(
            "notebook_contract",
            not missing_notebook and order_pass,
            f"missing={missing_notebook}, order_pass={order_pass}",
        )

        practice_text = (
            ROOT / "practice" / "chapter09" / "chapter09.md"
        ).read_text(encoding="utf-8")
        assignment_text = (
            ROOT
            / "practice"
            / "chapter09"
            / "templates"
            / "chapter09_assignment.md"
        ).read_text(encoding="utf-8")
        doc_text = practice_text + assignment_text
        doc_markers = [
            "ch09_regression_split_summary.csv",
            "ch09_regression_feature_audit.csv",
            "ch09_regression_cv_summary.csv",
            "ch09_regression_model_comparison.csv",
            "ch09_regression_validation.csv",
            "Final Test 전에 Selected Model",
            "Frozen Model",
            "prepare_ch09_data.py",
        ]
        missing_docs = [
            marker for marker in doc_markers if marker not in doc_text
        ]
        record(
            "practice_document_contract",
            not missing_docs,
            f"missing={missing_docs}",
        )

    except Exception as exc:
        record(
            "unexpected_exception",
            False,
            f"{type(exc).__name__}: {exc}",
        )

    overall = all(item["status"] == "PASS" for item in checks)
    payload = {
        "status": "PASS" if overall else "FAIL",
        "selected_model": (
            result.get("selected_model_name")
            if "result" in locals()
            else None
        ),
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
