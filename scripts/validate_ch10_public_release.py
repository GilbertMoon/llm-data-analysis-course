"""Chapter 10 Public release QA.

공통 data/raw를 QA 임시 폴더에 전처리한 뒤 분류 파이프라인을 실행하고,
Target/Feature 계약, Validation 기반 모델·Threshold 선택, Final Test 보호,
Privacy-safe Output, Notebook, 학생 실습 문서 계약을 확인합니다.
"""

from __future__ import annotations

import json
import py_compile
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.classification import (  # noqa: E402
    FORBIDDEN_FEATURES,
    public_prediction_result,
    run_classification_analysis,
)
from src.data_loader import load_sales_data  # noqa: E402
from src.preprocessing import (  # noqa: E402
    preprocess_sales_data,
    save_processed_data,
    validate_relationships,
)


QA_DIR = ROOT / "tmp" / "ch10_public_qa"
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

    try:
        for path in [
            ROOT / "src" / "classification.py",
            ROOT / "scripts" / "prepare_ch10_data.py",
            ROOT / "scripts" / "run_classification_analysis.py",
        ]:
            py_compile.compile(str(path), doraise=True)
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
            path.exists() and path.stat().st_size > 0 for path in saved_paths
        )
        record(
            "classification_processed_prerequisite",
            processed_ready,
            f"files={[path.name for path in saved_paths]}",
        )

        result = run_classification_analysis(
            processed_dir=PROCESSED_DIR,
            report_dir=REPORT_DIR,
            random_state=42,
        )
        record("pipeline_execution", True)

        validation = result["validation"]
        validation_pass = bool(validation["status"].eq("PASS").all())
        record(
            "classification_validation",
            validation_pass,
            repr(validation.to_dict(orient="records")),
        )

        target_values = set(result["model_data"]["is_cancelled"].unique())
        target_pass = target_values == {0, 1}
        record(
            "binary_target_contract",
            target_pass,
            f"target_values={sorted(target_values)}",
        )

        selected_features = set(result["features"])
        leaked = sorted(selected_features & FORBIDDEN_FEATURES)
        record(
            "feature_leakage_contract",
            not leaked,
            f"leaked={leaked}",
        )

        merge_checks = result["merge_checks"]
        merge_pass = bool(
            merge_checks["row_count_preserved"].eq(True).all()
            and merge_checks["unmatched_count"].eq(0).all()
        )
        record(
            "strict_merge_contract",
            merge_pass,
            repr(merge_checks.to_dict(orient="records")),
        )

        split_pass = all(
            set(result[key].unique()) == {0, 1}
            for key in ["y_train", "y_validation", "y_test"]
        )
        record("all_splits_have_two_classes", split_pass)

        validation_comparison = result["validation_model_comparison"]
        selected_model = result["selected_model_name"]
        ranked_models = validation_comparison.loc[
            ~validation_comparison["model"].eq("Dummy Most Frequent")
        ].sort_values(
            ["f1", "recall", "precision", "model"],
            ascending=[False, False, False, True],
        )
        expected_model = str(ranked_models.iloc[0]["model"])
        model_selection_pass = (
            selected_model == expected_model
            and selected_model != "Dummy Most Frequent"
        )
        record(
            "validation_model_selection",
            model_selection_pass,
            f"selected={selected_model}, expected={expected_model}",
        )

        threshold_df = result["threshold_metrics"]
        selected_threshold = float(result["selected_threshold"])
        ranked_thresholds = threshold_df.sort_values(
            ["f1", "recall", "precision", "threshold"],
            ascending=[False, False, False, True],
        )
        expected_threshold = float(ranked_thresholds.iloc[0]["threshold"])
        threshold_selection_pass = bool(
            np.isclose(selected_threshold, expected_threshold)
        )
        record(
            "validation_threshold_selection",
            threshold_selection_pass,
            f"selected={selected_threshold}, expected={expected_threshold}",
        )

        test_metrics = result["test_metrics"]
        final_test_pass = bool(
            len(test_metrics) == 1
            and test_metrics["evaluation_split"].eq("test").all()
            and np.isclose(
                float(test_metrics.iloc[0]["threshold"]),
                selected_threshold,
            )
        )
        record(
            "final_test_frozen_decision",
            final_test_pass,
            test_metrics.to_string(index=False),
        )

        internal_prediction = result["prediction_result_internal"]
        public_prediction = public_prediction_result(internal_prediction)
        forbidden_public = {
            "source_index",
            "order_id",
            "customer_id",
            "product_id",
        }
        privacy_pass = (
            "source_index" in internal_prediction.columns
            and not (set(public_prediction.columns) & forbidden_public)
        )
        record(
            "internal_public_separation",
            privacy_pass,
            "internal_columns="
            f"{internal_prediction.columns.tolist()}, "
            "public_columns="
            f"{public_prediction.columns.tolist()}",
        )

        expected_outputs = [
            REPORT_DIR / "ch10_classification_model_data_internal.csv",
            REPORT_DIR / "ch10_target_distribution.csv",
            REPORT_DIR / "ch10_feature_audit.csv",
            REPORT_DIR / "ch10_merge_checks.csv",
            REPORT_DIR / "ch10_data_quality_checks.csv",
            REPORT_DIR / "ch10_split_summary.csv",
            REPORT_DIR / "ch10_validation_model_comparison.csv",
            REPORT_DIR / "ch10_validation_threshold_metrics.csv",
            REPORT_DIR / "ch10_test_metrics.csv",
            REPORT_DIR / "ch10_classification_predictions_internal.csv",
            REPORT_DIR / "ch10_classification_predictions.csv",
            REPORT_DIR / "ch10_confusion_matrix.csv",
            REPORT_DIR / "ch10_classification_report.csv",
            REPORT_DIR / "ch10_classification_validation.csv",
            REPORT_DIR / "ch10_classification_checklist.csv",
            REPORT_DIR / "ch10_classification_summary.md",
        ]
        missing = [
            str(path.relative_to(QA_DIR))
            for path in expected_outputs
            if not path.exists() or path.stat().st_size == 0
        ]
        record("required_outputs", not missing, f"missing={missing}")

        notebook_path = ROOT / "notebooks" / "ch10_llm_code_generation.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        notebook_text = json.dumps(notebook, ensure_ascii=False)
        notebook_markers = [
            "build_classification_dataset",
            "split_train_validation_test",
            "train_and_compare_on_validation",
            "select_validation_model",
            "threshold_metrics",
            "choose_threshold",
            "final_test_evaluation",
            "public_prediction_result",
            "is_cancelled",
        ]
        missing_notebook = [
            marker for marker in notebook_markers if marker not in notebook_text
        ]
        order_pass = (
            notebook_text.find("select_validation_model")
            < notebook_text.find("choose_threshold")
            < notebook_text.find("final_test_evaluation")
        )
        record(
            "notebook_contract",
            not missing_notebook and order_pass,
            f"missing={missing_notebook}, order_pass={order_pass}",
        )

        practice_text = (
            ROOT / "practice" / "chapter10" / "chapter10.md"
        ).read_text(encoding="utf-8")
        assignment_text = (
            ROOT
            / "practice"
            / "chapter10"
            / "templates"
            / "chapter10_assignment.md"
        ).read_text(encoding="utf-8")
        doc_text = practice_text + assignment_text
        doc_markers = [
            "prepare_ch10_data.py",
            "completed = 0",
            "cancelled = 1",
            "line_total = quantity × unit_price",
            "Validation",
            "Threshold",
            "Final Test",
            "Dummy Most Frequent",
            "ch10_classification_validation.csv",
            "source_index",
            "random split",
        ]
        missing_docs = [
            marker for marker in doc_markers if marker not in doc_text
        ]
        record(
            "practice_document_contract",
            not missing_docs,
            f"missing={missing_docs}",
        )

        classification_source = (
            ROOT / "src" / "classification.py"
        ).read_text(encoding="utf-8")
        source_order_pass = (
            classification_source.find(
                "selected_model_name = select_validation_model"
            )
            < classification_source.find(
                "selected_threshold = choose_threshold"
            )
            < classification_source.find(
                "y_pred_test, y_proba_test, test_metrics = final_test_evaluation"
            )
        )
        record(
            "source_selection_before_final_test",
            source_order_pass,
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
        "selected_threshold": (
            result.get("selected_threshold")
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
