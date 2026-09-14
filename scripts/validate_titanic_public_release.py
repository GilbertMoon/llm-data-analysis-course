from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import nbformat
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "titanic_ai_analysis.ipynb"
DATA_PATH = PROJECT_ROOT / "data" / "titanic" / "train.csv"
BUNDLE_PATH = PROJECT_ROOT / "models" / "titanic_model_bundle.joblib"
CONTRACT_PATH = PROJECT_ROOT / "models" / "titanic_model_contract.json"
QA_DIR = PROJECT_ROOT / "tmp" / "titanic_public_qa"
QA_REPORT_PATH = QA_DIR / "qa_report.json"

EXPECTED_SHAPE = (891, 12)
EXPECTED_TARGET_COUNTS = {0: 549, 1: 342}
EXPECTED_MISSING = {"Age": 177, "Cabin": 687, "Embarked": 2}


def run_command(args: list[str]) -> None:
    print("\n$", " ".join(args))
    subprocess.run(args, cwd=PROJECT_ROOT, check=True)


def compile_python_sources() -> None:
    targets = [
        PROJECT_ROOT / "src" / "titanic_app" / "features.py",
        PROJECT_ROOT / "src" / "titanic_app" / "app.py",
        PROJECT_ROOT / "scripts" / "titanic_modeling_smoke_test.py",
        PROJECT_ROOT / "scripts" / "check_titanic_streamlit.py",
        PROJECT_ROOT / "scripts" / "test_titanic_streamlit_ui.py",
    ]
    for path in targets:
        if not path.is_file():
            raise FileNotFoundError(path)
        py_compile.compile(str(path), doraise=True)
        print("py_compile PASS:", path.relative_to(PROJECT_ROOT))


def validate_dataset() -> dict[str, object]:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(DATA_PATH)

    df = pd.read_csv(DATA_PATH)
    if tuple(df.shape) != EXPECTED_SHAPE:
        raise RuntimeError(f"Unexpected Titanic shape: {df.shape}")

    target_counts = {
        int(k): int(v)
        for k, v in df["Survived"].astype(int).value_counts().sort_index().items()
    }
    if target_counts != EXPECTED_TARGET_COUNTS:
        raise RuntimeError(f"Unexpected target counts: {target_counts}")

    missing = {column: int(df[column].isna().sum()) for column in EXPECTED_MISSING}
    if missing != EXPECTED_MISSING:
        raise RuntimeError(f"Unexpected missing counts: {missing}")

    print("dataset PASS:", df.shape, target_counts, missing)
    return {"shape": list(df.shape), "target_counts": target_counts, "missing": missing}


def validate_clean_notebook(notebook) -> None:
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        if cell.get("execution_count") is not None:
            raise RuntimeError(f"Source notebook has execution_count at cell {index}")
        if cell.get("outputs"):
            raise RuntimeError(f"Source notebook has committed outputs at cell {index}")
    print("source notebook clean-state PASS")


def execute_notebook_code_cells(notebook) -> int:
    os.environ.setdefault("MPLBACKEND", "Agg")
    namespace: dict[str, object] = {"__name__": "__main__"}
    old_cwd = Path.cwd()
    executed = 0

    try:
        os.chdir(PROJECT_ROOT)
        for index, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
            print(f"execute notebook code cell {index}")
            exec(
                compile(cell.source, f"{NOTEBOOK_PATH.name}:cell-{index}", "exec"),
                namespace,
            )
            executed += 1
            plt = namespace.get("plt")
            if plt is not None:
                plt.close("all")
    finally:
        os.chdir(old_cwd)

    print("notebook code-cell execution PASS:", executed)
    return executed


def validate_artifacts() -> dict[str, object]:
    if not BUNDLE_PATH.is_file():
        raise FileNotFoundError(BUNDLE_PATH)
    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(CONTRACT_PATH)

    bundle = joblib.load(BUNDLE_PATH)
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    required_bundle_keys = {
        "numeric_imputer",
        "categorical_imputer",
        "encoder",
        "scaler",
        "model",
    }
    if set(bundle) != required_bundle_keys:
        raise RuntimeError(f"Unexpected bundle keys: {sorted(bundle)}")

    new_passenger = pd.DataFrame(
        [
            {
                "Pclass": 3,
                "Sex": "male",
                "Age": 30.0,
                "SibSp": 0,
                "Parch": 0,
                "Fare": 10.0,
                "Embarked": "S",
            }
        ]
    )
    new_passenger["FamilySize"] = (
        new_passenger["SibSp"] + new_passenger["Parch"] + 1
    )
    new_passenger["IsAlone"] = (
        new_passenger["FamilySize"] == 1
    ).astype(int)

    numeric_features = contract["numeric_features"]
    categorical_features = contract["categorical_features"]

    num_imputed = bundle["numeric_imputer"].transform(new_passenger[numeric_features])
    num_scaled = bundle["scaler"].transform(num_imputed)

    cat_imputed = bundle["categorical_imputer"].transform(
        new_passenger[categorical_features]
    )
    cat_encoded = bundle["encoder"].transform(cat_imputed)

    prepared_array = np.hstack([num_scaled, cat_encoded])
    prepared_columns = contract["prepared_feature_columns"]
    model_input = pd.DataFrame(prepared_array, columns=prepared_columns)

    model = bundle["model"]
    prediction = int(model.predict(model_input)[0])
    positive_class = int(contract.get("positive_class", 1))
    positions = np.where(model.classes_ == positive_class)[0]
    if len(positions) != 1:
        raise RuntimeError(f"Positive class not found in classes_: {model.classes_}")
    probability = float(model.predict_proba(model_input)[:, positions[0]][0])

    print("artifact/contract PASS")
    print("sample prediction:", prediction, "class-1 probability:", round(probability, 4))
    return {
        "final_estimator": contract.get("final_estimator"),
        "scaling": contract.get("scaling"),
        "sample_prediction": prediction,
        "sample_class_1_probability": probability,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the public Titanic student notebook and model-serving contract."
    )
    parser.add_argument(
        "--skip-smoke-test",
        action="store_true",
        help="Skip the separate modeling smoke test when only Notebook execution is needed.",
    )
    args = parser.parse_args()

    print("Titanic public release QA")
    print("project root:", PROJECT_ROOT)
    print("python:", sys.executable)

    compile_python_sources()

    run_command([sys.executable, "scripts/prepare_titanic_data.py"])
    dataset_result = validate_dataset()

    if not args.skip_smoke_test:
        run_command([sys.executable, "scripts/titanic_modeling_smoke_test.py"])

    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    nbformat.validate(notebook)
    print("nbformat PASS")
    validate_clean_notebook(notebook)
    executed_code_cells = execute_notebook_code_cells(notebook)
    artifact_result = validate_artifacts()

    run_command([sys.executable, "scripts/test_titanic_streamlit_ui.py"])
    run_command([sys.executable, "scripts/check_titanic_streamlit.py"])

    QA_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PUBLIC_NOTEBOOK_EXECUTION_PASS",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.executable,
        "dataset": dataset_result,
        "notebook": {
            "path": str(NOTEBOOK_PATH.relative_to(PROJECT_ROOT)),
            "executed_code_cells": executed_code_cells,
            "source_outputs_committed": False,
        },
        "artifacts": artifact_result,
        "streamlit": {
            "app_test_form_submit": "PASS",
            "headless_health": "PASS",
            "page_http_response": "PASS",
        },
    }
    QA_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nPUBLIC_NOTEBOOK_EXECUTION_PASS")
    print("report:", QA_REPORT_PATH)


if __name__ == "__main__":
    main()
