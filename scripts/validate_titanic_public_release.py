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
PIPELINE_PATH = PROJECT_ROOT / "models" / "titanic_final_pipeline.joblib"
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
    # 현재 Python 환경에서 Notebook Code Cell을 위에서 아래로 같은 namespace에서 실행한다.
    # Notebook에는 shell/magic 명령을 넣지 않았으므로 이 방식으로 cell-order dependency를 검증할 수 있다.
    os.environ.setdefault("MPLBACKEND", "Agg")
    namespace: dict[str, object] = {"__name__": "__main__"}
    old_cwd = Path.cwd()
    executed = 0

    try:
        os.chdir(PROJECT_ROOT)
        for index, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
            source = cell.source
            print(f"execute notebook code cell {index}")
            exec(compile(source, f"{NOTEBOOK_PATH.name}:cell-{index}", "exec"), namespace)
            executed += 1
            plt = namespace.get("plt")
            if plt is not None:
                plt.close("all")
    finally:
        os.chdir(old_cwd)

    print("notebook code-cell execution PASS:", executed)
    return executed


def validate_artifacts() -> dict[str, object]:
    if not PIPELINE_PATH.is_file():
        raise FileNotFoundError(PIPELINE_PATH)
    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(CONTRACT_PATH)

    src_path = PROJECT_ROOT / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from titanic_app.features import MODEL_FEATURE_COLUMNS, build_model_features

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("model_feature_columns") != MODEL_FEATURE_COLUMNS:
        raise RuntimeError("Model contract and shared feature module disagree.")

    pipeline = joblib.load(PIPELINE_PATH)
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
    model_input = build_model_features(new_passenger)[MODEL_FEATURE_COLUMNS]
    prediction = int(pipeline.predict(model_input)[0])

    estimator = pipeline.named_steps["model"]
    positions = np.where(estimator.classes_ == int(contract.get("positive_class", 1)))[0]
    if len(positions) != 1:
        raise RuntimeError(f"Positive class not found in classes_: {estimator.classes_}")
    probability = float(pipeline.predict_proba(model_input)[:, positions[0]][0])

    print("artifact/contract PASS")
    print("sample prediction:", prediction, "class-1 probability:", round(probability, 4))
    return {
        "final_estimator": contract.get("final_estimator"),
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

    QA_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PASS",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.executable,
        "dataset": dataset_result,
        "notebook": {
            "path": str(NOTEBOOK_PATH.relative_to(PROJECT_ROOT)),
            "executed_code_cells": executed_code_cells,
            "source_outputs_committed": False,
        },
        "artifacts": artifact_result,
        "manual_follow_up": [
            "Run: streamlit run src/titanic_app/app.py",
            "Open the app in a browser and make at least one prediction.",
            "Confirm the displayed input, prediction, probability, and limitation text.",
        ],
    }
    QA_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nPUBLIC NOTEBOOK AUTOMATED QA: PASS")
    print("report:", QA_REPORT_PATH)
    print(
        "Remaining manual gate: run Streamlit in a browser before marking "
        "PUBLIC_NOTEBOOK_EXECUTION_PASS."
    )


if __name__ == "__main__":
    main()
