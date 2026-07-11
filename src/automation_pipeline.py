"""Chapter 14 validated analysis-automation utilities.

The local runner and Airflow DAG call the same deterministic functions. The
pipeline validates schemas and key relationships, aggregates completed orders
only, writes artifacts atomically, and verifies freshness and cross-file totals.
"""
from __future__ import annotations

import csv
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

RAW_FILENAMES = ["customers.csv", "products.csv", "orders.csv", "order_items.csv"]
PROCESSED_FILENAMES = [
    "customers_clean.csv", "products_clean.csv", "orders_clean.csv",
    "order_items_clean.csv",
]
REPORT_FILENAMES = [
    "ch14_daily_sales.csv", "ch14_category_sales.csv",
    "ch14_pipeline_task_summary.csv", "ch14_airflow_setup_guide.csv",
    "ch14_pipeline_run_metadata.csv", "ch14_airflow_report.md",
]
VALIDATION_LOG = "ch14_airflow_validation_log.csv"
REQUIRED = {
    "customers": {"customer_id", "gender", "age", "city", "signup_date"},
    "products": {"product_id", "product_name", "category", "price"},
    "orders": {"order_id", "customer_id", "order_date", "payment_method", "order_status"},
    "order_items": {"order_id", "product_id", "quantity", "unit_price"},
}
STATUS_MAP = {
    "complete": "completed", "completed": "completed", "완료": "completed",
    "cancel": "cancelled", "cancelled": "cancelled", "canceled": "cancelled", "취소": "cancelled",
    "refund": "refunded", "refunded": "refunded", "환불": "refunded",
}


def project_root_from_file(file_path: str | Path) -> Path:
    return Path(file_path).resolve().parents[1]


