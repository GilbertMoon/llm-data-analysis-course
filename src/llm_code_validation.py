"""Chapter 12 utilities for reviewing LLM-generated analysis code safely.

Generated code is treated as an untrusted draft.  The chapter separates:

1. data/schema/business-logic validation,
2. static screening for risky operations,
3. human approval before any limited execution,
4. post-execution validation evidence.

The static scanner never executes the supplied code and is only a screening aid.
A clean scan is not proof that code is safe.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

import pandas as pd


COMPLETED_STATUS = "completed"
TOTAL_TOLERANCE = 1e-6

REQUIRED_COLUMNS: dict[str, set[str]] = {
    "customers": {"customer_id", "gender", "age", "city"},
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

RELATIONSHIP_CHECKS = [
    {
        "left_dataset": "order_items",
        "right_dataset": "products",
        "key": "product_id",
        "purpose": "상품 정보와 주문 상세 연결",
    },
    {
        "left_dataset": "order_items",
        "right_dataset": "orders",
        "key": "order_id",
        "purpose": "주문 정보와 주문 상세 연결",
    },
    {
        "left_dataset": "orders",
        "right_dataset": "customers",
        "key": "customer_id",
        "purpose": "주문 정보와 고객 정보 연결",
    },
]

# Leakage rules are problem-specific.  Chapter 09 regression and Chapter 10
# classification intentionally have different prediction-time contracts.
REGRESSION_FORBIDDEN_FEATURES = {
    "order_total",
    "line_total",
    "quantity",
    "unit_price",
    "item_count",
    "total_quantity",
    "avg_unit_price",
    "order_status",
    "order_id",
    "customer_id",
}

CLASSIFICATION_FORBIDDEN_FEATURES = {
    "order_status",
    "is_cancelled",
    "order_id",
    "customer_id",
    "product_id",
    "line_total",
    "quantity",
    "unit_price",
    "cancel_reason",
    "cancelled_at",
}

CLASSIFICATION_CONDITIONAL_FEATURES = {
    "item_count",
    "total_quantity",
    "order_amount",
}

RISKY_IMPORT_ROOTS = {
    "ensurepip",
    "ftplib",
    "http",
    "os",
    "pip",
    "requests",
    "shutil",
    "socket",
    "subprocess",
    "urllib",
}

RISKY_CALLS = {
    "eval": ("critical", "동적 코드 실행"),
    "exec": ("critical", "동적 코드 실행"),
    "compile": ("high", "동적 코드 생성"),
    "__import__": ("high", "동적 모듈 로드"),
    "os.system": ("critical", "운영체제 명령 실행"),
    "os.popen": ("critical", "운영체제 명령 실행"),
    "os.remove": ("critical", "파일 삭제"),
    "os.unlink": ("critical", "파일 삭제"),
    "os.rename": ("high", "파일 이름 변경"),
    "os.replace": ("high", "파일 교체"),
    "subprocess.run": ("critical", "외부 프로세스 실행"),
    "subprocess.Popen": ("critical", "외부 프로세스 실행"),
    "subprocess.call": ("critical", "외부 프로세스 실행"),
    "subprocess.check_call": ("critical", "외부 프로세스 실행"),
    "subprocess.check_output": ("critical", "외부 프로세스 실행"),
    "shutil.rmtree": ("critical", "폴더 재귀 삭제"),
    "shutil.move": ("high", "파일·폴더 이동"),
    "requests.get": ("high", "외부 네트워크 요청"),
    "requests.post": ("high", "외부 네트워크 요청"),
    "requests.put": ("high", "외부 네트워크 요청"),
    "requests.patch": ("high", "외부 네트워크 요청"),
    "requests.delete": ("high", "외부 네트워크 요청"),
    "urllib.request.urlopen": ("high", "외부 네트워크 요청"),
    "socket.socket": ("high", "네트워크 소켓 생성"),
}

WRITE_METHOD_SUFFIXES = (
    ".to_csv",
    ".to_excel",
    ".to_json",
    ".to_pickle",
    ".write_text",
    ".write_bytes",
    ".touch",
    ".rename",
    ".replace",
)
DELETE_METHOD_SUFFIXES = (".unlink", ".rmdir")

DEFAULT_STATIC_SCAN_EXAMPLE = '''
import requests

response = requests.get("https://example.com/data.csv")
open("download.csv", "wb").write(response.content)
'''.strip()


# ---------------------------------------------------------------------------
# Data loading and structural checks
# ---------------------------------------------------------------------------


def _required_file_map(processed_dir: str | Path) -> dict[str, Path]:
    root = Path(processed_dir)
    return {
        "customers": root / "customers_clean.csv",
        "products": root / "products_clean.csv",
        "orders": root / "orders_clean.csv",
        "order_items": root / "order_items_clean.csv",
    }


def load_validation_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """Load Chapter 05 processed files only; never silently fall back to raw data."""
    file_map = _required_file_map(processed_dir)
    missing = [path for path in file_map.values() if not path.exists()]
    if missing:
        missing_text = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(
            "Chapter 12는 processed 데이터에서 시작합니다. raw로 자동 fallback하지 않습니다.\n"
            "먼저 python scripts/preprocess_data.py 를 실행하세요.\n"
            f"누락 파일:\n{missing_text}"
        )
    return {name: pd.read_csv(path) for name, path in file_map.items()}


def build_dataset_inventory(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Summarize observed structure without copying raw row values."""
    rows: list[dict[str, object]] = []
    for name in REQUIRED_COLUMNS:
        df = datasets.get(name)
        rows.append(
            {
                "dataset": name,
                "exists": df is not None,
                "rows": int(df.shape[0]) if df is not None else None,
                "columns": int(df.shape[1]) if df is not None else None,
                "column_list": ", ".join(map(str, df.columns)) if df is not None else "",
                "missing_values": int(df.isna().sum().sum()) if df is not None else None,
                "duplicated_rows": int(df.duplicated().sum()) if df is not None else None,
            }
        )
    return pd.DataFrame(rows)


