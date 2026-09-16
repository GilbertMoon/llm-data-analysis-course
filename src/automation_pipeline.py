"""Chapter 14 validated analysis-automation utilities.

The local runner and the canonical Airflow DAG call the same deterministic
functions.  The pipeline validates schema/key relationships, aggregates
completed orders only, writes each artifact atomically, tags related analysis
artifacts with one run id, and validates freshness/cross-file consistency.

Important limits:
- Atomic replacement is per file, not a transaction across the whole pipeline.
- Airflow task success is not proof that the analysis output is valid.
- External delivery must wait until ``validate_outputs`` succeeds.
"""
from __future__ import annotations

import csv
import hashlib
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

RAW_FILENAMES = ["customers.csv", "products.csv", "orders.csv", "order_items.csv"]
PROCESSED_FILENAMES = [
    "customers_clean.csv",
    "products_clean.csv",
    "orders_clean.csv",
    "order_items_clean.csv",
]
REPORT_FILENAMES = [
    "ch14_daily_sales.csv",
    "ch14_category_sales.csv",
    "ch14_pipeline_task_summary.csv",
    "ch14_airflow_setup_guide.csv",
    "ch14_pipeline_run_metadata.csv",
    "ch14_airflow_report.md",
]
VALIDATION_LOG = "ch14_airflow_validation_log.csv"
ARTIFACT_MANIFEST = "ch14_artifact_manifest.csv"
TOTAL_TOLERANCE = 0.01
RATIO_TOLERANCE = 0.1

REQUIRED = {
    "customers": {"customer_id", "gender", "age", "city", "signup_date"},
    "products": {"product_id", "product_name", "category", "price"},
    "orders": {
        "order_id",
        "customer_id",
        "order_date",
        "payment_method",
        "order_status",
    },
    "order_items": {
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    },
}

PRIMARY_KEYS = {
    "customers": "customer_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "order_item_id",
}