def get_project_paths(base_dir: str | Path = ".") -> dict[str, Path]:
    base = Path(os.getenv("PROJECT_ROOT", str(base_dir))).resolve() if str(base_dir) == "." else Path(base_dir).resolve()
    paths = {
        "base_dir": base, "raw_dir": base / "data" / "raw",
        "processed_dir": base / "data" / "processed", "report_dir": base / "reports",
        "figure_dir": base / "reports" / "figures",
    }
    for key in ("processed_dir", "report_dir", "figure_dir"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def expected_input_files(base_dir: str | Path = ".") -> list[Path]:
    raw = get_project_paths(base_dir)["raw_dir"]
    return [raw / name for name in RAW_FILENAMES]


def expected_output_files(base_dir: str | Path = ".") -> list[Path]:
    p = get_project_paths(base_dir)
    return (
        [p["processed_dir"] / name for name in PROCESSED_FILENAMES]
        + [p["report_dir"] / name for name in REPORT_FILENAMES]
        + [p["figure_dir"] / "ch14_daily_sales.png"]
    )


def _atomic_csv(frame: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as f:
        temporary = Path(f.name)
    try:
        frame.to_csv(temporary, index=False, encoding="utf-8-sig")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _atomic_text(text: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as f:
        f.write(text)
        temporary = Path(f.name)
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
    missing = int(frame[key].isna().sum())
    duplicated = int(frame[key].duplicated(keep=False).sum())
    if missing or duplicated:
        raise ValueError(f"{name}.{key} 무결성 오류: 결측 {missing}건, 중복 행 {duplicated}건")


def _convert_numeric(name: str, frame: pd.DataFrame, column: str) -> None:
    before = frame[column].isna()
    converted = pd.to_numeric(frame[column], errors="coerce")
    failed = int((~before & converted.isna()).sum())
    if failed:
        raise ValueError(f"{name}.{column} 숫자 변환 실패: {failed}건")
    frame[column] = converted


def _convert_date(name: str, frame: pd.DataFrame, column: str) -> None:
    before = frame[column].isna()
    converted = pd.to_datetime(frame[column], errors="coerce")
    failed = int((~before & converted.isna()).sum())
    if failed:
        raise ValueError(f"{name}.{column} 날짜 변환 실패: {failed}건")
    frame[column] = converted


def _require_reference(child_name: str, child: pd.DataFrame, child_key: str, parent_name: str, parent: pd.DataFrame, parent_key: str) -> None:
    invalid = ~child[child_key].isin(parent[parent_key])
    if invalid.any():
        examples = child.loc[invalid, child_key].dropna().astype(str).head(5).tolist()
        raise ValueError(
            f"{child_name}.{child_key} 중 {int(invalid.sum())}건이 "
            f"{parent_name}.{parent_key}에 없습니다. 예: {examples}"
        )


def check_input_files(base_dir: str | Path = ".") -> pd.DataFrame:
    rows = []
    for path in expected_input_files(base_dir):
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        rows.append({"file": str(path), "exists": exists, "size_bytes": size, "status": "ok" if exists and size else "error"})
    result = pd.DataFrame(rows)
    failed = result[result["status"].ne("ok")]
    if not failed.empty:
        raise FileNotFoundError("필수 원본 CSV가 없거나 비어 있습니다: " + ", ".join(failed["file"]))
    return result


def run_preprocessing(base_dir: str | Path = ".") -> dict[str, Path]:
    p = get_project_paths(base_dir)
    check_input_files(base_dir)
    data = {
        "customers": pd.read_csv(p["raw_dir"] / "customers.csv"),
        "products": pd.read_csv(p["raw_dir"] / "products.csv"),
        "orders": pd.read_csv(p["raw_dir"] / "orders.csv"),
        "order_items": pd.read_csv(p["raw_dir"] / "order_items.csv"),
    }
    for name, frame in data.items():
        for col in frame.select_dtypes(include="object").columns:
            frame[col] = frame[col].astype("string").str.strip().replace("", pd.NA)
        _require_columns(name, frame, REQUIRED[name])
    customers, products, orders, items = data.values()
    _require_unique("customers", customers, "customer_id")
    _require_unique("products", products, "product_id")
    _require_unique("orders", orders, "order_id")
    _convert_numeric("customers", customers, "age")
    _convert_date("customers", customers, "signup_date")
    _convert_numeric("products", products, "price")
    _convert_date("orders", orders, "order_date")
    _convert_numeric("order_items", items, "quantity")
    _convert_numeric("order_items", items, "unit_price")
    for name, frame, columns in [
        ("customers", customers, ["customer_id", "age", "city", "signup_date"]),
        ("products", products, ["product_id", "product_name", "category", "price"]),
        ("orders", orders, ["order_id", "customer_id", "order_date", "payment_method", "order_status"]),
        ("order_items", items, ["order_id", "product_id", "quantity", "unit_price"]),
    ]:
        missing = frame[columns].isna().sum()
        if missing.gt(0).any():
            raise ValueError(f"{name} 필수값 결측: {missing[missing.gt(0)].to_dict()}")
    if products["price"].le(0).any() or items["quantity"].le(0).any() or items["unit_price"].le(0).any():
        raise ValueError("price, quantity, unit_price에는 0보다 큰 값만 허용됩니다.")
    orders["order_status"] = orders["order_status"].astype("string").str.lower().replace(STATUS_MAP)
    unknown = sorted(set(orders["order_status"].dropna()) - {"completed", "cancelled", "refunded"})
    if unknown:
        raise ValueError(f"알 수 없는 order_status가 있습니다: {unknown}")
    _require_reference("orders", orders, "customer_id", "customers", customers, "customer_id")
    _require_reference("order_items", items, "order_id", "orders", orders, "order_id")
    _require_reference("order_items", items, "product_id", "products", products, "product_id")
    calculated = items["quantity"] * items["unit_price"]
    if "line_total" in items:
        current = pd.to_numeric(items["line_total"], errors="coerce")
        mismatch = current.isna() | current.sub(calculated).abs().gt(0.01)
        if mismatch.any():
            raise ValueError(f"line_total이 quantity × unit_price와 다른 행이 {int(mismatch.sum())}건 있습니다.")
    items["line_total"] = calculated
    frames = {
        "customers": customers.sort_values("customer_id"),
        "products": products.sort_values("product_id"),
        "orders": orders.sort_values(["order_date", "order_id"]),
        "order_items": items.sort_values(["order_id", "product_id"]),
    }
    outputs = {name: p["processed_dir"] / f"{name}_clean.csv" for name in frames}
    for name, frame in frames.items():
        _atomic_csv(frame.reset_index(drop=True), outputs[name])
    return outputs


def create_pipeline_task_summary() -> pd.DataFrame:
    return pd.DataFrame({
        "task_id": ["check_input_files", "run_preprocessing", "run_analysis", "generate_visualizations", "generate_report", "validate_outputs"],
        "purpose": ["원본 CSV 확인", "스키마·타입·키 검증", "완료 주문 기준 집계", "추이 그래프 생성", "Markdown 보고서 생성", "최신성·행 수·총합 검증"],
        "retry_safety": ["읽기 전용", "전체 파일 원자적 교체", "전체 파일 원자적 교체", "PNG 원자적 교체", "Markdown 원자적 교체", "검증 로그 원자적 교체"],
    })


def create_airflow_setup_guide() -> pd.DataFrame:
    return pd.DataFrame({
        "step": ["Docker 확인", "Python 사전 검증", ".env 준비", "비밀값 변경", "빌드·초기화", "서비스 시작", "DAG 실행", "결과 검증", "종료"],
        "action": ["docker compose version", "python scripts/run_ch14_pipeline.py", "cp .env.example .env", "CHANGE_ME 값 교체", "docker compose build && docker compose up airflow-init", "docker compose up -d", "UI에서 수동 실행", "validation_log status 확인", "docker compose down"],
    })


def run_analysis(base_dir: str | Path = ".") -> dict[str, Path]:
    p = get_project_paths(base_dir)
    orders = pd.read_csv(p["processed_dir"] / "orders_clean.csv", parse_dates=["order_date"])
    items = pd.read_csv(p["processed_dir"] / "order_items_clean.csv")
    products = pd.read_csv(p["processed_dir"] / "products_clean.csv")
    _require_unique("orders", orders, "order_id")
    _require_unique("products", products, "product_id")
    _require_reference("order_items", items, "order_id", "orders", orders, "order_id")
    _require_reference("order_items", items, "product_id", "products", products, "product_id")
    completed_orders = orders.loc[orders["order_status"].eq("completed"), ["order_id", "order_date"]]
    completed = items.merge(completed_orders, on="order_id", how="inner", validate="many_to_one")
    completed = completed.merge(products[["product_id", "category"]], on="product_id", how="left", validate="many_to_one")
    if completed.empty or completed["category"].isna().any():
        raise ValueError("완료 주문이 없거나 상품 카테고리를 연결하지 못했습니다.")
    completed["order_day"] = pd.to_datetime(completed["order_date"]).dt.normalize()
    daily = completed.groupby("order_day", as_index=False).agg(
        completed_order_amount=("line_total", "sum"), completed_order_count=("order_id", "nunique")
    ).sort_values("order_day")
    daily["avg_completed_order_amount"] = (daily["completed_order_amount"] / daily["completed_order_count"]).round(2)
    category = completed.groupby("category", as_index=False).agg(
        completed_quantity=("quantity", "sum"), completed_order_amount=("line_total", "sum")
    ).sort_values("completed_order_amount", ascending=False)
    total = float(category["completed_order_amount"].sum())
    category["amount_ratio_pct"] = (category["completed_order_amount"] / total * 100).round(2)
    metadata = pd.DataFrame([{
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aggregation_scope": "order_status == completed",
        "amount_definition": "sum(quantity * unit_price)",
        "is_accounting_net_revenue": False,
        "completed_order_count": int(completed_orders["order_id"].nunique()),
        "completed_order_amount": total,
    }])
    outputs = {
        "daily_sales": p["report_dir"] / "ch14_daily_sales.csv",
        "category_sales": p["report_dir"] / "ch14_category_sales.csv",
        "task_summary": p["report_dir"] / "ch14_pipeline_task_summary.csv",
        "setup_guide": p["report_dir"] / "ch14_airflow_setup_guide.csv",
        "run_metadata": p["report_dir"] / "ch14_pipeline_run_metadata.csv",
    }
    for frame, key in [(daily, "daily_sales"), (category, "category_sales"), (create_pipeline_task_summary(), "task_summary"), (create_airflow_setup_guide(), "setup_guide"), (metadata, "run_metadata")]:
        _atomic_csv(frame, outputs[key])
    return outputs


def generate_visualizations(base_dir: str | Path = ".") -> dict[str, Path]:
    p = get_project_paths(base_dir)
    daily = pd.read_csv(p["report_dir"] / "ch14_daily_sales.csv", parse_dates=["order_day"])
    if daily.empty:
        raise ValueError("일자별 집계가 비어 있습니다.")
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(daily["order_day"], daily["completed_order_amount"], marker="o")
    axis.set(title="Completed-order amount by day", xlabel="Order day", ylabel="Completed-order amount")
    axis.tick_params(axis="x", rotation=45)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    destination = p["figure_dir"] / "ch14_daily_sales.png"
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".png", delete=False) as f:
        temporary = Path(f.name)
    try:
        figure.savefig(temporary, dpi=150, bbox_inches="tight")
        temporary.replace(destination)
    finally:
        plt.close(figure)
        temporary.unlink(missing_ok=True)
    return {"daily_sales_figure": destination}


def generate_report(base_dir: str | Path = ".") -> Path:
    p = get_project_paths(base_dir)
    daily = pd.read_csv(p["report_dir"] / "ch14_daily_sales.csv")
    category = pd.read_csv(p["report_dir"] / "ch14_category_sales.csv")
    total = float(daily["completed_order_amount"].sum())
    count = int(daily["completed_order_count"].sum())
    top = str(category.iloc[0]["category"]) if not category.empty else "확인 불가"
    text = f'''# Chapter 14 Airflow 자동화 보고서

- 집계 범위: `order_status == "completed"`
- 금액 정의: `quantity × unit_price` 합계
- 완료 주문 기준 금액 합계: {total:,.0f}
- 완료 주문 수: {count:,}
- 완료 주문 금액 1위 카테고리: {top}

이 금액은 할인, 배송비, 세금, 부분 환불과 정산 기준을 반영한 회계상 순매출이 아닙니다.
파이프라인 성공은 실행과 산출물 생성을 뜻하며, 업무 해석에는 사람의 검토가 필요합니다.

![Completed-order amount](figures/ch14_daily_sales.png)
'''
    return _atomic_text(text, p["report_dir"] / "ch14_airflow_report.md")


def validate_outputs(base_dir: str | Path = ".") -> pd.DataFrame:
    p = get_project_paths(base_dir)
    raw_mtime = max(path.stat().st_mtime for path in expected_input_files(base_dir))
    rows = []
    for path in expected_output_files(base_dir):
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        fresh = exists and path.stat().st_mtime >= raw_mtime - 1
        row_count = None
        if exists and path.suffix == ".csv":
            try:
                row_count = len(pd.read_csv(path))
            except Exception:
                row_count = -1
        ok = exists and size > 0 and fresh and (row_count is None or row_count > 0)
        rows.append({"check_type": "file", "target": str(path), "value": f"size={size}; fresh={fresh}; rows={row_count}", "status": "ok" if ok else "error"})
    daily = pd.read_csv(p["report_dir"] / "ch14_daily_sales.csv")
    category = pd.read_csv(p["report_dir"] / "ch14_category_sales.csv")
    difference = float(daily["completed_order_amount"].sum() - category["completed_order_amount"].sum())
    ratio_sum = float(category["amount_ratio_pct"].sum())
    rows += [
        {"check_type": "cross_total", "target": "daily_vs_category_completed_order_amount", "value": difference, "status": "ok" if abs(difference) <= 0.01 else "error"},
        {"check_type": "ratio", "target": "category_amount_ratio_pct_sum", "value": ratio_sum, "status": "ok" if abs(ratio_sum - 100) <= 0.1 else "error"},
    ]
    report = (p["report_dir"] / "ch14_airflow_report.md").read_text(encoding="utf-8")
    scope_ok = 'order_status == "completed"' in report and "회계상 순매출이 아닙니다" in report
    rows.append({"check_type": "report_scope", "target": "ch14_airflow_report.md", "value": scope_ok, "status": "ok" if scope_ok else "error"})
    validation = pd.DataFrame(rows)
    _atomic_csv(validation, p["report_dir"] / VALIDATION_LOG)
    failed = validation[validation["status"].ne("ok")]
    if not failed.empty:
        raise RuntimeError("결과 검증 실패: " + ", ".join(failed["target"].astype(str)))
    return validation


def run_local_pipeline(base_dir: str | Path = ".") -> dict[str, object]:
    input_check = check_input_files(base_dir)
    preprocessing_outputs = run_preprocessing(base_dir)
    analysis_outputs = run_analysis(base_dir)
    figure_outputs = generate_visualizations(base_dir)
    report_path = generate_report(base_dir)
    validation_log = validate_outputs(base_dir)
    return {
        "input_check": input_check, "preprocessing_outputs": preprocessing_outputs,
        "analysis_outputs": analysis_outputs, "figure_outputs": figure_outputs,
        "report_path": report_path, "validation_log": validation_log,
        "setup_guide": create_airflow_setup_guide(),
        "setup_guide_path": analysis_outputs["setup_guide"],
    }


def write_validation_log_csv(rows: list[dict[str, object]], output_path: str | Path) -> None:
    """Compatibility helper for small external integrations."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
