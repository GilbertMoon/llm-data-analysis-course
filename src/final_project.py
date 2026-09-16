"""Chapter 15 reproducible final-project pipeline.

Required core analysis is fail-fast. Classification, external data and LLM use
are optional and leave explicit status evidence. Public artifacts avoid direct
customer identifiers and absolute local filesystem paths. The final submission
gate combines project validation with required artifact existence.
"""
from __future__ import annotations

import json
import platform
import re
import tempfile
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from src.classification import (
    build_classification_checklist,
    build_classification_dataset,
    build_classification_validation,
    build_feature_audit,
    build_selection_summary,
    build_split_summary,
    choose_threshold,
    classification_report_dataframe,
    confusion_matrix_dataframe,
    create_prediction_result,
    final_test_evaluation,
    select_validation_model,
    split_train_validation_test,
    target_distribution,
    threshold_metrics,
    train_and_compare_on_validation,
)
from src.data_loader import load_sales_data
from src.external_data_collection import merge_external_data, redact_url, sha256_file
from src.midterm_project import (
    build_analysis_tables,
    build_key_duplicate_checks,
    build_project_validation as build_midterm_project_validation,
    summarize_datasets,
)
from src.preprocessing import (
    compare_shapes,
    preprocess_sales_data,
    save_processed_data,
    validate_relationships,
)
from src.visualization import setup_korean_font

TOTAL_TOLERANCE = 1e-6
HOLIDAY_REQUIRED_COLUMNS = {"date", "holiday_name", "is_holiday"}
HOLIDAY_PROVENANCE_COLUMNS = {
    "provider",
    "source_url",
    "data_reference_date",
    "license_or_terms",
}
RAW_INPUT_FILES = ("customers.csv", "products.csv", "orders.csv", "order_items.csv")
LLM_LOG_COLUMNS = [
    "execution_status",
    "executed_at",
    "provider",
    "model",
    "prompt_version",
    "step",
    "input_summary",
    "response_summary",
    "validation_result",
    "revision_note",
    "final_use",
]
LLM_SECRET_PATTERN = re.compile(
    r"(?i)(api[_ -]?key|client[_ -]?secret|access[_ -]?token|password)\s*[:=]\s*\S+"
)
CLASSIFICATION_SKIP_MARKERS = (
    "completed 또는 cancelled 주문이 없어",
    "completed와 cancelled 두 클래스",
    "각 클래스에 최소 5개 주문",
    "층화 train/validation/test 분할에 필요한 클래스 표본",
    "데이터에 두 클래스가 모두 포함되지",
)


def get_project_paths(base_dir: str | Path = ".") -> dict[str, Path]:
    """Create and return project directories."""
    base_path = Path(base_dir).resolve()
    external_root = base_path / "data" / "external"
    paths = {
        "base_dir": base_path,
        "raw_dir": base_path / "data" / "raw",
        "processed_dir": base_path / "data" / "processed",
        "external_root": external_root,
        "external_raw_dir": external_root / "raw",
        "external_processed_dir": external_root / "processed",
        "external_metadata_dir": external_root / "metadata",
        "report_dir": base_path / "reports",
        "figure_dir": base_path / "reports" / "figures",
    }
    for key, path in paths.items():
        if key != "raw_dir":
            path.mkdir(parents=True, exist_ok=True)
    return paths


def _relative_project_path(path: str | Path, base_dir: str | Path) -> str:
    """Return a public-safe project-relative path, never a user home path."""
    target = Path(path).resolve()
    root = Path(base_dir).resolve()
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return target.name