STATUS_MAP = {
    "complete": "completed",
    "completed": "completed",
    "완료": "completed",
    "cancel": "cancelled",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "취소": "cancelled",
    "refund": "refunded",
    "refunded": "refunded",
    "환불": "refunded",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(
        microsecond=0
    ).isoformat()


def new_pipeline_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"ch14-{stamp}-{uuid.uuid4().hex[:8]}"


def project_root_from_file(file_path: str | Path) -> Path:
    return Path(file_path).resolve().parents[1]


def get_project_paths(base_dir: str | Path = ".") -> dict[str, Path]:
    if str(base_dir) == "." and os.getenv("PROJECT_ROOT"):
        base = Path(os.environ["PROJECT_ROOT"]).resolve()
    else:
        base = Path(base_dir).resolve()

    paths = {
        "base_dir": base,
        "raw_dir": base / "data" / "raw",
        "processed_dir": base / "data" / "processed",
        "report_dir": base / "reports",
        "figure_dir": base / "reports" / "figures",
    }
    for key in ("processed_dir", "report_dir", "figure_dir"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def expected_input_files(base_dir: str | Path = ".") -> list[Path]:
    raw = get_project_paths(base_dir)["raw_dir"]
    return [raw / name for name in RAW_FILENAMES]


def expected_output_files(base_dir: str | Path = ".") -> list[Path]:
    """Return artifacts that must exist before the validation log itself is written."""
    paths = get_project_paths(base_dir)
    return (
        [paths["processed_dir"] / name for name in PROCESSED_FILENAMES]
        + [paths["report_dir"] / name for name in REPORT_FILENAMES]
        + [paths["figure_dir"] / "ch14_daily_sales.png"]
    )


def _atomic_csv(frame: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, suffix=".tmp", delete=False
    ) as file:
        temporary = Path(file.name)
    try:
        frame.to_csv(temporary, index=False, encoding="utf-8-sig")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _atomic_text(text: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        suffix=".tmp",
        delete=False,
    ) as file:
        file.write(text)
        temporary = Path(file.name)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _require_columns(name: str, frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise KeyError(f"{name}에 필요한 컬럼이 없습니다: {missing}")


def _require_unique(name: str, frame: pd.DataFrame, key: str) -> None:
    if key not in frame.columns:
        raise KeyError(f"{name}.{key} 키 컬럼이 없습니다.")
    missing = int(frame[key].isna().sum())
    duplicated = int(frame.loc[frame[key].notna(), key].duplicated(keep=False).sum())
    if missing or duplicated:
        raise ValueError(
            f"{name}.{key} 무결성 오류: 결측 {missing}건, 중복 행 {duplicated}건"
        )


def _convert_numeric(name: str, frame: pd.DataFrame, column: str) -> None:
    before_missing = frame[column].isna()
    converted = pd.to_numeric(frame[column], errors="coerce")
    failed = int((~before_missing & converted.isna()).sum())
    if failed:
        raise ValueError(f"{name}.{column} 숫자 변환 실패: {failed}건")
    frame[column] = converted


def _convert_date(name: str, frame: pd.DataFrame, column: str) -> None:
    before_missing = frame[column].isna()
    converted = pd.to_datetime(frame[column], errors="coerce")
    failed = int((~before_missing & converted.isna()).sum())
    if failed:
        raise ValueError(f"{name}.{column} 날짜 변환 실패: {failed}건")
    frame[column] = converted


def _require_reference(
    child_name: str,
    child: pd.DataFrame,
    child_key: str,
    parent_name: str,
    parent: pd.DataFrame,
    parent_key: str,
) -> None:
    _require_columns(child_name, child, [child_key])
    _require_columns(parent_name, parent, [parent_key])
    invalid = child[child_key].isna() | ~child[child_key].isin(parent[parent_key])
    if invalid.any():
        examples = (
            child.loc[invalid, child_key]
            .dropna()
            .astype(str)
            .head(5)
            .tolist()
        )
        raise ValueError(
            f"{child_name}.{child_key} 중 {int(invalid.sum())}건이 "
            f"{parent_name}.{parent_key}에 없습니다. 예: {examples}"
        )


def check_input_files(base_dir: str | Path = ".") -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in expected_input_files(base_dir):
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        rows.append(
            {
                "file": str(path),
                "exists": exists,
                "size_bytes": size,
                "modified_at_utc": _mtime_utc(path) if exists else "",
                "status": "ok" if exists and size > 0 else "error",
            }
        )
    result = pd.DataFrame(rows)
    failed = result[result["status"].ne("ok")]
    if not failed.empty:
        raise FileNotFoundError(
            "필수 원본 CSV가 없거나 비어 있습니다: "
            + ", ".join(failed["file"].astype(str))
        )
    return result


def run_preprocessing(base_dir: str | Path = ".") -> dict[str, Path]:
    paths = get_project_paths(base_dir)
    check_input_files(base_dir)
    data = {
        "customers": pd.read_csv(paths["raw_dir"] / "customers.csv"),
        "products": pd.read_csv(paths["raw_dir"] / "products.csv"),
        "orders": pd.read_csv(paths["raw_dir"] / "orders.csv"),
        "order_items": pd.read_csv(paths["raw_dir"] / "order_items.csv"),
    }

    for name, frame in data.items():
        for column in frame.select_dtypes(include="object").columns:
            frame[column] = (
                frame[column].astype("string").str.strip().replace("", pd.NA)
            )
        _require_columns(name, frame, REQUIRED[name])

    customers = data["customers"]
    products = data["products"]
    orders = data["orders"]
    items = data["order_items"]

    for name, key in PRIMARY_KEYS.items():
        _require_unique(name, data[name], key)

    _convert_numeric("customers", customers, "age")
    _convert_date("customers", customers, "signup_date")
    _convert_numeric("products", products, "price")
    _convert_date("orders", orders, "order_date")
    _convert_numeric("order_items", items, "quantity")
    _convert_numeric("order_items", items, "unit_price")

    required_values = [
        ("customers", customers, ["customer_id", "age", "city", "signup_date"]),
        ("products", products, ["product_id", "product_name", "category", "price"]),
        (
            "orders",
            orders,
            ["order_id", "customer_id", "order_date", "payment_method", "order_status"],
        ),
        (
            "order_items",
            items,
            ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
        ),
    ]
    for name, frame, columns in required_values:
        missing = frame[columns].isna().sum()
        if missing.gt(0).any():
            raise ValueError(
                f"{name} 필수값 결측: {missing[missing.gt(0)].to_dict()}"
            )

    if (
        products["price"].le(0).any()
        or items["quantity"].le(0).any()
        or items["unit_price"].le(0).any()
    ):
        raise ValueError("price, quantity, unit_price에는 0보다 큰 값만 허용됩니다.")

    orders["order_status"] = (
        orders["order_status"].astype("string").str.lower().replace(STATUS_MAP)
    )
    unknown = sorted(
        set(orders["order_status"].dropna())
        - {"completed", "cancelled", "refunded"}
    )
    if unknown:
        raise ValueError(f"알 수 없는 order_status가 있습니다: {unknown}")

    _require_reference(
        "orders", orders, "customer_id", "customers", customers, "customer_id"
    )
    _require_reference(
        "order_items", items, "order_id", "orders", orders, "order_id"
    )
    _require_reference(
        "order_items", items, "product_id", "products", products, "product_id"
    )

    calculated = items["quantity"] * items["unit_price"]
    if "line_total" in items.columns:
        current = pd.to_numeric(items["line_total"], errors="coerce")
        mismatch = current.isna() | current.sub(calculated).abs().gt(TOTAL_TOLERANCE)
        if mismatch.any():
            raise ValueError(
                "line_total이 quantity × unit_price와 다른 행이 "
                f"{int(mismatch.sum())}건 있습니다."
            )
    items["line_total"] = calculated

    frames = {
        "customers": customers.sort_values("customer_id"),
        "products": products.sort_values("product_id"),
        "orders": orders.sort_values(["order_date", "order_id"]),
        "order_items": items.sort_values(["order_id", "order_item_id"]),
    }
    outputs = {
        name: paths["processed_dir"] / f"{name}_clean.csv" for name in frames
    }
    for name, frame in frames.items():
        _atomic_csv(frame.reset_index(drop=True), outputs[name])
    return outputs


def create_pipeline_task_summary() -> pd.DataFrame:
    """Document task contracts; this table is evidence, not an execution log."""
    return pd.DataFrame(
        [
            {
                "task_id": "check_input_files",
                "input": "data/raw CSV 4개",
                "output": "입력 상태",
                "failure_condition": "누락 또는 0 byte",
                "retry_policy": "0회: 입력 수정 전 재시도 의미 없음",
                "idempotency": "읽기 전용",
            },
            {
                "task_id": "run_preprocessing",
                "input": "raw CSV 4개",
                "output": "processed/*_clean.csv",
                "failure_condition": "schema/type/PK/FK/line_total 오류",
                "retry_policy": "0회: 데이터/코드 원인 먼저 수정",
                "idempotency": "전체 파일을 임시 파일 후 원자적 교체",
            },
            {
                "task_id": "run_analysis",
                "input": "processed CSV",
                "output": "daily/category/run metadata",
                "failure_condition": "completed 0행, 관계/집계 오류",
                "retry_policy": "0회: 분석 규칙 원인 먼저 확인",
                "idempotency": "동일 범위 전체 재생성 + run id",
            },
            {
                "task_id": "generate_visualizations",
                "input": "daily CSV",
                "output": "PNG",
                "failure_condition": "빈 집계 또는 저장 오류",
                "retry_policy": "최대 1회 예시; 반복 실패 시 로그 확인",
                "idempotency": "PNG 임시 파일 후 원자적 교체",
            },
            {
                "task_id": "generate_report",
                "input": "daily/category CSV",
                "output": "Markdown",
                "failure_condition": "집계/run id 불일치",
                "retry_policy": "0회: 입력 산출물 일관성 확인",
                "idempotency": "Markdown 임시 파일 후 원자적 교체",
            },
            {
                "task_id": "validate_outputs",
                "input": "전체 산출물",
                "output": VALIDATION_LOG,
                "failure_condition": "freshness/rows/run id/total/scope 오류",
                "retry_policy": "0회: 실패 Evidence를 읽고 원인 수정",
                "idempotency": "검증 로그 전체 교체",
            },
        ]
    )


def create_airflow_setup_guide() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "step": "Docker 확인",
                "command": "docker --version && docker compose version",
                "success": "Docker/Compose 버전 확인",
                "failure_check": "Docker Desktop/Engine 상태",
                "destructive": False,
            },
            {
                "step": "Python 사전 검증",
                "command": "python scripts/run_ch14_pipeline.py",
                "success": "validation log 모두 ok",
                "failure_check": "Python 예외와 validation log",
                "destructive": False,
            },
            {
                "step": ".env 준비",
                "command": "cp .env.example .env 또는 Copy-Item",
                "success": "필수 Secret 3개를 서로 다른 값으로 설정",
                "failure_check": "빈 Secret/커밋 여부 확인",
                "destructive": False,
            },
            {
                "step": "이미지 빌드",
                "command": "docker compose build",
                "success": "custom image build 성공",
                "failure_check": "dependency/build log",
                "destructive": False,
            },
            {
                "step": "초기화",
                "command": "docker compose up airflow-init",
                "success": "airflow-init exit code 0",
                "failure_check": "init/postgres log",
                "destructive": False,
            },
            {
                "step": "서비스 시작",
                "command": "docker compose up -d && docker compose ps",
                "success": "필수 서비스 running/healthy",
                "failure_check": "service별 logs",
                "destructive": False,
            },
            {
                "step": "DAG 수동 실행",
                "command": "UI에서 ch14_local_analysis_pipeline 실행",
                "success": "validate_outputs까지 성공",
                "failure_check": "첫 실패 Task log",
                "destructive": False,
            },
            {
                "step": "일반 종료",
                "command": "docker compose down",
                "success": "컨테이너 종료, DB volume 유지",
                "failure_check": "docker compose ps",
                "destructive": False,
            },
            {
                "step": "완전 초기화",
                "command": "docker compose down --volumes --remove-orphans",
                "success": "학습 환경 metadata를 의도적으로 삭제",
                "failure_check": "실행 기록/계정 삭제 영향 재확인",
                "destructive": True,
            },
        ]
    )