def validate_required_columns(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset_name, required_columns in REQUIRED_COLUMNS.items():
        df = datasets.get(dataset_name)
        for column in sorted(required_columns):
            exists = bool(df is not None and column in df.columns)
            rows.append(
                {
                    "dataset": dataset_name,
                    "column": column,
                    "dataset_exists": df is not None,
                    "exists": exists,
                    "status": "PASS" if exists else "FAIL",
                }
            )
    return pd.DataFrame(rows)


def validate_primary_keys(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset_name, key in PRIMARY_KEYS.items():
        df = datasets.get(dataset_name)
        key_exists = bool(df is not None and key in df.columns)
        missing_count = None
        duplicated_count = None
        if key_exists and df is not None:
            missing_count = int(df[key].isna().sum())
            duplicated_count = int(df.loc[df[key].notna(), key].duplicated().sum())
        status = (
            "PASS"
            if key_exists and missing_count == 0 and duplicated_count == 0
            else "FAIL"
        )
        rows.append(
            {
                "dataset": dataset_name,
                "primary_key": key,
                "key_exists": key_exists,
                "missing_key_count": missing_count,
                "duplicated_key_count": duplicated_count,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def validate_relationship_keys(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for check in RELATIONSHIP_CHECKS:
        left_name = check["left_dataset"]
        right_name = check["right_dataset"]
        key = check["key"]
        left_df = datasets.get(left_name)
        right_df = datasets.get(right_name)
        left_has_key = bool(left_df is not None and key in left_df.columns)
        right_has_key = bool(right_df is not None and key in right_df.columns)
        missing_left = None
        invalid_reference = None
        duplicate_parent = None

        if left_has_key and left_df is not None:
            missing_left = int(left_df[key].isna().sum())
        if right_has_key and right_df is not None:
            duplicate_parent = int(
                right_df.loc[right_df[key].notna(), key].duplicated().sum()
            )
        if left_has_key and right_has_key and left_df is not None and right_df is not None:
            left_non_null = left_df.loc[left_df[key].notna(), key]
            parent_keys = set(right_df.loc[right_df[key].notna(), key])
            invalid_reference = int((~left_non_null.isin(parent_keys)).sum())

        status = (
            "PASS"
            if left_has_key
            and right_has_key
            and (missing_left or 0) == 0
            and (duplicate_parent or 0) == 0
            and (invalid_reference or 0) == 0
            else "FAIL"
        )
        rows.append(
            {
                "purpose": check["purpose"],
                "left_dataset": left_name,
                "right_dataset": right_name,
                "key": key,
                "left_has_key": left_has_key,
                "right_has_key": right_has_key,
                "missing_left_key_count": missing_left,
                "duplicated_parent_key_count": duplicate_parent,
                "invalid_reference_count": invalid_reference,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def assert_validation_ready(
    required_column_check: pd.DataFrame,
    primary_key_check: pd.DataFrame,
    relationship_check: pd.DataFrame,
) -> None:
    """Fail before aggregation when required schema or relationship evidence fails."""
    failures: list[str] = []
    for row in required_column_check.loc[required_column_check["status"].eq("FAIL")].itertuples(index=False):
        failures.append(f"required column: {row.dataset}.{row.column}")
    for row in primary_key_check.loc[primary_key_check["status"].eq("FAIL")].itertuples(index=False):
        failures.append(
            f"primary key: {row.dataset}.{row.primary_key} "
            f"exists={row.key_exists}, missing={row.missing_key_count}, duplicate={row.duplicated_key_count}"
        )
    for row in relationship_check.loc[relationship_check["status"].eq("FAIL")].itertuples(index=False):
        failures.append(
            f"relationship: {row.left_dataset}.{row.key} -> {row.right_dataset}.{row.key}"
        )
    if failures:
        raise ValueError(
            "분석 코드를 실행하기 전에 해결해야 할 데이터 구조 문제가 있습니다.\n"
            + "\n".join(f"- {item}" for item in failures)
        )


# ---------------------------------------------------------------------------
# Business-rule and aggregation validation
# ---------------------------------------------------------------------------


def ensure_line_total(order_items: pd.DataFrame) -> pd.DataFrame:
    result = order_items.copy()
    required = {"quantity", "unit_price"}
    missing = required - set(result.columns)
    if missing:
        raise KeyError(f"order_items에 필요한 컬럼이 없습니다: {sorted(missing)}")

    original_missing = {
        column: int(result[column].isna().sum()) for column in ["quantity", "unit_price"]
    }
    result["quantity"] = pd.to_numeric(result["quantity"], errors="coerce")
    result["unit_price"] = pd.to_numeric(result["unit_price"], errors="coerce")
    if "line_total" in result.columns:
        result["line_total"] = pd.to_numeric(result["line_total"], errors="coerce")
    else:
        result["line_total"] = result["quantity"] * result["unit_price"]

    conversion_failures = sum(
        max(0, int(result[column].isna().sum()) - original_missing.get(column, 0))
        for column in ["quantity", "unit_price"]
    )
    invalid = result[["quantity", "unit_price", "line_total"]].isna().any(axis=1)
    if invalid.any():
        raise ValueError(
            "quantity, unit_price 또는 line_total에 결측/변환 실패가 있습니다: "
            f"{int(invalid.sum())}행 (새 변환 실패 약 {conversion_failures}건)"
        )

    expected = result["quantity"] * result["unit_price"]
    mismatch = (result["line_total"] - expected).abs().gt(TOTAL_TOLERANCE)
    if mismatch.any():
        raise ValueError(
            "line_total과 quantity × unit_price가 다른 행이 "
            f"{int(mismatch.sum())}개 있습니다."
        )
    return result


def _prepare_completed_order_items(
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    items = ensure_line_total(order_items)
    required = {"order_id", "order_date", "order_status"}
    missing = required - set(orders.columns)
    if missing:
        raise KeyError(f"orders에 필요한 컬럼이 없습니다: {sorted(missing)}")
    if orders["order_id"].isna().any() or orders["order_id"].duplicated().any():
        raise ValueError("orders.order_id는 many_to_one 병합 전에 고유해야 합니다.")

    before_rows = len(items)
    merged = items.merge(
        orders[["order_id", "order_date", "order_status"]],
        on="order_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    unmatched = int(merged["_merge"].ne("both").sum())
    row_preserved = before_rows == len(merged)
    if not row_preserved or unmatched:
        raise ValueError(
            f"orders 병합 검증 실패: before={before_rows}, after={len(merged)}, unmatched={unmatched}"
        )
    merged = merged.drop(columns="_merge")
    normalized = merged["order_status"].astype("string").str.strip().str.lower()
    completed = merged.loc[normalized.eq(COMPLETED_STATUS)].copy()
    if completed.empty:
        raise ValueError("completed 주문 상세가 0행입니다. 집계 범위를 확인하세요.")

    validation = pd.DataFrame(
        [
            {"check_item": "order_merge_row_count", "value": row_preserved, "status": "PASS"},
            {"check_item": "order_merge_unmatched", "value": unmatched, "status": "PASS"},
            {"check_item": "completed_detail_rows", "value": len(completed), "status": "PASS"},
            {"check_item": "included_status", "value": COMPLETED_STATUS, "status": "PASS"},
        ]
    )
    return completed, validation


def _assert_total_equal(label: str, source_total: float, grouped_total: float) -> float:
    diff = float(source_total - grouped_total)
    if abs(diff) > TOTAL_TOLERANCE:
        raise ValueError(
            f"{label} 총합 검증 실패: source={source_total}, grouped={grouped_total}, diff={diff}"
        )
    return diff


def safe_category_sales(
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    completed, order_validation = _prepare_completed_order_items(order_items, orders)
    required = {"product_id", "category"}
    missing = required - set(products.columns)
    if missing:
        raise KeyError(f"products에 필요한 컬럼이 없습니다: {sorted(missing)}")
    if products["product_id"].isna().any() or products["product_id"].duplicated().any():
        raise ValueError("products.product_id는 many_to_one 병합 전에 고유해야 합니다.")

    before_rows = len(completed)
    sales_items = completed.merge(
        products[["product_id", "category"]],
        on="product_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    unmatched = int(sales_items["_merge"].ne("both").sum())
    category_missing = int(sales_items["category"].isna().sum())
    row_preserved = before_rows == len(sales_items)
    if not row_preserved or unmatched or category_missing:
        raise ValueError(
            "상품 병합 검증 실패: "
            f"before={before_rows}, after={len(sales_items)}, unmatched={unmatched}, category_missing={category_missing}"
        )
    sales_items = sales_items.drop(columns="_merge")

    category_sales = (
        sales_items.groupby("category", as_index=False, dropna=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("line_total", "sum"))
        .sort_values("total_sales", ascending=False)
        .reset_index(drop=True)
    )
    source_total = float(sales_items["line_total"].sum())
    grouped_total = float(category_sales["total_sales"].sum())
    diff = _assert_total_equal("category", source_total, grouped_total)
    category_sales["sales_ratio"] = (
        category_sales["total_sales"].div(grouped_total).mul(100).round(2)
        if grouped_total
        else 0.0
    )
    ratio_sum = float(category_sales["sales_ratio"].sum()) if len(category_sales) else 0.0

    validation = pd.concat(
        [
            order_validation,
            pd.DataFrame(
                [
                    {"check_item": "product_merge_row_count", "value": row_preserved, "status": "PASS"},
                    {"check_item": "product_merge_unmatched", "value": unmatched, "status": "PASS"},
                    {"check_item": "category_missing", "value": category_missing, "status": "PASS"},
                    {"check_item": "completed_source_total", "value": source_total, "status": "PASS"},
                    {"check_item": "category_grouped_total", "value": grouped_total, "status": "PASS"},
                    {"check_item": "category_total_difference", "value": diff, "status": "PASS"},
                    {"check_item": "category_ratio_sum_pct", "value": ratio_sum, "status": "PASS" if abs(ratio_sum - 100) <= 0.1 else "WARN"},
                ]
            ),
        ],
        ignore_index=True,
    )
    return category_sales, validation


def safe_monthly_sales(
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    completed, order_validation = _prepare_completed_order_items(order_items, orders)
    original_missing = int(completed["order_date"].isna().sum())
    completed["order_date"] = pd.to_datetime(completed["order_date"], errors="coerce")
    date_missing = int(completed["order_date"].isna().sum())
    conversion_failures = max(0, date_missing - original_missing)
    if date_missing:
        raise ValueError(
            f"completed order_date에 결측/변환 실패가 {date_missing}행 있습니다 (새 실패 {conversion_failures})."
        )

    completed["order_month"] = completed["order_date"].dt.to_period("M").astype("string")
    monthly_sales = (
        completed.groupby("order_month", as_index=False, dropna=False)
        .agg(total_sales=("line_total", "sum"), order_count=("order_id", "nunique"))
        .sort_values("order_month")
        .reset_index(drop=True)
    )
    monthly_sales["avg_order_value"] = (
        monthly_sales["total_sales"].div(monthly_sales["order_count"]).round(0)
    )
    source_total = float(completed["line_total"].sum())
    grouped_total = float(monthly_sales["total_sales"].sum())
    diff = _assert_total_equal("monthly", source_total, grouped_total)

    validation = pd.concat(
        [
            order_validation,
            pd.DataFrame(
                [
                    {"check_item": "order_date_missing_or_failure", "value": date_missing, "status": "PASS"},
                    {"check_item": "completed_source_total", "value": source_total, "status": "PASS"},
                    {"check_item": "monthly_grouped_total", "value": grouped_total, "status": "PASS"},
                    {"check_item": "monthly_total_difference", "value": diff, "status": "PASS"},
                ]
            ),
        ],
        ignore_index=True,
    )
    return monthly_sales, validation


# ---------------------------------------------------------------------------
# Static scan — screening only, never execution
# ---------------------------------------------------------------------------


def _qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _literal_string(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def scan_generated_code(code: str) -> pd.DataFrame:
    """Find obvious risky constructs without executing code.

    Limitations: aliases, dynamic dispatch, library side effects, compiled extensions,
    indirect network/file operations and obfuscated code may evade this scan.
    """
    findings: list[dict[str, object]] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return pd.DataFrame(
            [{"severity": "critical", "category": "syntax", "line": exc.lineno, "detail": f"문법 오류: {exc.msg}"}]
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in RISKY_IMPORT_ROOTS:
                    findings.append({"severity": "review", "category": "import", "line": getattr(node, "lineno", None), "detail": f"외부 작업 가능 모듈 import: {alias.name}"})
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in RISKY_IMPORT_ROOTS:
                findings.append({"severity": "review", "category": "import", "line": getattr(node, "lineno", None), "detail": f"외부 작업 가능 모듈 import: {node.module}"})

        if isinstance(node, ast.Call):
            call_name = _qualified_name(node.func)
            risk = RISKY_CALLS.get(call_name)
            if risk is None and call_name.endswith(DELETE_METHOD_SUFFIXES):
                risk = ("critical", "파일 또는 폴더 삭제")
            if risk is None and call_name.endswith(WRITE_METHOD_SUFFIXES):
                risk = ("review", "파일 생성·수정 가능")
            if risk is not None:
                severity, detail = risk
                findings.append({"severity": severity, "category": "operation", "line": getattr(node, "lineno", None), "detail": f"{detail}: {call_name}"})

            if call_name == "open":
                mode_node = node.args[1] if len(node.args) > 1 else next((kw.value for kw in node.keywords if kw.arg == "mode"), None)
                mode = _literal_string(mode_node) or "r"
                if any(flag in mode for flag in ("w", "a", "x", "+")):
                    findings.append({"severity": "high", "category": "file_write", "line": getattr(node, "lineno", None), "detail": f"파일 쓰기 모드: open(..., {mode!r})"})

            string_args = [value for value in (_literal_string(arg) for arg in node.args) if value]
            if any(value.startswith(("http://", "https://")) for value in string_args):
                findings.append({"severity": "high", "category": "network", "line": getattr(node, "lineno", None), "detail": f"외부 URL 사용: {call_name or 'call'}"})

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: Iterable[ast.AST]
            value_node: ast.AST | None
            if isinstance(node, ast.Assign):
                targets, value_node = node.targets, node.value
            else:
                targets, value_node = [node.target], node.value
            value = _literal_string(value_node)
            if value is None:
                continue
            target_names = {_qualified_name(target).lower() for target in targets}
            if any(token in name for name in target_names for token in ("api_key", "apikey", "password", "secret", "token", "credential")):
                findings.append({"severity": "critical", "category": "secret", "line": getattr(node, "lineno", None), "detail": "민감정보로 보이는 문자열이 코드에 직접 할당됨"})

    columns = ["severity", "category", "line", "detail"]
    result = pd.DataFrame(findings, columns=columns)
    if not result.empty:
        result = result.drop_duplicates().sort_values(["line", "severity", "category"], na_position="last").reset_index(drop=True)
    return result


# ---------------------------------------------------------------------------
# ML leakage review — problem-specific
# ---------------------------------------------------------------------------


def forbidden_features_for(problem: str) -> set[str]:
    normalized = problem.strip().lower()
    if normalized in {"regression", "회귀"}:
        return set(REGRESSION_FORBIDDEN_FEATURES)
    if normalized in {"classification", "분류"}:
        return set(CLASSIFICATION_FORBIDDEN_FEATURES)
    raise ValueError("problem은 'regression' 또는 'classification'이어야 합니다.")


def validate_feature_list(feature_columns: Iterable[str], *, problem: str) -> None:
    feature_list = list(feature_columns)
    if not feature_list:
        raise ValueError("입력값 목록이 비어 있습니다.")
    leaked = set(feature_list) & forbidden_features_for(problem)
    if leaked:
        raise ValueError(
            f"{problem} 입력값에 목표값 재료·정답·사후정보·식별자가 포함되어 있습니다: {sorted(leaked)}"
        )


def build_feature_audit(feature_columns: Iterable[str], *, problem: str) -> pd.DataFrame:
    features = list(feature_columns)
    forbidden = forbidden_features_for(problem)
    rows: list[dict[str, object]] = []
    for feature in features:
        status = "FAIL" if feature in forbidden else "REVIEW"
        note = "금지 feature" if feature in forbidden else "예측 시점 가용성을 사람이 확인"
        if problem.lower() in {"classification", "분류"} and feature in CLASSIFICATION_CONDITIONAL_FEATURES:
            status = "REVIEW"
            note = "주문 생성 시 상품 구성·수량·금액이 확정되어 있다는 교육용 가정 확인"
        rows.append({"problem": problem, "feature": feature, "status": status, "review_note": note})
    return pd.DataFrame(rows)


def build_leakage_review_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "problem": "regression",
                "prediction_time": "주문 상세 기반 target 재료를 아직 사용할 수 없는 시점",
                "target": "order_total",
                "forbidden_examples": ", ".join(sorted(REGRESSION_FORBIDDEN_FEATURES)),
                "split_rule": "날짜 순서 split + train 내부 TimeSeriesSplit selection + frozen final test",
            },
            {
                "problem": "classification",
                "prediction_time": "주문 생성 직후",
                "target": "completed=0, cancelled=1; refunded/other 제외",
                "forbidden_examples": ", ".join(sorted(CLASSIFICATION_FORBIDDEN_FEATURES)),
                "split_rule": "교육용 stratified train/validation/test; model/threshold는 validation, test는 frozen final",
            },
        ]
    )


# ---------------------------------------------------------------------------
# Human review templates
# ---------------------------------------------------------------------------


def build_sandbox_checklist() -> pd.DataFrame:
    items = [
        "운영 데이터가 아닌 복사한 소량 샘플을 사용하는가?",
        "API Key·클라우드 credential·DB 비밀번호가 없는 환경인가?",
        "불필요한 네트워크 접근을 차단했는가?",
        "최소 파일/폴더 권한으로 실행하는가?",
        "실행 전 Git 상태와 변경 대상 파일을 확인했는가?",
        "실행 후 생성·수정 파일을 비교할 수 있는가?",
    ]
    return pd.DataFrame({"check_item": items, "status": ["REVIEW"] * len(items), "evidence": [""] * len(items)})


def build_package_install_review_template() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "package": "",
                "requested_version": "",
                "purpose": "",
                "official_source_verified": "REVIEW",
                "name_typo_checked": "REVIEW",
                "python_compatibility_checked": "REVIEW",
                "install_script_reviewed": "REVIEW",
                "organization_policy_checked": "REVIEW",
                "decision": "DO_NOT_INSTALL_UNTIL_REVIEWED",
            }
        ]
    )


def build_human_revision_log_template() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "original_code_ref": "",
                "llm_suggestion_summary": "",
                "human_change": "",
                "reason": "",
                "reviewer": "",
                "reviewed_at": "",
                "execution_approved": False,
            }
        ]
    )


def build_code_review_checklist() -> pd.DataFrame:
    items = [
        ("데이터 구조", "실제 데이터셋과 컬럼명만 사용하는가?"),
        ("데이터 구조", "필수 컬럼·PK가 없으면 조용히 제외하지 않고 중단하는가?"),
        ("키/병합", "부모 키 고유성, validate, indicator, 전후 행 수, 미매칭을 확인하는가?"),
        ("집계", "completed 범위와 line_total 의미가 명확한가?"),
        ("집계", "원본 범위 총합과 category/monthly 집계 총합 차이가 허용오차 이내인가?"),
        ("전처리", "숫자·날짜 변환 실패를 기존 결측과 구분해 확인하는가?"),
        ("머신러닝", "문제별 prediction time과 forbidden feature를 구분했는가?"),
        ("평가", "회귀/분류에 맞는 split, baseline, selection data, final test 역할을 지켰는가?"),
        ("실행 안전", "eval/exec/외부 통신/OS 명령/파일 쓰기·삭제를 실행 전 검토했는가?"),
        ("실행 안전", "새 package의 공식 출처·이름·버전·설치 스크립트·조직 정책을 확인했는가?"),
        ("보안", "원본 행·PII·Secret·내부 URL·민감 경로를 LLM에 제공하지 않았는가?"),
        ("해석", "관찰·예측 패턴·원인 가설을 구분했는가?"),
        ("재현성", "원본 LLM 코드, 사람 수정, 환경, 검증 Evidence, 승인자를 기록했는가?"),
    ]
    return pd.DataFrame(
        {
            "category": [category for category, _ in items],
            "check_item": [item for _, item in items],
            "status": ["REVIEW"] * len(items),
            "evidence": [""] * len(items),
            "reviewer": [""] * len(items),
        }
    )


def build_error_fix_prompt_template() -> str:
    return """# 오류 수정 요청 — 최소·비식별 Context만 사용

분석 목적:
- [계산/예측하려는 내용을 한 문장으로 작성]

실제 필요한 데이터 구조:
- [데이터셋과 필요한 컬럼만 작성]
- 원본 고객/거래 행, 개인정보, API Key, 내부 URL, 사용자명, 절대 경로는 제공하지 않음

최소 재현 코드:
```python
[오류를 재현하는 최소 코드만]
```

민감정보를 제거한 오류 또는 검증 결과:
```text
[예외 유형, 필요한 메시지, 행 수, 미매칭 수, 총합 차이 등]
```

요청:
1. 실행 오류와 분석 논리 오류를 구분해서 설명해 주세요.
2. 실제 제공한 컬럼명만 사용하는 최소 수정안을 제안해 주세요.
3. merge validate, 전후 행 수, 미매칭, 총합 대조를 포함해 주세요.
4. 원인을 확인하지 못한 부분은 추측하지 말고 확인 방법을 제시해 주세요.
5. 파일 삭제·덮어쓰기, 외부 통신, OS 명령, package 설치 코드를 추가하지 마세요.
6. 수정 코드와 함께 사람이 다시 검증할 항목을 표로 제시해 주세요.
"""


def build_execution_gate(
    required_column_check: pd.DataFrame,
    primary_key_check: pd.DataFrame,
    relationship_check: pd.DataFrame,
    category_validation: pd.DataFrame,
    monthly_validation: pd.DataFrame,
    static_scan: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        {
            "gate": "schema_and_keys",
            "status": "PASS"
            if required_column_check["status"].eq("PASS").all()
            and primary_key_check["status"].eq("PASS").all()
            and relationship_check["status"].eq("PASS").all()
            else "FAIL",
            "meaning": "필수 구조·PK·관계",
        },
        {
            "gate": "aggregate_validation",
            "status": "PASS"
            if not category_validation["status"].eq("FAIL").any()
            and not monthly_validation["status"].eq("FAIL").any()
            else "FAIL",
            "meaning": "completed 범위·병합·총합",
        },
        {
            "gate": "static_scan",
            "status": "REVIEW" if static_scan.empty else "BLOCKED",
            "meaning": "0건이어도 사람 검토 필요; 탐지 항목이 있으면 실행 금지",
        },
        {
            "gate": "human_approval",
            "status": "REVIEW",
            "meaning": "샌드박스·패키지·파일 변경·환경을 사람이 승인해야 함",
        },
    ]
    gate = pd.DataFrame(rows)
    decision = "DO_NOT_EXECUTE" if gate["status"].isin(["FAIL", "BLOCKED"]).any() else "HUMAN_REVIEW_REQUIRED"
    gate.loc[len(gate)] = {"gate": "execution_decision", "status": decision, "meaning": "자동 승인하지 않음"}
    return gate


def build_validation_summary(
    *,
    inventory: pd.DataFrame,
    required_column_check: pd.DataFrame,
    primary_key_check: pd.DataFrame,
    relationship_check: pd.DataFrame,
    category_validation: pd.DataFrame,
    monthly_validation: pd.DataFrame,
    leakage_review: pd.DataFrame,
    static_scan: pd.DataFrame,
    execution_gate: pd.DataFrame,
) -> str:
    static_text = "탐지 항목 없음 — 안전 보증 아님" if static_scan.empty else static_scan.to_string(index=False)
    return f"""# Chapter 12 LLM 분석 코드 검증 요약

## 핵심 원칙

- 생성 코드는 검토되지 않은 초안입니다.
- 코드가 실행됨 ≠ 분석이 올바름.
- 정적 스캔 0건 ≠ 코드가 안전함.
- 자동 검증 PASS ≠ 실행 승인. 사람 승인과 제한된 실행 환경이 별도로 필요합니다.

## 1. 데이터셋 인벤토리
```text
{inventory.to_string(index=False)}
```

## 2. 필수 컬럼
```text
{required_column_check.to_string(index=False)}
```

## 3. PK
```text
{primary_key_check.to_string(index=False)}
```

## 4. 관계
```text
{relationship_check.to_string(index=False)}
```

## 5. 카테고리 집계 검증
```text
{category_validation.to_string(index=False)}
```

## 6. 월별 집계 검증
```text
{monthly_validation.to_string(index=False)}
```

## 7. 문제별 ML 누수 계약
```text
{leakage_review.to_string(index=False)}
```

## 8. 정적 스캔
```text
{static_text}
```

## 9. 실행 Gate
```text
{execution_gate.to_string(index=False)}
```

## 10. 해석 범위
- 금액 집계는 `order_status == "completed"`인 주문 상세만 사용합니다.
- `line_total = quantity × unit_price`이며 여기서는 완료 주문 상세 금액입니다.
- 할인·배송비·세금·부분 환불을 모두 반영한 회계상 순매출이라고 단정하지 않습니다.
- 모델 결과와 동시 변화를 원인으로 단정하지 않습니다.
"""


# ---------------------------------------------------------------------------
# Saving and chapter pipeline
# ---------------------------------------------------------------------------


def save_validation_outputs(
    outputs: dict[str, pd.DataFrame | str],
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    root = Path(report_dir)
    root.mkdir(parents=True, exist_ok=True)
    file_map = {
        "inventory": "ch12_dataset_inventory.csv",
        "required_column_check": "ch12_required_column_check.csv",
        "primary_key_check": "ch12_primary_key_check.csv",
        "relationship_check": "ch12_relationship_key_check.csv",
        "category_sales": "ch12_category_sales_validated.csv",
        "category_validation": "ch12_category_sales_validation.csv",
        "monthly_sales": "ch12_monthly_sales_validated.csv",
        "monthly_validation": "ch12_monthly_sales_validation.csv",
        "leakage_review": "ch12_ml_leakage_review.csv",
        "static_scan": "ch12_generated_code_static_scan.csv",
        "execution_gate": "ch12_execution_gate.csv",
        "sandbox_checklist": "ch12_sandbox_execution_checklist.csv",
        "package_review": "ch12_package_install_review.csv",
        "human_revision_log": "ch12_human_revision_log.csv",
        "code_review_checklist": "ch12_llm_code_review_checklist.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in file_map.items():
        value = outputs[key]
        if not isinstance(value, pd.DataFrame):
            raise TypeError(f"{key} 결과는 DataFrame이어야 합니다.")
        path = root / filename
        value.to_csv(path, index=False, encoding="utf-8-sig")
        paths[key] = path

    prompt_path = root / "ch12_error_fix_prompt_template.md"
    prompt_path.write_text(str(outputs["error_fix_prompt"]), encoding="utf-8")
    paths["error_fix_prompt"] = prompt_path

    summary_path = root / "ch12_code_validation_summary.md"
    summary_path.write_text(str(outputs["validation_summary"]), encoding="utf-8")
    paths["validation_summary"] = summary_path
    return paths


def run_llm_code_validation(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    code_for_static_scan: str = DEFAULT_STATIC_SCAN_EXAMPLE,
) -> dict[str, object]:
    """Generate Chapter 12 evidence without executing the supplied generated code."""
    datasets = load_validation_data(processed_dir)
    inventory = build_dataset_inventory(datasets)
    required_column_check = validate_required_columns(datasets)
    primary_key_check = validate_primary_keys(datasets)
    relationship_check = validate_relationship_keys(datasets)
    assert_validation_ready(required_column_check, primary_key_check, relationship_check)

    category_sales, category_validation = safe_category_sales(
        datasets["order_items"], datasets["products"], datasets["orders"]
    )
    monthly_sales, monthly_validation = safe_monthly_sales(
        datasets["order_items"], datasets["orders"]
    )

    leakage_review = build_leakage_review_table()
    static_scan = scan_generated_code(code_for_static_scan)
    sandbox_checklist = build_sandbox_checklist()
    package_review = build_package_install_review_template()
    human_revision_log = build_human_revision_log_template()
    code_review_checklist = build_code_review_checklist()
    error_fix_prompt = build_error_fix_prompt_template()
    execution_gate = build_execution_gate(
        required_column_check,
        primary_key_check,
        relationship_check,
        category_validation,
        monthly_validation,
        static_scan,
    )
    validation_summary = build_validation_summary(
        inventory=inventory,
        required_column_check=required_column_check,
        primary_key_check=primary_key_check,
        relationship_check=relationship_check,
        category_validation=category_validation,
        monthly_validation=monthly_validation,
        leakage_review=leakage_review,
        static_scan=static_scan,
        execution_gate=execution_gate,
    )

    outputs: dict[str, pd.DataFrame | str] = {
        "inventory": inventory,
        "required_column_check": required_column_check,
        "primary_key_check": primary_key_check,
        "relationship_check": relationship_check,
        "category_sales": category_sales,
        "category_validation": category_validation,
        "monthly_sales": monthly_sales,
        "monthly_validation": monthly_validation,
        "leakage_review": leakage_review,
        "static_scan": static_scan,
        "execution_gate": execution_gate,
        "sandbox_checklist": sandbox_checklist,
        "package_review": package_review,
        "human_revision_log": human_revision_log,
        "code_review_checklist": code_review_checklist,
        "error_fix_prompt": error_fix_prompt,
        "validation_summary": validation_summary,
    }
    output_paths = save_validation_outputs(outputs, report_dir=report_dir)
    return {"datasets": datasets, "outputs": outputs, "output_paths": output_paths}