def _atomic_csv(frame: pd.DataFrame, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        frame.to_csv(temporary, index=False, encoding="utf-8-sig")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def _atomic_text(text: str, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output.parent, suffix=".tmp", delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    try:
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def _atomic_figure(figure: plt.Figure, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".png", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        figure.savefig(temporary, dpi=150, bbox_inches="tight")
        temporary.replace(output)
    finally:
        plt.close(figure)
        temporary.unlink(missing_ok=True)
    return output


def _new_project_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"ch15-{timestamp}-{uuid.uuid4().hex[:8]}"


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "NOT_INSTALLED"


def build_reproducibility_manifest(paths: dict[str, Path]) -> pd.DataFrame:
    """Fingerprint source inputs and record a conservative environment contract."""
    rows: list[dict[str, Any]] = []
    for name in RAW_INPUT_FILES:
        path = paths["raw_dir"] / name
        exists = path.is_file()
        rows.append({
            "record_type": "input_file",
            "input_file": _relative_project_path(path, paths["base_dir"]),
            "size_bytes": path.stat().st_size if exists else 0,
            "sha256": sha256_file(path) if exists and path.stat().st_size else "",
            "modified_at_utc": datetime.fromtimestamp(
                path.stat().st_mtime, timezone.utc
            ).isoformat() if exists else "MISSING",
            "value": "",
        })
    environment = {
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "scikit_learn_version": _package_version("scikit-learn"),
        "matplotlib_version": _package_version("matplotlib"),
        "platform": platform.platform(),
        "code_revision": "UNKNOWN",
    }
    rows.extend({
        "record_type": "environment", "input_file": key, "size_bytes": "",
        "sha256": "", "modified_at_utc": "", "value": value,
    } for key, value in environment.items())
    return pd.DataFrame(rows)


def prepare_core_analysis(base_dir: str | Path = ".") -> dict[str, Any]:
    """Run required preprocessing, relationship checks and completed-order EDA."""
    paths = get_project_paths(base_dir)
    raw_data = load_sales_data(paths["raw_dir"])
    dataset_summary = summarize_datasets(raw_data)
    processed = preprocess_sales_data(raw_data)
    preprocessing_comparison = compare_shapes(raw_data, processed)
    key_duplicate_checks = build_key_duplicate_checks(processed)
    relationship_checks = validate_relationships(processed)

    failed_keys = key_duplicate_checks.loc[key_duplicate_checks["status"].ne("PASS")]
    if not failed_keys.empty:
        raise ValueError("최종 프로젝트 기본 키 검증 실패:\n" + failed_keys.to_string(index=False))
    if not relationship_checks.empty:
        failed_relationships = relationship_checks.loc[
            relationship_checks["invalid_count"].fillna(0).gt(0)
        ]
        if not failed_relationships.empty:
            raise ValueError(
                "최종 프로젝트 외래키 관계 검증 실패:\n"
                + failed_relationships.to_string(index=False)
            )

    save_processed_data(
        processed,
        output_dir=paths["processed_dir"],
        encoding="utf-8-sig",
    )
    tables = build_analysis_tables(processed)

    customer_sales_public = tables["customer_sales"].drop(
        columns=["customer_id", "name", "email", "phone", "address", "city"],
        errors="ignore",
    )

    completed_items = tables["completed_sales_items"]
    product_group_columns = [
        column
        for column in ["product_id", "product_name", "category", "price"]
        if column in completed_items.columns
    ]
    if not product_group_columns:
        raise ValueError("상품별 완료 주문 기준 금액을 집계할 상품 컬럼이 없습니다.")
    product_sales = (
        completed_items.groupby(product_group_columns, as_index=False)
        .agg(
            total_quantity=("quantity", "sum"),
            total_sales=("line_total", "sum"),
        )
        .sort_values("total_sales", ascending=False)
        .reset_index(drop=True)
    )
    product_sales["avg_unit_amount"] = (
        product_sales["total_sales"]
        / product_sales["total_quantity"].replace(0, pd.NA)
    ).round(0)

    public_tables = {
        "category_sales": tables["category_sales"],
        "monthly_sales": tables["monthly_sales"],
        "customer_sales": customer_sales_public,
        "product_sales": product_sales,
        "order_status_summary": tables["order_status_summary"],
        "amount_scope_summary": tables["amount_scope_summary"],
        "merge_checks": tables["merge_checks"],
        "total_consistency_check": tables["total_consistency_check"],
        "core_validation": build_midterm_project_validation(
    key_duplicate_checks,
    relationship_checks,
    tables,
),
    }

    return {
        "paths": paths,
        "raw_data": raw_data,
        "processed": processed,
        "dataset_summary": dataset_summary,
        "preprocessing_comparison": preprocessing_comparison,
        "key_duplicate_checks": key_duplicate_checks,
        "relationship_checks": relationship_checks,
        "analysis_tables": tables,
        "public_tables": public_tables,
    }


def save_core_outputs(core: dict[str, Any]) -> dict[str, Path]:
    """Save required public-safe core Evidence."""
    report_dir = core["paths"]["report_dir"]
    outputs = {
        "dataset_summary": report_dir / "ch15_dataset_summary.csv",
        "preprocessing_comparison": report_dir / "ch15_preprocessing_comparison.csv",
        "key_duplicate_checks": report_dir / "ch15_key_duplicate_checks.csv",
        "relationship_checks": report_dir / "ch15_relationship_checks.csv",
        "merge_checks": report_dir / "ch15_merge_checks.csv",
        "amount_scope_summary": report_dir / "ch15_amount_scope_summary.csv",
        "total_consistency_check": report_dir / "ch15_total_consistency_check.csv",
        "core_validation": report_dir / "ch15_core_validation.csv",
        "category_sales": report_dir / "ch15_category_sales.csv",
        "monthly_sales": report_dir / "ch15_monthly_sales.csv",
        "customer_sales": report_dir / "ch15_customer_sales.csv",
        "product_sales": report_dir / "ch15_product_sales.csv",
        "order_status_summary": report_dir / "ch15_order_status_summary.csv",
    }
    frames = {
        "dataset_summary": core["dataset_summary"],
        "preprocessing_comparison": core["preprocessing_comparison"],
        "key_duplicate_checks": core["key_duplicate_checks"],
        "relationship_checks": core["relationship_checks"],
        **core["public_tables"],
    }
    for name, path in outputs.items():
        _atomic_csv(frames[name], path)
    return outputs


def generate_project_figures(
    public_tables: dict[str, pd.DataFrame],
    figure_dir: str | Path,
) -> dict[str, Path]:
    """Generate four figures with scope and privacy aligned to public tables."""
    output_dir = Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_korean_font()
    outputs: dict[str, Path] = {}

    category = public_tables["category_sales"]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(category["category"], category["total_sales"])
    axis.set(
        title="카테고리별 완료 주문 기준 금액",
        xlabel="카테고리",
        ylabel="완료 주문 기준 금액",
    )
    axis.tick_params(axis="x", rotation=45)
    axis.set_ylim(bottom=0)
    figure.tight_layout()
    outputs["category_sales"] = _atomic_figure(
        figure, output_dir / "ch15_category_sales.png"
    )

    monthly = public_tables["monthly_sales"]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(monthly["order_month"], monthly["total_sales"], marker="o")
    axis.set(
        title="월별 완료 주문 기준 금액",
        xlabel="주문 월",
        ylabel="완료 주문 기준 금액",
    )
    axis.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    outputs["monthly_sales"] = _atomic_figure(
        figure, output_dir / "ch15_monthly_sales.png"
    )

    customer = public_tables["customer_sales"].head(10).copy().sort_values("total_sales")
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.barh(customer["customer_label"], customer["total_sales"])
    axis.set(
        title="완료 주문 구매 금액 상위 익명 고객군",
        xlabel="완료 주문 기준 구매 금액",
        ylabel="익명 고객 라벨",
    )
    axis.set_xlim(left=0)
    figure.tight_layout()
    outputs["top_customers"] = _atomic_figure(
        figure, output_dir / "ch15_top_customers.png"
    )

    status = public_tables["order_status_summary"]
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(status["order_status"].astype(str), status["order_count"])
    axis.set(title="주문 상태별 주문 수", xlabel="주문 상태", ylabel="주문 수")
    axis.set_ylim(bottom=0)
    figure.tight_layout()
    outputs["order_status"] = _atomic_figure(
        figure, output_dir / "ch15_order_status.png"
    )
    return outputs


def _classification_skip_reason(message: str) -> bool:
    return any(marker in message for marker in CLASSIFICATION_SKIP_MARKERS)


def run_classification_stage(
    processed: dict[str, pd.DataFrame],
    report_dir: str | Path,
    *,
    random_state: int = 42,
) -> dict[str, Any]:
    """Run Chapter 10 rules as an optional classification stage."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        (
            model_data,
            numeric_features,
            categorical_features,
            merge_checks,
            data_quality_checks,
        ) = build_classification_dataset(
            customers=processed["customers"],
            orders=processed["orders"],
            order_items=processed["order_items"],
        )
        target_dist = target_distribution(model_data)
        feature_audit = build_feature_audit(numeric_features, categorical_features)
        (
            X_train,
            X_valid,
            X_test,
            y_train,
            y_valid,
            y_test,
            features,
        ) = split_train_validation_test(
            model_data,
            numeric_features,
            categorical_features,
            random_state=random_state,
        )
        split_summary = build_split_summary(y_train, y_valid, y_test)
        (
            models,
            validation_comparison,
            _validation_predictions,
            validation_probabilities,
        ) = train_and_compare_on_validation(
            X_train,
            X_valid,
            y_train,
            y_valid,
            numeric_features,
            categorical_features,
            random_state=random_state,
        )
        selected_model_name = select_validation_model(validation_comparison)
        selected_model = models[selected_model_name]
        threshold_df = threshold_metrics(
            y_valid, validation_probabilities[selected_model_name]
        )
        selected_threshold = choose_threshold(threshold_df)
        selection_summary = build_selection_summary(
            selected_model_name,
            selected_threshold,
            validation_comparison,
            threshold_df,
        )
        y_pred_test, y_proba_test, test_metrics = final_test_evaluation(
            selected_model,
            X_test,
            y_test,
            threshold=selected_threshold,
            model_name=selected_model_name,
        )
        confusion_df = confusion_matrix_dataframe(y_test, y_pred_test)
        report_df = classification_report_dataframe(y_test, y_pred_test)
        predictions = create_prediction_result(
            y_test=y_test,
            y_pred=y_pred_test,
            y_proba=y_proba_test,
            model_name=selected_model_name,
            threshold=selected_threshold,
        )
        classification_validation = build_classification_validation(
            model_data=model_data,
            features=features,
            merge_checks=merge_checks,
            y_train=y_train,
            y_valid=y_valid,
            y_test=y_test,
            validation_comparison=validation_comparison,
            selected_model_name=selected_model_name,
            selected_threshold=selected_threshold,
            threshold_df=threshold_df,
            test_metrics=test_metrics,
            prediction_result=predictions,
        )
        checklist = build_classification_checklist()

        frames = {
            "classification_target_distribution": target_dist,
            "classification_feature_audit": feature_audit,
            "classification_merge_checks": merge_checks,
            "classification_data_quality_checks": data_quality_checks,
            "classification_split_summary": split_summary,
            "classification_validation_comparison": validation_comparison,
            "classification_selection_summary": selection_summary,
            "classification_threshold_metrics": threshold_df,
            "classification_test_metrics": test_metrics,
            "classification_predictions": predictions,
            "classification_confusion_matrix": confusion_df.reset_index(names="actual_class"),
            "classification_report": report_df,
            "classification_validation": classification_validation,
            "classification_checklist": checklist,
        }
        output_paths: dict[str, Path] = {}
        for name, frame in frames.items():
            path = output_dir / f"ch15_{name}.csv"
            _atomic_csv(frame, path)
            output_paths[name] = path

        status = pd.DataFrame(
            [
                {
                    "stage": "classification",
                    "status": "completed",
                    "reason_type": "completed",
                    "selected_model": selected_model_name,
                    "selected_threshold": selected_threshold,
                    "feature_count": len(features),
                    "note": "모델과 임계값은 validation에서 고정하고 test는 최종 평가에만 사용",
                }
            ]
        )
        status_path = output_dir / "ch15_classification_status.csv"
        _atomic_csv(status, status_path)
        output_paths["classification_status"] = status_path
        return {
            "status": status,
            "model_data": model_data,
            "validation_comparison": validation_comparison,
            "test_metrics": test_metrics,
            "confusion_matrix": confusion_df,
            "selected_model_name": selected_model_name,
            "selected_threshold": selected_threshold,
            "output_paths": output_paths,
        }
    except ValueError as exc:
        message = str(exc)
        expected_skip = _classification_skip_reason(message)
        status = pd.DataFrame(
            [
                {
                    "stage": "classification",
                    "status": "skipped" if expected_skip else "warning",
                    "reason_type": (
                        "insufficient_data"
                        if expected_skip
                        else "optional_stage_contract_error"
                    ),
                    "selected_model": "",
                    "selected_threshold": "",
                    "feature_count": "",
                    "note": message,
                }
            ]
        )
        status_path = output_dir / "ch15_classification_status.csv"
        _atomic_csv(status, status_path)
        return {
            "status": status,
            "model_data": pd.DataFrame(),
            "validation_comparison": pd.DataFrame(),
            "test_metrics": pd.DataFrame(),
            "confusion_matrix": pd.DataFrame(),
            "selected_model_name": "",
            "selected_threshold": None,
            "output_paths": {"classification_status": status_path},
        }


def create_holiday_template(report_dir: str | Path) -> Path:
    """Create an empty provenance-aware template, not synthetic external data."""
    path = Path(report_dir) / "ch15_holidays_template.csv"
    _atomic_csv(
        pd.DataFrame(
            columns=[
                "date",
                "holiday_name",
                "is_holiday",
                "provider",
                "source_url",
                "data_reference_date",
                "license_or_terms",
            ]
        ),
        path,
    )
    return path


def _external_stage_result(
    *,
    paths: dict[str, Path],
    template_path: Path,
    status_value: str,
    reason_type: str,
    note: str,
    source_file: Path,
    source_hash: str = "",
    quality_checks: pd.DataFrame | None = None,
) -> dict[str, Any]:
    status = pd.DataFrame(
        [
            {
                "stage": "external_integration",
                "status": status_value,
                "reason_type": reason_type,
                "source_file": _relative_project_path(source_file, paths["base_dir"]),
                "source_sha256": source_hash,
                "note": note,
            }
        ]
    )
    status_path = paths["report_dir"] / "ch15_external_integration_status.csv"
    quality_path = paths["report_dir"] / "ch15_external_quality_checks.csv"
    if quality_checks is None:
        quality_checks = pd.DataFrame(
            [{"check": "external_stage", "value": status_value, "status": "WARN"}]
        )
    _atomic_csv(status, status_path)
    _atomic_csv(quality_checks, quality_path)
    return {
        "status": status,
        "comparison": pd.DataFrame(),
        "merge_check": pd.DataFrame(),
        "quality_checks": quality_checks,
        "output_paths": {
            "external_status": status_path,
            "external_quality_checks": quality_path,
            "holiday_template": template_path,
        },
    }


def _normalise_is_holiday(series: pd.Series) -> pd.Series:
    mapping = {
        "1": 1,
        "0": 0,
        "true": 1,
        "false": 0,
        "yes": 1,
        "no": 0,
        "holiday": 1,
        "normal": 0,
        "공휴일": 1,
        "일반일": 0,
    }
    text_values = series.astype("string").str.strip().str.lower().map(mapping)
    numeric_values = pd.to_numeric(series, errors="coerce")
    normalized = text_values.fillna(numeric_values)
    return normalized.where(normalized.isin([0, 1]), pd.NA).astype("Int64")


def _load_holiday_metadata(paths: dict[str, Path]) -> dict[str, str]:
    """Load separated provenance metadata; processed-column fallback remains readable."""
    json_path = paths["external_metadata_dir"] / "holidays.json"
    csv_path = paths["external_metadata_dir"] / "holidays.csv"
    try:
        if json_path.is_file():
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            return {str(key): str(value) for key, value in payload.items()}
        if csv_path.is_file():
            frame = pd.read_csv(csv_path, dtype="string").fillna("")
            return frame.iloc[0].astype(str).to_dict() if not frame.empty else {}
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return {}


def run_external_integration_stage(
    analysis_tables: dict[str, pd.DataFrame],
    paths: dict[str, Path],
) -> dict[str, Any]:
    """Integrate a real holiday file only after provenance and coverage checks."""
    holiday_path = paths["external_processed_dir"] / "holidays.csv"
    template_path = create_holiday_template(paths["report_dir"])
    if not holiday_path.exists():
        return _external_stage_result(
            paths=paths,
            template_path=template_path,
            status_value="skipped",
            reason_type="source_file_missing",
            note="실제 출처의 holidays.csv가 없어 외부 데이터 단계를 건너뜁니다.",
            source_file=holiday_path,
        )

    source_hash = sha256_file(holiday_path)
    try:
        holidays = pd.read_csv(holiday_path)
    except Exception as exc:
        return _external_stage_result(
            paths=paths,
            template_path=template_path,
            status_value="warning",
            reason_type="source_file_unreadable",
            note=f"holidays.csv를 읽지 못해 통합하지 않았습니다: {type(exc).__name__}",
            source_file=holiday_path,
            source_hash=source_hash,
        )

    metadata = _load_holiday_metadata(paths)
    for column in HOLIDAY_PROVENANCE_COLUMNS:
        if column not in holidays.columns and metadata.get(column, "").strip():
            holidays[column] = metadata[column]

    missing_required = sorted(HOLIDAY_REQUIRED_COLUMNS - set(holidays.columns))
    missing_provenance = sorted(HOLIDAY_PROVENANCE_COLUMNS - set(holidays.columns))
    provenance_missing_rows: dict[str, int] = {}
    for column in sorted(HOLIDAY_PROVENANCE_COLUMNS & set(holidays.columns)):
        clean = holidays[column].astype("string").str.strip().replace("", pd.NA)
        missing_count = int(clean.isna().sum())
        if missing_count:
            provenance_missing_rows[column] = missing_count

    original_missing_dates = int(holidays["date"].isna().sum()) if "date" in holidays else 0
    parsed_dates = (
        pd.to_datetime(holidays["date"], errors="coerce")
        if "date" in holidays
        else pd.Series(dtype="datetime64[ns]")
    )
    date_parse_failures = (
        max(0, int(parsed_dates.isna().sum()) - original_missing_dates)
        if "date" in holidays
        else 0
    )
    normalized_holiday = (
        _normalise_is_holiday(holidays["is_holiday"])
        if "is_holiday" in holidays
        else pd.Series(dtype="Int64")
    )
    invalid_holiday_values = int(normalized_holiday.isna().sum()) if "is_holiday" in holidays else 0

    quality_checks = pd.DataFrame(
        [
            {
                "check": "required_columns",
                "value": ",".join(missing_required) if missing_required else "none",
                "status": "FAIL" if missing_required else "PASS",
            },
            {
                "check": "provenance_columns",
                "value": ",".join(missing_provenance) if missing_provenance else "none",
                "status": "FAIL" if missing_provenance else "PASS",
            },
            {
                "check": "provenance_missing_rows",
                "value": str(provenance_missing_rows) if provenance_missing_rows else "none",
                "status": "FAIL" if provenance_missing_rows else "PASS",
            },
            {
                "check": "date_parse_failures",
                "value": date_parse_failures,
                "status": "FAIL" if date_parse_failures else "PASS",
            },
            {
                "check": "invalid_is_holiday_values",
                "value": invalid_holiday_values,
                "status": "FAIL" if invalid_holiday_values else "PASS",
            },
        ]
    )
    if quality_checks["status"].eq("FAIL").any():
        return _external_stage_result(
            paths=paths,
            template_path=template_path,
            status_value="warning",
            reason_type="source_contract_failed",
            note="외부 파일의 컬럼·provenance·날짜·공휴일 값 검증에 실패해 분석에 사용하지 않았습니다.",
            source_file=holiday_path,
            source_hash=source_hash,
            quality_checks=quality_checks,
        )

    holidays = holidays.copy()
    holidays["date"] = parsed_dates
    holidays["is_holiday"] = normalized_holiday.astype(int)
    holidays["order_day"] = holidays["date"].dt.date
    duplicate_dates = int(holidays["order_day"].duplicated().sum())
    quality_checks = pd.concat(
        [
            quality_checks,
            pd.DataFrame(
                [
                    {
                        "check": "duplicate_dates",
                        "value": duplicate_dates,
                        "status": "FAIL" if duplicate_dates else "PASS",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    if duplicate_dates:
        return _external_stage_result(
            paths=paths,
            template_path=template_path,
            status_value="warning",
            reason_type="duplicate_external_key",
            note="외부 파일 날짜 키가 중복되어 분석에 사용하지 않았습니다.",
            source_file=holiday_path,
            source_hash=source_hash,
            quality_checks=quality_checks,
        )

    completed_orders = analysis_tables["completed_order_sales"].copy()
    completed_orders["order_day"] = pd.to_datetime(
        completed_orders["order_date"], errors="coerce"
    ).dt.date
    if completed_orders["order_day"].isna().any():
        return _external_stage_result(
            paths=paths,
            template_path=template_path,
            status_value="warning",
            reason_type="internal_date_invalid",
            note="내부 completed 주문 날짜에 변환 실패가 있어 외부 데이터와 연결하지 않았습니다.",
            source_file=holiday_path,
            source_hash=source_hash,
            quality_checks=quality_checks,
        )

    daily_completed = (
        completed_orders.groupby("order_day", as_index=False)
        .agg(
            completed_order_amount=("line_total", "sum"),
            completed_order_count=("order_id", "nunique"),
        )
        .sort_values("order_day")
        .reset_index(drop=True)
    )
    holiday_lookup = holidays[["order_day", "holiday_name", "is_holiday"]].copy()
    merged, merge_check = merge_external_data(
        daily_completed,
        holiday_lookup,
        on="order_day",
        how="left",
        validate="many_to_one",
    )
    left_only_count = int(merge_check.iloc[0].get("left_only_count", 0))
    both_count = int(merge_check.iloc[0].get("both_count", 0))
    quality_checks = pd.concat(
        [
            quality_checks,
            pd.DataFrame(
                [
                    {
                        "check": "internal_dates_matched",
                        "value": f"matched={both_count}; unmatched={left_only_count}",
                        "status": "PASS" if left_only_count == 0 and both_count > 0 else "WARN",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    matched = merged.dropna(subset=["is_holiday"]).copy()
    if matched.empty:
        return _external_stage_result(
            paths=paths,
            template_path=template_path,
            status_value="warning",
            reason_type="no_date_overlap",
            note="내부 분석 기간과 외부 파일 날짜가 겹치지 않아 통합하지 않았습니다.",
            source_file=holiday_path,
            source_hash=source_hash,
            quality_checks=quality_checks,
        )
    matched["is_holiday"] = matched["is_holiday"].astype(int)
    comparison = (
        matched.groupby("is_holiday", as_index=False)
        .agg(
            day_count=("order_day", "count"),
            avg_daily_completed_amount=("completed_order_amount", "mean"),
            avg_completed_order_count=("completed_order_count", "mean"),
            total_completed_amount=("completed_order_amount", "sum"),
        )
    )
    comparison["day_type"] = comparison["is_holiday"].map({0: "일반일", 1: "공휴일"})
    comparison = comparison[
        [
            "day_type",
            "day_count",
            "avg_daily_completed_amount",
            "avg_completed_order_count",
            "total_completed_amount",
        ]
    ]
    both_day_types = set(comparison["day_type"]) == {"일반일", "공휴일"}
    stage_status = "completed" if left_only_count == 0 and both_day_types else "warning"
    note = (
        "외부 날짜가 내부 기간을 모두 덮고 공휴일·일반일 표본을 모두 확인"
        if stage_status == "completed"
        else "일부 날짜 미매칭 또는 한쪽 day type 부족으로 해석 범위를 제한"
    )
    status = pd.DataFrame(
        [
            {
                "stage": "external_integration",
                "status": stage_status,
                "reason_type": "completed" if stage_status == "completed" else "coverage_warning",
                "source_file": _relative_project_path(holiday_path, paths["base_dir"]),
                "source_sha256": source_hash,
                "provider": str(holidays["provider"].iloc[0]),
                "source_url": redact_url(str(holidays["source_url"].iloc[0])),
                "data_reference_date": str(holidays["data_reference_date"].iloc[0]),
                "license_or_terms": str(holidays["license_or_terms"].iloc[0]),
                "note": note,
            }
        ]
    )
    output_paths = {
        "external_status": paths["report_dir"] / "ch15_external_integration_status.csv",
        "external_quality_checks": paths["report_dir"] / "ch15_external_quality_checks.csv",
        "external_daily_amount": paths["report_dir"] / "ch15_holiday_daily_amount.csv",
        "external_comparison": paths["report_dir"] / "ch15_holiday_amount_comparison.csv",
        "external_merge_check": paths["report_dir"] / "ch15_external_merge_check.csv",
        "holiday_template": template_path,
    }
    _atomic_csv(status, output_paths["external_status"])
    _atomic_csv(quality_checks, output_paths["external_quality_checks"])
    _atomic_csv(merged, output_paths["external_daily_amount"])
    _atomic_csv(comparison, output_paths["external_comparison"])
    _atomic_csv(merge_check, output_paths["external_merge_check"])
    return {
        "status": status,
        "comparison": comparison,
        "merge_check": merge_check,
        "quality_checks": quality_checks,
        "output_paths": output_paths,
    }


def build_llm_usage_log_template() -> pd.DataFrame:
    """Create an explicit not-executed LLM usage template."""
    steps = [
        "분석 질문 검토",
        "코드 초안 검토",
        "머신러닝 코드 검토",
        "외부 데이터 연결 검토",
        "오류 해결",
        "결과 해석",
        "보고서 문장 보완",
        "자동화 설계",
    ]
    return pd.DataFrame(
        {
            "execution_status": ["not_executed"] * len(steps),
            "executed_at": [""] * len(steps),
            "provider": [""] * len(steps),
            "model": [""] * len(steps),
            "prompt_version": ["v1"] * len(steps),
            "step": steps,
            "input_summary": [""] * len(steps),
            "response_summary": [""] * len(steps),
            "validation_result": [""] * len(steps),
            "revision_note": [""] * len(steps),
            "final_use": ["not_used"] * len(steps),
        }
    )


def load_or_create_llm_usage_log(report_dir: str | Path) -> tuple[pd.DataFrame, Path]:
    """Preserve an existing human-edited LLM log instead of overwriting it."""
    path = Path(report_dir) / "ch15_llm_usage_log.csv"
    if path.exists() and path.stat().st_size > 0:
        log = pd.read_csv(path, dtype="string").fillna("")
        if "execution_status" not in log.columns:
            executed_at = log.get("executed_at", pd.Series([""] * len(log)))
            used = executed_at.astype(str).str.strip().ne("")
            log.insert(
                0,
                "execution_status",
                used.map({True: "executed", False: "not_executed"}),
            )
        if "final_use" in log.columns:
            log["final_use"] = log["final_use"].replace(
                {"미사용": "not_used", "사용": "used", "부분 사용": "partial"}
            )
        missing = [column for column in LLM_LOG_COLUMNS if column not in log.columns]
        if missing:
            return log, path
        log = log[LLM_LOG_COLUMNS].copy()
        return log, path
    else:
        log = build_llm_usage_log_template()
        _atomic_csv(log, path)
    return log, path


def build_llm_usage_validation(log: pd.DataFrame) -> pd.DataFrame:
    """Validate actual LLM usage Evidence without treating a template as usage."""
    missing = sorted(set(LLM_LOG_COLUMNS) - set(log.columns))
    if missing:
        return pd.DataFrame(
            [{"check": "llm_log_schema", "value": ",".join(missing), "status": "FAIL"}]
        )
    invalid_status = sorted(
        set(log["execution_status"].astype(str)) - {"not_executed", "executed"}
    )
    executed = log.loc[log["execution_status"].eq("executed")].copy()
    required_when_executed = [
        "executed_at",
        "provider",
        "model",
        "prompt_version",
        "validation_result",
        "final_use",
    ]
    incomplete = 0
    if not executed.empty:
        incomplete = int(
            executed[required_when_executed]
            .astype("string")
            .apply(lambda column: column.str.strip().eq(""))
            .any(axis=1)
            .sum()
        )
    secret_like = int(
        log["input_summary"]
        .astype(str)
        .map(lambda value: bool(LLM_SECRET_PATTERN.search(value)))
        .sum()
    )
    return pd.DataFrame(
        [
            {"check": "llm_log_schema", "value": "ok", "status": "PASS"},
            {
                "check": "llm_execution_status_values",
                "value": ",".join(invalid_status) if invalid_status else "valid",
                "status": "FAIL" if invalid_status else "PASS",
            },
            {
                "check": "executed_rows_complete",
                "value": incomplete,
                "status": "FAIL" if incomplete else "PASS",
            },
            {
                "check": "secret_like_input_summary",
                "value": secret_like,
                "status": "FAIL" if secret_like else "PASS",
            },
            {
                "check": "actual_llm_usage",
                "value": len(executed),
                "status": "PASS" if len(executed) else "SKIP",
            },
        ]
    )


def build_automation_plan() -> str:
    """Return a design artifact, not evidence that automation was executed."""
    return """# Chapter 15 자동화 설계서

> 이 문서는 **설계 산출물**이며 자동화가 실제로 구현·실행되었다는 증거가 아닙니다.

## 실행 순서

1. 원본 파일 존재·스키마 확인 — 필수 실패 시 STOP
2. 전처리 및 PK/FK·병합 검증 — 필수 실패 시 STOP
3. 완료 주문 기준 금액 EDA와 시각화 — 총합 불일치 시 STOP
4. 분류 모델 — 데이터 부족으로 미실행 시 SKIP, 계약 제한 시 WARN
5. 외부 데이터 — 파일 없음은 SKIP, provenance·coverage 제한은 WARN
6. LLM 사용 — 미사용 가능, 사용 시 검증 Evidence 필수
7. 프로젝트 Validation — FAIL이면 제출 BLOCKED
8. 보고서·Manifest·Submission Status 저장
9. READY 또는 READY_WITH_WARNINGS일 때만 승인된 전달 단계 진행

## 운영 원칙

- 필수 단계 실패와 선택 단계 미실행을 구분합니다.
- 네트워크 수집과 분석 실행을 분리합니다.
- API Key·토큰·개인정보·사용자 로컬 절대 경로를 공개 Evidence에 넣지 않습니다.
- 재실행은 기존 LLM 사용 로그를 조용히 덮어쓰지 않습니다.
- 실행 성공, 분석 검증, 제출 가능 상태를 서로 다른 상태로 관리합니다.
- Project Run ID, Airflow Dag Run ID, Business Data Interval은 서로 다른 식별 계약입니다.
- Task Green은 Analysis Valid를, Fresh File은 Complete Data를 보장하지 않습니다.
- Retry는 자동 복구가 아니며 멱등성과 제한된 재시도 조건이 필요합니다.
- Atomic File Write는 전체 Project Transaction을 보장하지 않습니다.
- 외부 전달은 안정적인 delivery idempotency key와 수신 측 dedupe 정책을 포함해야 합니다.
"""


def build_project_validation(
    core: dict[str, Any],
    classification_result: dict[str, Any],
    external_result: dict[str, Any],
    llm_validation: pd.DataFrame,
    figure_paths: dict[str, Path],
    automation_path: Path,
) -> pd.DataFrame:
    """Build PASS/WARN/FAIL Evidence for required and optional stages."""
    scope = core["public_tables"]["amount_scope_summary"].set_index("scope")
    completed_amount = float(scope.loc["completed_order_items", "amount"])
    totals = {
        "category": float(core["public_tables"]["category_sales"]["total_sales"].sum()),
        "monthly": float(core["public_tables"]["monthly_sales"]["total_sales"].sum()),
        "customer": float(core["public_tables"]["customer_sales"]["total_sales"].sum()),
        "product": float(core["public_tables"]["product_sales"]["total_sales"].sum()),
    }
    totals_match = all(
        abs(value - completed_amount) <= TOTAL_TOLERANCE for value in totals.values()
    )
    merge_checks = core["public_tables"]["merge_checks"]
    relationship_checks = core["relationship_checks"]
    key_checks = core["key_duplicate_checks"]
    core_validation = core["public_tables"]["core_validation"]
    customer_columns = set(core["public_tables"]["customer_sales"].columns)
    private_columns = {"customer_id", "name", "email", "phone", "address"}
    classification_status = str(classification_result["status"].iloc[0]["status"])
    external_status = str(external_result["status"].iloc[0]["status"])
    llm_fail = bool(llm_validation["status"].eq("FAIL").any())
    llm_warn = bool(llm_validation["status"].eq("WARN").any())
    classification_gate = (
        "PASS" if classification_status == "completed"
        else "SKIP" if classification_status == "skipped" else "WARN"
    )
    external_gate = (
        "PASS" if external_status == "completed"
        else "SKIP" if external_status == "skipped" else "WARN"
    )
    llm_usage_rows = llm_validation.loc[llm_validation["check"].eq("actual_llm_usage")]
    llm_executed = bool(not llm_usage_rows.empty and int(llm_usage_rows.iloc[0]["value"]) > 0)
    llm_gate = "FAIL" if llm_fail else (
        "WARN" if llm_warn else ("PASS" if llm_executed else "SKIP")
    )

    return pd.DataFrame(
        [
            {
                "check": "required_primary_keys",
                "status": "PASS" if key_checks["status"].eq("PASS").all() else "FAIL",
                "detail": f"PK checks={len(key_checks)}",
            },
            {
                "check": "required_foreign_keys",
                "status": (
                    "PASS"
                    if relationship_checks["invalid_count"].fillna(0).eq(0).all()
                    else "FAIL"
                ),
                "detail": f"invalid={int(relationship_checks['invalid_count'].fillna(0).sum())}",
            },
            {
                "check": "safe_merge_contract",
                "status": (
                    "PASS"
                    if merge_checks["status"].eq("PASS").all()
                    and merge_checks["row_count_preserved"].fillna(False).all()
                    and merge_checks["unmatched_count"].fillna(0).eq(0).all()
                    else "FAIL"
                ),
                "detail": f"merge checks={len(merge_checks)}",
            },
            {
                "check": "core_validation_gate",
                "status": "PASS" if core_validation["status"].eq("PASS").all() else "FAIL",
                "detail": "; ".join(core_validation["check"].astype(str)),
            },
            {
                "check": "completed_amount_consistency",
                "status": "PASS" if totals_match else "FAIL",
                "detail": f"completed={completed_amount}; {totals}",
            },
            {
                "check": "customer_public_privacy",
                "status": "PASS" if not private_columns.intersection(customer_columns) else "FAIL",
                "detail": ", ".join(sorted(customer_columns)),
            },
            {
                "check": "classification_optional_stage",
                "status": classification_gate,
                "detail": str(classification_result["status"].iloc[0]["note"]),
            },
            {
                "check": "external_optional_stage",
                "status": external_gate,
                "detail": str(external_result["status"].iloc[0]["note"]),
            },
            {
                "check": "llm_usage_evidence",
                "status": llm_gate,
                "detail": "미사용은 SKIP; 실제 사용 시 provider/model/prompt/review Evidence 필수",
            },
            {
                "check": "required_figures",
                "status": (
                    "PASS"
                    if figure_paths
                    and all(path.is_file() and path.stat().st_size > 0 for path in figure_paths.values())
                    else "FAIL"
                ),
                "detail": f"figures={len(figure_paths)}",
            },
            {
                "check": "automation_plan_design_artifact",
                "status": (
                    "PASS"
                    if automation_path.is_file() and automation_path.stat().st_size > 0
                    else "FAIL"
                ),
                "detail": "설계 파일 존재 여부만 확인; 실제 자동화 실행 증거는 아님",
            },
        ]
    )


def _validation_summary(validation: pd.DataFrame) -> str:
    if validation["status"].eq("FAIL").any():
        return "BLOCKED"
    if validation["status"].eq("WARN").any():
        return "READY_WITH_WARNINGS"
    return "READY"


def build_final_report(
    core: dict[str, Any],
    classification_result: dict[str, Any],
    external_result: dict[str, Any],
    llm_usage_log: pd.DataFrame,
    validation: pd.DataFrame,
    submission_status: pd.DataFrame | None = None,
    project_run_id: str = "NOT_ASSIGNED",
) -> str:
    """Build the public-safe final Markdown report."""
    public = core["public_tables"]
    classification_text = (
        classification_result["test_metrics"].to_string(index=False)
        if not classification_result["test_metrics"].empty
        else classification_result["status"].to_string(index=False)
    )
    external_text = (
        external_result["comparison"].to_string(index=False)
        if not external_result["comparison"].empty
        else external_result["status"].to_string(index=False)
    )
    executed_llm = int(llm_usage_log["execution_status"].eq("executed").sum())
    gate = (
        str(submission_status.iloc[0]["status"])
        if submission_status is not None and not submission_status.empty
        else _validation_summary(validation)
    )
    return f"""# 온라인 쇼핑몰 데이터 분석 최종 보고서

- Project Run ID: `{project_run_id}`
- 분석 질문: 완료 주문 기준 금액은 카테고리·월·고객·상품에 따라 어떤 패턴을 보이는가?
- 의사결정/다음 조사: 우선 검토할 범위를 정하되, 금액이 높다는 사실을 수익성이나 원인으로 해석하지 않습니다.

## 0. 제출 Gate

- 현재 상태: **{gate}**
- `FAIL`이 하나라도 남으면 제출 완료 상태가 아닙니다.
- `SKIP`은 선택 단계 미사용, `WARN`은 실행·해석 제한이며 서로 다른 상태입니다.

## 1. 프로젝트 목적

완료 주문 기준 금액과 고객·상품·월별 패턴을 분석하고, 선택 단계인 주문 취소 분류와 외부 데이터 통합 가능성을 검토했습니다.

## 2. 데이터 개요

```text
{core['dataset_summary'].to_string(index=False)}
```

## 3. 데이터 품질과 분석 범위

```text
{public['amount_scope_summary'].to_string(index=False)}
```

금액성 EDA는 `order_status == "completed"`인 주문 상세의 `quantity × unit_price` 합계만 사용합니다. 기존 결과 컬럼의 `total_sales`는 이 프로젝트에서 **완료 주문 기준 금액**을 뜻하며 할인·배송비·세금·부분 환불·정산 기준을 반영한 회계상 순매출이 아닙니다.

## 4. 핵심 EDA

### 카테고리별 완료 주문 기준 금액

```text
{public['category_sales'].head(10).to_string(index=False)}
```

### 월별 완료 주문 기준 금액

```text
{public['monthly_sales'].head(12).to_string(index=False)}
```

### 비식별 고객 라벨별 완료 주문 구매 금액

```text
{public['customer_sales'].head(10).to_string(index=False)}
```

## 5. 주문 취소 분류 — 선택 단계

```text
{classification_text}
```

모델과 임계값은 validation에서 고정하고 test는 최종 평가에만 사용합니다. `completed=0`, `cancelled=1`로 귀결된 주문만 사용하고 `refunded` 등은 제외하므로 모든 신규 주문의 취소 위험을 뜻하지 않습니다. 클래스별 예측 점수는 실제 발생 확률이 아니며 확률 해석에는 calibration 검증이 필요합니다. F1 중심 임계값은 교육용 선택 규칙이고 실제 업무에서는 FP/FN 비용과 최소 precision/recall 정책을 함께 적용해야 합니다. 같은 validation으로 모델과 임계값을 모두 선택했으므로 test만 최종 일반화 평가로 해석합니다.

## 6. 외부 데이터 — 선택 단계

```text
{external_text}
```

외부 파일이 없거나 provenance·날짜·키·coverage 검증을 통과하지 못하면 `skipped` 또는 `warning`으로 기록합니다. processed 데이터와 metadata provenance는 분리하며 미매칭 날짜를 자동으로 일반일이라고 가정하지 않습니다. 원본 보존과 배포 가능 여부는 license/terms, distribution_allowed, retention_note 계약을 별도로 확인해야 합니다. 외부 변수와 완료 주문 기준 금액의 동시 변화는 인과관계를 의미하지 않습니다.

## 7. LLM 사용 기록 — 선택 단계

- 실제 실행으로 기록된 행: {executed_llm}건
- 빈 템플릿은 LLM 사용 증거가 아닙니다.
- 실제 사용 시 제공자·모델·실행 시각·프롬프트 버전·검증 결과·사람 수정·최종 사용 여부를 기록합니다.

## 8. 프로젝트 검증

```text
{validation.to_string(index=False)}
```

## 9. 자동화 설계

`ch15_automation_plan.md`는 실패·경고·재실행·알림 기준을 설명하는 **설계 산출물**이며 자동화가 실제 실행되었다는 증거는 아닙니다.

## 10. 한계와 다음 단계

- 샘플 데이터의 기간과 크기에 결과가 제한됩니다.
- 완료 주문 기준 금액은 현재 주문 상태와 제공 필드 정의에 의존합니다.
- 익명 고객 결과도 소규모 집단에서는 재식별 위험을 추가 검토해야 합니다.
- 분류 운영 적용 전 시간 순서 평가, 비용 기준, 공정성 검토가 필요합니다.
- 외부 데이터의 출처 범위와 갱신 주기를 관리해야 합니다.
- LLM 제안은 실행·수치·논리 검증 후에만 반영합니다.
"""


def build_deliverable_manifest(
    files: dict[str, Path],
    *,
    required_names: set[str],
    base_dir: str | Path,
    project_run_id: str,
) -> pd.DataFrame:
    """Record public-safe relative paths, size and SHA-256 change Evidence."""
    rows = []
    for name, path in sorted(files.items()):
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        rows.append(
            {
                "deliverable": name,
                "project_run_id": project_run_id,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "required": name in required_names,
                "path": _relative_project_path(path, base_dir),
                "exists": exists,
                "size_bytes": size,
                "nonempty": bool(exists and size > 0),
                "sha256": sha256_file(path) if exists and size > 0 else "",
            }
        )
    return pd.DataFrame(rows)


def build_submission_status(
    validation: pd.DataFrame,
    manifest: pd.DataFrame,
    *,
    project_run_id: str,
    manifest_path: Path,
    base_dir: Path,
) -> pd.DataFrame:
    """Decide submission readiness from validation and required artifacts."""
    fail_count = int(validation["status"].eq("FAIL").sum())
    warn_count = int(validation["status"].eq("WARN").sum())
    skip_count = int(validation["status"].eq("SKIP").sum())
    pass_count = int(validation["status"].eq("PASS").sum())
    required_missing = manifest.loc[
        manifest["required"] & (~manifest["exists"] | ~manifest["nonempty"])
    ]
    blocked = fail_count > 0 or not required_missing.empty
    status = "BLOCKED" if blocked else ("READY_WITH_WARNINGS" if warn_count else "READY")
    return pd.DataFrame(
        [
            {
                "status": status,
                "project_run_id": project_run_id,
                "can_submit": not blocked,
                "pass_count": pass_count,
                "skip_count": skip_count,
                "warn_count": warn_count,
                "fail_count": fail_count,
                "validation_fail_count": fail_count,
                "validation_warn_count": warn_count,
                "required_missing_count": len(required_missing),
                "required_missing": ",".join(required_missing["deliverable"].astype(str)),
                "manifest_path": _relative_project_path(manifest_path, base_dir),
                "manifest_sha256": sha256_file(manifest_path),
                "note": (
                    "FAIL 또는 필수 산출물 누락을 수정한 뒤 다시 실행"
                    if blocked
                    else "WARN 사유를 보고서에 포함하고 제출 가능"
                    if warn_count
                    else "필수 검증과 산출물 기준 충족"
                ),
            }
        ]
    )


def run_final_project(
    base_dir: str | Path = ".",
    *,
    random_state: int = 42,
) -> dict[str, Any]:
    """Run the complete Chapter 15 project without network collection."""
    project_run_id = _new_project_run_id()
    generated_at_utc = datetime.now(timezone.utc).isoformat()
    core = prepare_core_analysis(base_dir)
    paths = core["paths"]
    core_outputs = save_core_outputs(core)
    figure_outputs = generate_project_figures(core["public_tables"], paths["figure_dir"])
    classification = run_classification_stage(
        core["processed"], paths["report_dir"], random_state=random_state
    )
    external = run_external_integration_stage(core["analysis_tables"], paths)

    llm_log, llm_log_path = load_or_create_llm_usage_log(paths["report_dir"])
    llm_validation = build_llm_usage_validation(llm_log)
    llm_validation_path = paths["report_dir"] / "ch15_llm_usage_validation.csv"
    _atomic_csv(llm_validation, llm_validation_path)

    automation_path = paths["report_dir"] / "ch15_automation_plan.md"
    _atomic_text(build_automation_plan(), automation_path)

    validation = build_project_validation(
        core,
        classification,
        external,
        llm_validation,
        figure_outputs,
        automation_path,
    )
    validation.insert(0, "project_run_id", project_run_id)
    validation_path = paths["report_dir"] / "ch15_project_validation.csv"
    _atomic_csv(validation, validation_path)

    reproducibility = build_reproducibility_manifest(paths)
    reproducibility.insert(0, "project_run_id", project_run_id)
    reproducibility["random_state"] = random_state
    reproducibility_path = paths["report_dir"] / "ch15_reproducibility_manifest.csv"
    _atomic_csv(reproducibility, reproducibility_path)

    project_metadata = pd.DataFrame([{
        "project_run_id": project_run_id,
        "generated_at_utc": generated_at_utc,
        "random_state": random_state,
        "core_scope": "order_status == completed; sum(quantity * unit_price)",
        "classification_status": str(classification["status"].iloc[0]["status"]),
        "external_status": str(external["status"].iloc[0]["status"]),
        "llm_status": "executed" if llm_log.get("execution_status", pd.Series(dtype=str)).eq("executed").any() else "not_executed",
    }])
    metadata_path = paths["report_dir"] / "ch15_project_run_metadata.csv"
    _atomic_csv(project_metadata, metadata_path)

    report_path = paths["report_dir"] / "ch15_final_report.md"
    _atomic_text(
        build_final_report(
            core, classification, external, llm_log, validation,
            project_run_id=project_run_id,
        ),
        report_path,
    )

    files: dict[str, Path] = {
        **core_outputs,
        **{f"figure_{name}": path for name, path in figure_outputs.items()},
        **classification["output_paths"],
        **external["output_paths"],
        "llm_usage_log": llm_log_path,
        "llm_usage_validation": llm_validation_path,
        "automation_plan": automation_path,
        "project_validation": validation_path,
        "reproducibility_manifest": reproducibility_path,
        "project_run_metadata": metadata_path,
        "final_report": report_path,
    }
    required_names = {
        "dataset_summary",
        "preprocessing_comparison",
        "key_duplicate_checks",
        "relationship_checks",
        "merge_checks",
        "amount_scope_summary",
        "total_consistency_check",
        "core_validation",
        "category_sales",
        "monthly_sales",
        "customer_sales",
        "product_sales",
        "order_status_summary",
        "figure_category_sales",
        "figure_monthly_sales",
        "figure_top_customers",
        "figure_order_status",
        "classification_status",
        "external_status",
        "external_quality_checks",
        "llm_usage_log",
        "llm_usage_validation",
        "automation_plan",
        "project_validation",
        "reproducibility_manifest",
        "project_run_metadata",
        "final_report",
    }
    manifest = build_deliverable_manifest(
        files,
        required_names=required_names,
        base_dir=paths["base_dir"],
        project_run_id=project_run_id,
    )
    manifest_path = paths["report_dir"] / "ch15_project_deliverables.csv"
    _atomic_csv(manifest, manifest_path)
    files["deliverable_manifest"] = manifest_path

    # Authoritative status is deliberately the last write. The manifest does
    # not contain itself or this status file, avoiding a circular hash contract.
    submission_status = build_submission_status(
        validation,
        manifest,
        project_run_id=project_run_id,
        manifest_path=manifest_path,
        base_dir=paths["base_dir"],
    )
    submission_path = paths["report_dir"] / "ch15_submission_status.csv"
    _atomic_csv(submission_status, submission_path)
    files["submission_status"] = submission_path

    return {
        "project_run_id": project_run_id,
        "paths": paths,
        "core": core,
        "classification": classification,
        "external": external,
        "llm_usage_log": llm_log,
        "llm_usage_validation": llm_validation,
        "validation": validation,
        "submission_status": submission_status,
        "manifest": manifest,
        "reproducibility": reproducibility,
        "output_paths": files,
        "final_report_path": report_path,
        "deliverables_path": manifest_path,
        "submission_status_path": submission_path,
    }