def _load_processed_tables(base_dir: str | Path) -> dict[str, pd.DataFrame]:
    paths = get_project_paths(base_dir)
    file_map = {
        "customers": paths["processed_dir"] / "customers_clean.csv",
        "products": paths["processed_dir"] / "products_clean.csv",
        "orders": paths["processed_dir"] / "orders_clean.csv",
        "order_items": paths["processed_dir"] / "order_items_clean.csv",
    }
    missing = [path for path in file_map.values() if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError(
            "processed 파일이 없거나 비어 있습니다: "
            + ", ".join(map(str, missing))
        )
    return {
        "customers": pd.read_csv(file_map["customers"]),
        "products": pd.read_csv(file_map["products"]),
        "orders": pd.read_csv(file_map["orders"]),
        "order_items": pd.read_csv(file_map["order_items"]),
    }


def run_analysis(
    base_dir: str | Path = ".", *, run_id: str | None = None,
    orchestration_context: dict[str, object] | None = None,
) -> dict[str, Path]:
    paths = get_project_paths(base_dir)
    data = _load_processed_tables(base_dir)
    customers = data["customers"]
    products = data["products"]
    orders = data["orders"]
    items = data["order_items"]

    for name, frame in data.items():
        _require_columns(name, frame, REQUIRED[name])
    _require_columns("order_items", items, ["line_total"])
    for name, key in PRIMARY_KEYS.items():
        _require_unique(name, data[name], key)

    _convert_date("orders", orders, "order_date")
    for column in ["quantity", "unit_price", "line_total"]:
        _convert_numeric("order_items", items, column)
    expected_total = items["quantity"] * items["unit_price"]
    mismatch = items["line_total"].sub(expected_total).abs().gt(TOTAL_TOLERANCE)
    if mismatch.any():
        raise ValueError(
            f"processed line_total 불일치가 {int(mismatch.sum())}건 있습니다."
        )

    _require_reference(
        "orders", orders, "customer_id", "customers", customers, "customer_id"
    )
    _require_reference(
        "order_items", items, "order_id", "orders", orders, "order_id"
    )
    _require_reference(
        "order_items", items, "product_id", "products", products, "product_id"
    )

    completed_orders = orders.loc[
        orders["order_status"].astype("string").eq("completed"),
        ["order_id", "order_date"],
    ]
    if completed_orders.empty:
        raise ValueError("completed 주문이 0건입니다.")

    completed = items.merge(
        completed_orders,
        on="order_id",
        how="inner",
        validate="many_to_one",
    )
    completed = completed.merge(
        products[["product_id", "category"]],
        on="product_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    unmatched_products = int(completed["_merge"].ne("both").sum())
    category_missing = int(completed["category"].isna().sum())
    if completed.empty or unmatched_products or category_missing:
        raise ValueError(
            "완료 주문 상품 병합 오류: "
            f"rows={len(completed)}, unmatched={unmatched_products}, "
            f"category_missing={category_missing}"
        )
    completed = completed.drop(columns="_merge")

    completed["order_day"] = completed["order_date"].dt.normalize()
    daily = (
        completed.groupby("order_day", as_index=False)
        .agg(
            completed_order_amount=("line_total", "sum"),
            completed_order_count=("order_id", "nunique"),
        )
        .sort_values("order_day")
        .reset_index(drop=True)
    )
    daily["avg_completed_order_amount"] = (
        daily["completed_order_amount"] / daily["completed_order_count"]
    ).round(2)

    category = (
        completed.groupby("category", as_index=False)
        .agg(
            completed_quantity=("quantity", "sum"),
            completed_order_amount=("line_total", "sum"),
        )
        .sort_values("completed_order_amount", ascending=False)
        .reset_index(drop=True)
    )
    total = float(category["completed_order_amount"].sum())
    if total <= 0:
        raise ValueError("completed 주문 기준 금액 합계가 0 이하입니다.")
    category["amount_ratio_pct"] = (
        category["completed_order_amount"] / total * 100
    ).round(2)

    daily_total = float(daily["completed_order_amount"].sum())
    if abs(daily_total - total) > TOTAL_TOLERANCE:
        raise ValueError(
            "분석 단계 총합 불일치: "
            f"daily={daily_total}, category={total}"
        )

    pipeline_run_id = run_id or new_pipeline_run_id()
    generated_at_utc = utc_now_iso()
    input_files = expected_input_files(base_dir)
    input_latest_mtime = max(path.stat().st_mtime for path in input_files)
    input_latest_mtime_utc = datetime.fromtimestamp(
        input_latest_mtime, tz=timezone.utc
    ).replace(microsecond=0).isoformat()

    for frame in (daily, category):
        frame.insert(0, "pipeline_run_id", pipeline_run_id)
        frame.insert(1, "generated_at_utc", generated_at_utc)

    context = orchestration_context or {}
    metadata = pd.DataFrame(
        [
            {
                "pipeline_run_id": pipeline_run_id,
                "generated_at_utc": generated_at_utc,
                "input_latest_mtime_utc": input_latest_mtime_utc,
                "file_freshness_check": "output mtime >= latest raw mtime",
                "expected_data_start": context.get("data_interval_start", "NOT_CONFIGURED"),
                "expected_data_end": context.get("data_interval_end", "NOT_CONFIGURED"),
                "source_max_event_time": "NOT_CONFIGURED",
                "source_complete": "REVIEW_REQUIRED",
                "airflow_dag_id": context.get("airflow_dag_id", "LOCAL_RUN"),
                "airflow_dag_run_id": context.get("airflow_dag_run_id", "LOCAL_RUN"),
                "airflow_logical_date": context.get("airflow_logical_date", "NOT_CONFIGURED"),
                "aggregation_scope": "order_status == completed",
                "amount_definition": "sum(quantity * unit_price)",
                "is_accounting_net_revenue": False,
                "completed_order_count": int(completed_orders["order_id"].nunique()),
                "completed_detail_rows": int(len(completed)),
                "completed_order_amount": total,
            }
        ]
    )

    outputs = {
        "daily_sales": paths["report_dir"] / "ch14_daily_sales.csv",
        "category_sales": paths["report_dir"] / "ch14_category_sales.csv",
        "task_summary": paths["report_dir"] / "ch14_pipeline_task_summary.csv",
        "setup_guide": paths["report_dir"] / "ch14_airflow_setup_guide.csv",
        "run_metadata": paths["report_dir"] / "ch14_pipeline_run_metadata.csv",
    }
    frames_and_keys = [
        (daily, "daily_sales"),
        (category, "category_sales"),
        (create_pipeline_task_summary(), "task_summary"),
        (create_airflow_setup_guide(), "setup_guide"),
        (metadata, "run_metadata"),
    ]
    for frame, key in frames_and_keys:
        _atomic_csv(frame, outputs[key])
    return outputs


def generate_visualizations(base_dir: str | Path = ".") -> dict[str, Path]:
    paths = get_project_paths(base_dir)
    daily = pd.read_csv(
        paths["report_dir"] / "ch14_daily_sales.csv", parse_dates=["order_day"]
    )
    _require_columns(
        "ch14_daily_sales",
        daily,
        ["pipeline_run_id", "order_day", "completed_order_amount"],
    )
    if daily.empty:
        raise ValueError("일자별 집계가 비어 있습니다.")
    if daily["pipeline_run_id"].nunique(dropna=False) != 1:
        raise ValueError("일자별 집계에 여러 pipeline_run_id가 섞여 있습니다.")

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(daily["order_day"], daily["completed_order_amount"], marker="o")
    axis.set(
        title="Completed-order amount by day",
        xlabel="Order day",
        ylabel="Completed-order amount",
    )
    axis.tick_params(axis="x", rotation=45)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()

    destination = paths["figure_dir"] / "ch14_daily_sales.png"
    with tempfile.NamedTemporaryFile(
        dir=destination.parent, suffix=".png", delete=False
    ) as file:
        temporary = Path(file.name)
    try:
        figure.savefig(temporary, dpi=150, bbox_inches="tight")
        temporary.replace(destination)
    finally:
        plt.close(figure)
        temporary.unlink(missing_ok=True)
    return {"daily_sales_figure": destination}


def _single_run_id(frame: pd.DataFrame, label: str) -> str:
    _require_columns(label, frame, ["pipeline_run_id"])
    values = frame["pipeline_run_id"].dropna().astype(str).unique().tolist()
    if len(values) != 1:
        raise ValueError(f"{label}의 pipeline_run_id가 1개가 아닙니다: {values}")
    return values[0]


def generate_report(base_dir: str | Path = ".") -> Path:
    paths = get_project_paths(base_dir)
    daily = pd.read_csv(paths["report_dir"] / "ch14_daily_sales.csv")
    category = pd.read_csv(paths["report_dir"] / "ch14_category_sales.csv")
    daily_run_id = _single_run_id(daily, "daily")
    category_run_id = _single_run_id(category, "category")
    if daily_run_id != category_run_id:
        raise ValueError(
            f"daily/category run id가 다릅니다: {daily_run_id} != {category_run_id}"
        )
    if daily.empty or category.empty:
        raise ValueError("보고서 입력 집계가 비어 있습니다.")

    total = float(daily["completed_order_amount"].sum())
    count = int(daily["completed_order_count"].sum())
    top = str(category.iloc[0]["category"])
    text = f'''# Chapter 14 Airflow 자동화 보고서

- Pipeline Run ID: `{daily_run_id}`
- 집계 범위: `order_status == "completed"`
- 금액 정의: `quantity × unit_price` 합계
- 완료 주문 기준 금액 합계: {total:,.0f}
- 완료 주문 수: {count:,}
- 완료 주문 금액 1위 카테고리: {top}

이 금액은 할인, 배송비, 세금, 부분 환불과 정산 기준을 반영한 회계상 순매출이 아닙니다.
파이프라인 성공은 실행과 산출물 생성을 뜻하며, 업무 해석에는 사람의 검토가 필요합니다.

![Completed-order amount](figures/ch14_daily_sales.png)
'''
    return _atomic_text(text, paths["report_dir"] / "ch14_airflow_report.md")


def _read_csv_for_validation(path: Path) -> tuple[pd.DataFrame | None, str]:
    if not path.is_file() or path.stat().st_size == 0:
        return None, "missing_or_empty"
    try:
        return pd.read_csv(path), "ok"
    except Exception as exc:
        return None, f"read_error:{type(exc).__name__}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_artifact_manifest(base_dir: str | Path, pipeline_run_id: str) -> Path:
    """Write run-consistency evidence for CSV, report and PNG artifacts.

    SHA-256 proves byte-level integrity only; it does not prove analytical validity.
    """
    paths = get_project_paths(base_dir)
    artifacts = [
        paths["report_dir"] / "ch14_daily_sales.csv",
        paths["report_dir"] / "ch14_category_sales.csv",
        paths["report_dir"] / "ch14_airflow_report.md",
        paths["figure_dir"] / "ch14_daily_sales.png",
    ]
    generated_at = utc_now_iso()
    rows = []
    for path in artifacts:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"manifest 대상 산출물이 없거나 비어 있습니다: {path}")
        rows.append({
            "artifact": str(path.relative_to(paths["base_dir"])),
            "pipeline_run_id": pipeline_run_id,
            "generated_at_utc": generated_at,
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "sha256_scope": "byte_integrity_not_analysis_validity",
        })
    destination = paths["report_dir"] / ARTIFACT_MANIFEST
    _atomic_csv(pd.DataFrame(rows), destination)
    return destination


def validate_outputs(base_dir: str | Path = ".") -> pd.DataFrame:
    """Validate artifacts and always write a validation log before raising.

    The function does not treat existence as sufficient.  It checks freshness,
    readable row counts, run-id consistency, cross-aggregation totals, category
    ratios and report scope.  A successful Airflow task is therefore not enough.
    """
    paths = get_project_paths(base_dir)
    inputs = expected_input_files(base_dir)
    missing_inputs = [path for path in inputs if not path.is_file()]
    if missing_inputs:
        raise FileNotFoundError(
            "검증에 필요한 원본 파일이 없습니다: "
            + ", ".join(map(str, missing_inputs))
        )
    raw_mtime = max(path.stat().st_mtime for path in inputs)

    rows: list[dict[str, object]] = []
    for path in expected_output_files(base_dir):
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        modified_at = _mtime_utc(path) if exists else ""
        freshness_seconds = path.stat().st_mtime - raw_mtime if exists else None
        fresh = bool(exists and freshness_seconds is not None and freshness_seconds >= -1)
        row_count: int | None = None
        readable = True
        if exists and path.suffix == ".csv":
            frame, read_status = _read_csv_for_validation(path)
            readable = read_status == "ok"
            row_count = len(frame) if frame is not None else -1
        ok = (
            exists
            and size > 0
            and fresh
            and readable
            and (row_count is None or row_count > 0)
        )
        rows.append(
            {
                "check_type": "file",
                "target": str(path),
                "value": (
                    f"size={size}; modified_at_utc={modified_at}; "
                    f"freshness_seconds={freshness_seconds}; rows={row_count}; "
                    f"readable={readable}"
                ),
                "status": "ok" if ok else "error",
            }
        )

    daily_path = paths["report_dir"] / "ch14_daily_sales.csv"
    category_path = paths["report_dir"] / "ch14_category_sales.csv"
    metadata_path = paths["report_dir"] / "ch14_pipeline_run_metadata.csv"
    report_path = paths["report_dir"] / "ch14_airflow_report.md"

    daily, daily_read = _read_csv_for_validation(daily_path)
    category, category_read = _read_csv_for_validation(category_path)
    metadata, metadata_read = _read_csv_for_validation(metadata_path)

    run_id = ""
    if daily is not None and category is not None:
        try:
            daily_run_id = _single_run_id(daily, "daily")
            category_run_id = _single_run_id(category, "category")
            run_id_match = daily_run_id == category_run_id
            run_id = daily_run_id if run_id_match else ""
            rows.append(
                {
                    "check_type": "run_consistency",
                    "target": "daily_vs_category_pipeline_run_id",
                    "value": f"daily={daily_run_id}; category={category_run_id}",
                    "status": "ok" if run_id_match else "error",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "check_type": "run_consistency",
                    "target": "daily_vs_category_pipeline_run_id",
                    "value": type(exc).__name__,
                    "status": "error",
                }
            )

        required_daily = {"completed_order_amount"}
        required_category = {"completed_order_amount", "amount_ratio_pct"}
        if required_daily.issubset(daily.columns) and required_category.issubset(
            category.columns
        ):
            difference = float(
                daily["completed_order_amount"].sum()
                - category["completed_order_amount"].sum()
            )
            ratio_sum = float(category["amount_ratio_pct"].sum())
            rows.extend(
                [
                    {
                        "check_type": "cross_total",
                        "target": "daily_vs_category_completed_order_amount",
                        "value": difference,
                        "status": "ok"
                        if abs(difference) <= TOTAL_TOLERANCE
                        else "error",
                    },
                    {
                        "check_type": "ratio",
                        "target": "category_amount_ratio_pct_sum",
                        "value": ratio_sum,
                        "status": "ok"
                        if abs(ratio_sum - 100) <= RATIO_TOLERANCE
                        else "error",
                    },
                ]
            )
        else:
            rows.append(
                {
                    "check_type": "cross_total",
                    "target": "daily/category required columns",
                    "value": "missing required aggregation columns",
                    "status": "error",
                }
            )
    else:
        rows.append(
            {
                "check_type": "cross_total",
                "target": "daily/category readable",
                "value": f"daily={daily_read}; category={category_read}",
                "status": "error",
            }
        )

    if metadata is not None:
        try:
            metadata_run_id = _single_run_id(metadata, "run_metadata")
            metadata_match = bool(run_id and metadata_run_id == run_id)
            rows.append(
                {
                    "check_type": "run_consistency",
                    "target": "run_metadata_pipeline_run_id",
                    "value": metadata_run_id,
                    "status": "ok" if metadata_match else "error",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "check_type": "run_consistency",
                    "target": "run_metadata_pipeline_run_id",
                    "value": type(exc).__name__,
                    "status": "error",
                }
            )
    else:
        rows.append(
            {
                "check_type": "run_consistency",
                "target": "run_metadata readable",
                "value": metadata_read,
                "status": "error",
            }
        )

    if report_path.is_file() and report_path.stat().st_size > 0:
        try:
            report = report_path.read_text(encoding="utf-8")
            scope_ok = (
                'order_status == "completed"' in report
                and "회계상 순매출이 아닙니다" in report
            )
            run_ok = bool(run_id and f"`{run_id}`" in report)
            rows.extend(
                [
                    {
                        "check_type": "report_scope",
                        "target": "ch14_airflow_report.md",
                        "value": scope_ok,
                        "status": "ok" if scope_ok else "error",
                    },
                    {
                        "check_type": "run_consistency",
                        "target": "report_pipeline_run_id",
                        "value": run_ok,
                        "status": "ok" if run_ok else "error",
                    },
                ]
            )
        except Exception as exc:
            rows.append(
                {
                    "check_type": "report_scope",
                    "target": "ch14_airflow_report.md",
                    "value": type(exc).__name__,
                    "status": "error",
                }
            )
    else:
        rows.append(
            {
                "check_type": "report_scope",
                "target": "ch14_airflow_report.md",
                "value": "missing_or_empty",
                "status": "error",
            }
        )

    validation = pd.DataFrame(rows)
    _atomic_csv(validation, paths["report_dir"] / VALIDATION_LOG)
    if run_id:
        run_dir = paths["report_dir"] / "runs" / run_id
        _atomic_csv(validation, run_dir / "validation.csv")
        if metadata is not None:
            _atomic_csv(metadata, run_dir / "run_metadata.csv")
    failed = validation[validation["status"].ne("ok")]
    if not failed.empty:
        raise RuntimeError(
            "결과 검증 실패: " + ", ".join(failed["target"].astype(str))
        )
    return validation


def run_local_pipeline(base_dir: str | Path = ".") -> dict[str, object]:
    pipeline_run_id = new_pipeline_run_id()
    input_check = check_input_files(base_dir)
    preprocessing_outputs = run_preprocessing(base_dir)
    analysis_outputs = run_analysis(base_dir, run_id=pipeline_run_id)
    figure_outputs = generate_visualizations(base_dir)
    report_path = generate_report(base_dir)
    artifact_manifest = create_artifact_manifest(base_dir, pipeline_run_id)
    validation_log = validate_outputs(base_dir)
    return {
        "pipeline_run_id": pipeline_run_id,
        "input_check": input_check,
        "preprocessing_outputs": preprocessing_outputs,
        "analysis_outputs": analysis_outputs,
        "figure_outputs": figure_outputs,
        "report_path": report_path,
        "artifact_manifest": artifact_manifest,
        "validation_log": validation_log,
        "setup_guide": create_airflow_setup_guide(),
        "setup_guide_path": analysis_outputs["setup_guide"],
    }


def write_validation_log_csv(
    rows: list[dict[str, object]], output_path: str | Path
) -> None:
    """Compatibility helper that keeps small validation logs atomic."""
    path = Path(output_path)
    if not rows:
        _atomic_csv(pd.DataFrame(columns=["status"]), path)
        return
    fieldnames = sorted({key for row in rows for key in row})
    normalized_rows = [{name: row.get(name, "") for name in fieldnames} for row in rows]
    _atomic_csv(pd.DataFrame(normalized_rows, columns=fieldnames), path)
