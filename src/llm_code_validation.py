"""Chapter 12 utilities for validating LLM-generated analysis code.

The workflow treats generated code as an untrusted draft. It checks the real
data schema and key relationships before execution, applies explicit business
rules to aggregate completed orders, scans example code for risky operations,
and records the validation evidence in reusable report files.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

import pandas as pd


COMPLETED_STATUS = "completed"

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

FORBIDDEN_MODEL_FEATURES = {
    "order_total",
    "line_total",
    "quantity",
    "unit_price",
    "item_count",
    "total_quantity",
    "avg_unit_price",
    "order_status",
    "is_cancelled",
    "order_id",
    "customer_id",
}

RISKY_IMPORT_ROOTS = {
    "ftplib",
    "http",
    "os",
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
    "subprocess.run": ("critical", "외부 프로세스 실행"),
    "subprocess.Popen": ("critical", "외부 프로세스 실행"),
    "subprocess.call": ("critical", "외부 프로세스 실행"),
    "subprocess.check_call": ("critical", "외부 프로세스 실행"),
    "subprocess.check_output": ("critical", "외부 프로세스 실행"),
    "shutil.rmtree": ("critical", "폴더 재귀 삭제"),
    "Path.unlink": ("high", "파일 삭제"),
    "Path.rmdir": ("high", "폴더 삭제"),
    "requests.get": ("high", "외부 네트워크 요청"),
    "requests.post": ("high", "외부 네트워크 요청"),
    "requests.put": ("high", "외부 네트워크 요청"),
    "requests.delete": ("high", "외부 네트워크 요청"),
    "urllib.request.urlopen": ("high", "외부 네트워크 요청"),
    "socket.socket": ("high", "네트워크 소켓 생성"),
}

DEFAULT_STATIC_SCAN_EXAMPLE = """
import requests

response = requests.get("https://example.com/data.csv")
open("download.csv", "wb").write(response.content)
"""


def _required_file_map(processed_dir: str | Path) -> dict[str, Path]:
    input_dir = Path(processed_dir)
    return {
        "customers": input_dir / "customers_clean.csv",
        "products": input_dir / "products_clean.csv",
        "orders": input_dir / "orders_clean.csv",
        "order_items": input_dir / "order_items_clean.csv",
    }


def load_validation_data(
    processed_dir: str | Path = "data/processed",
) -> dict[str, pd.DataFrame]:
    """Load the four processed data files required for Chapter 12."""
    file_map = _required_file_map(processed_dir)
    missing_files = [path for path in file_map.values() if not path.exists()]

    if missing_files:
        missing_text = "\n".join(f"- {path}" for path in missing_files)
        raise FileNotFoundError(
            "전처리 파일이 없습니다. 먼저 프로젝트 루트에서 "
            "`python scripts/preprocess_data.py`를 실행하세요.\n"
            f"{missing_text}"
        )

    return {
        name: pd.read_csv(path)
        for name, path in file_map.items()
    }


def build_dataset_inventory(
    datasets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Summarize the observed schema and basic quality of each dataset."""
    rows: list[dict[str, object]] = []

    for name in REQUIRED_COLUMNS:
        df = datasets.get(name)
        if df is None:
            rows.append(
                {
                    "dataset": name,
                    "exists": False,
                    "rows": None,
                    "columns": None,
                    "column_list": "",
                    "missing_values": None,
                    "duplicated_rows": None,
                }
            )
            continue

        rows.append(
            {
                "dataset": name,
                "exists": True,
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
                "column_list": ", ".join(map(str, df.columns)),
                "missing_values": int(df.isna().sum().sum()),
                "duplicated_rows": int(df.duplicated().sum()),
            }
        )

    return pd.DataFrame(rows)


def validate_required_columns(
    datasets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Check whether every required dataset and column exists."""
    rows: list[dict[str, object]] = []

    for dataset_name, required_columns in REQUIRED_COLUMNS.items():
        df = datasets.get(dataset_name)

        for column in sorted(required_columns):
            rows.append(
                {
                    "dataset": dataset_name,
                    "column": column,
                    "dataset_exists": df is not None,
                    "exists": bool(
                        df is not None and column in df.columns
                    ),
                }
            )

    return pd.DataFrame(rows)


def validate_primary_keys(
    datasets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Check missing and duplicated values in identifiers expected to be unique."""
    rows: list[dict[str, object]] = []

    for dataset_name, key in PRIMARY_KEYS.items():
        df = datasets.get(dataset_name)
        key_exists = bool(df is not None and key in df.columns)

        missing_count = None
        duplicated_count = None
        if key_exists and df is not None:
            missing_count = int(df[key].isna().sum())
            duplicated_count = int(
                df.loc[df[key].notna(), key].duplicated().sum()
            )

        rows.append(
            {
                "dataset": dataset_name,
                "primary_key": key,
                "key_exists": key_exists,
                "missing_key_count": missing_count,
                "duplicated_key_count": duplicated_count,
            }
        )

    return pd.DataFrame(rows)


def validate_relationship_keys(
    datasets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Check foreign-key coverage and parent-key uniqueness."""
    rows: list[dict[str, object]] = []

    for check in RELATIONSHIP_CHECKS:
        left_name = check["left_dataset"]
        right_name = check["right_dataset"]
        key = check["key"]

        left_df = datasets.get(left_name)
        right_df = datasets.get(right_name)
        left_has_key = bool(
            left_df is not None and key in left_df.columns
        )
        right_has_key = bool(
            right_df is not None and key in right_df.columns
        )

        missing_left_key_count = None
        invalid_reference_count = None
        duplicated_parent_key_count = None

        if left_has_key and left_df is not None:
            missing_left_key_count = int(left_df[key].isna().sum())

        if right_has_key and right_df is not None:
            duplicated_parent_key_count = int(
                right_df.loc[right_df[key].notna(), key]
                .duplicated()
                .sum()
            )

        if (
            left_has_key
            and right_has_key
            and left_df is not None
            and right_df is not None
        ):
            left_non_null = left_df.loc[left_df[key].notna(), key]
            parent_keys = set(
                right_df.loc[right_df[key].notna(), key]
            )
            invalid_reference_count = int(
                (~left_non_null.isin(parent_keys)).sum()
            )

        rows.append(
            {
                "purpose": check["purpose"],
                "left_dataset": left_name,
                "right_dataset": right_name,
                "key": key,
                "left_has_key": left_has_key,
                "right_has_key": right_has_key,
                "missing_left_key_count": missing_left_key_count,
                "duplicated_parent_key_count": duplicated_parent_key_count,
                "invalid_reference_count": invalid_reference_count,
            }
        )

    return pd.DataFrame(rows)


def assert_validation_ready(
    required_column_check: pd.DataFrame,
    primary_key_check: pd.DataFrame,
    relationship_check: pd.DataFrame,
) -> None:
    """Stop the workflow when schema or key checks contain blocking errors."""
    problems: list[str] = []

    missing_columns = required_column_check.loc[
        ~required_column_check["exists"],
        ["dataset", "column"],
    ]
    for row in missing_columns.itertuples(index=False):
        problems.append(f"{row.dataset}.{row.column} 컬럼 없음")

    bad_primary_keys = primary_key_check.loc[
        primary_key_check["key_exists"]
        & (
            primary_key_check["missing_key_count"].fillna(0).gt(0)
            | primary_key_check["duplicated_key_count"].fillna(0).gt(0)
        )
    ]
    for row in bad_primary_keys.itertuples(index=False):
        problems.append(
            f"{row.dataset}.{row.primary_key}: "
            f"결측 {int(row.missing_key_count or 0)}, "
            f"중복 {int(row.duplicated_key_count or 0)}"
        )

    bad_relationships = relationship_check.loc[
        (~relationship_check["left_has_key"])
        | (~relationship_check["right_has_key"])
        | relationship_check[
            "duplicated_parent_key_count"
        ].fillna(0).gt(0)
        | relationship_check[
            "missing_left_key_count"
        ].fillna(0).gt(0)
        | relationship_check[
            "invalid_reference_count"
        ].fillna(0).gt(0)
    ]
    for row in bad_relationships.itertuples(index=False):
        problems.append(
            f"{row.left_dataset}.{row.key} → "
            f"{row.right_dataset}.{row.key} 관계 점검 실패"
        )

    if problems:
        details = "\n".join(f"- {problem}" for problem in problems)
        raise ValueError(
            "분석 코드를 실행하기 전에 해결해야 할 데이터 구조 "
            f"문제가 있습니다.\n{details}"
        )


def ensure_line_total(
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """Return numeric quantity, unit_price, and line_total columns."""
    result = order_items.copy()
    required = {"quantity", "unit_price"}
    missing = required - set(result.columns)

    if missing:
        raise KeyError(
            "order_items에 필요한 컬럼이 없습니다: "
            f"{sorted(missing)}"
        )

    result["quantity"] = pd.to_numeric(
        result["quantity"],
        errors="coerce",
    )
    result["unit_price"] = pd.to_numeric(
        result["unit_price"],
        errors="coerce",
    )

    if "line_total" in result.columns:
        result["line_total"] = pd.to_numeric(
            result["line_total"],
            errors="coerce",
        )
    else:
        result["line_total"] = (
            result["quantity"] * result["unit_price"]
        )

    invalid_mask = result[
        ["quantity", "unit_price", "line_total"]
    ].isna().any(axis=1)

    if invalid_mask.any():
        raise ValueError(
            "quantity, unit_price 또는 line_total의 숫자 변환에 "
            f"실패한 행이 {int(invalid_mask.sum())}개 있습니다."
        )

    expected_total = (
        result["quantity"] * result["unit_price"]
    )
    mismatch_mask = ~result["line_total"].round(6).eq(
        expected_total.round(6)
    )

    if mismatch_mask.any():
        raise ValueError(
            "line_total과 quantity × unit_price가 다른 행이 "
            f"{int(mismatch_mask.sum())}개 있습니다."
        )

    return result


def _prepare_completed_order_items(
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attach order metadata and keep completed orders only."""
    items = ensure_line_total(order_items)

    required_order_columns = {
        "order_id",
        "order_date",
        "order_status",
    }
    missing = required_order_columns - set(orders.columns)
    if missing:
        raise KeyError(
            "orders에 필요한 컬럼이 없습니다: "
            f"{sorted(missing)}"
        )

    order_meta = orders[
        ["order_id", "order_date", "order_status"]
    ].copy()

    before_rows = len(items)
    merged = items.merge(
        order_meta,
        on="order_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    unlinked_rows = int(merged["_merge"].ne("both").sum())
    merged = merged.drop(columns="_merge")
    status_normalized = (
        merged["order_status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    completed_mask = status_normalized.eq(COMPLETED_STATUS)
    completed = merged.loc[completed_mask].copy()

    validation = pd.DataFrame(
        {
            "check_item": [
                "원본 주문 상세 행 수",
                "주문 병합 후 행 수",
                "병합 전후 행 수 동일 여부",
                "orders에 연결되지 않은 행 수",
                "완료 주문 상세 행 수",
                "집계 포함 주문 상태",
            ],
            "value": [
                before_rows,
                len(merged),
                before_rows == len(merged),
                unlinked_rows,
                len(completed),
                COMPLETED_STATUS,
            ],
        }
    )

    if unlinked_rows:
        raise ValueError(
            "orders에 연결되지 않는 주문 상세 행이 "
            f"{unlinked_rows}개 있습니다."
        )

    return completed, validation


def safe_category_sales(
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate completed-order amount by product category with checks."""
    completed_items, order_validation = (
        _prepare_completed_order_items(
            order_items=order_items,
            orders=orders,
        )
    )

    required_product_columns = {
        "product_id",
        "category",
    }
    missing = required_product_columns - set(products.columns)
    if missing:
        raise KeyError(
            "products에 필요한 컬럼이 없습니다: "
            f"{sorted(missing)}"
        )

    sales_items = completed_items.merge(
        products[["product_id", "category"]],
        on="product_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    missing_product_rows = int(
        sales_items["_merge"].ne("both").sum()
    )
    missing_category_rows = int(
        sales_items["category"].isna().sum()
    )
    sales_items = sales_items.drop(columns="_merge")

    if missing_product_rows or missing_category_rows:
        raise ValueError(
            "상품 또는 카테고리에 연결되지 않는 완료 주문 상세가 "
            f"{max(missing_product_rows, missing_category_rows)}개 있습니다."
        )

    category_sales = (
        sales_items.groupby(
            "category",
            as_index=False,
            dropna=False,
        )
        .agg(
            total_quantity=("quantity", "sum"),
            total_sales=("line_total", "sum"),
        )
        .sort_values("total_sales", ascending=False)
        .reset_index(drop=True)
    )

    total_amount = float(category_sales["total_sales"].sum())
    category_sales["sales_ratio"] = (
        category_sales["total_sales"]
        .div(total_amount)
        .mul(100)
        .round(2)
        if total_amount
        else 0.0
    )

    validation = pd.concat(
        [
            order_validation,
            pd.DataFrame(
                {
                    "check_item": [
                        "상품 병합 후 행 수",
                        "products에 연결되지 않은 행 수",
                        "category 결측치 수",
                        "완료 주문 상세 금액 합계",
                        "카테고리 집계 금액 합계",
                        "총합 차이",
                    ],
                    "value": [
                        len(sales_items),
                        missing_product_rows,
                        missing_category_rows,
                        float(sales_items["line_total"].sum()),
                        total_amount,
                        float(
                            sales_items["line_total"].sum()
                            - total_amount
                        ),
                    ],
                }
            ),
        ],
        ignore_index=True,
    )

    return category_sales, validation


def safe_monthly_sales(
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate completed-order amount by month with checks."""
    completed_items, order_validation = (
        _prepare_completed_order_items(
            order_items=order_items,
            orders=orders,
        )
    )

    completed_items["order_date"] = pd.to_datetime(
        completed_items["order_date"],
        errors="coerce",
    )
    date_failures = int(
        completed_items["order_date"].isna().sum()
    )
    if date_failures:
        raise ValueError(
            "완료 주문의 order_date 변환에 실패한 행이 "
            f"{date_failures}개 있습니다."
        )

    completed_items["order_month"] = (
        completed_items["order_date"]
        .dt.to_period("M")
        .astype("string")
    )

    monthly_sales = (
        completed_items.groupby(
            "order_month",
            as_index=False,
            dropna=False,
        )
        .agg(
            total_sales=("line_total", "sum"),
            order_count=("order_id", "nunique"),
        )
        .sort_values("order_month")
        .reset_index(drop=True)
    )
    monthly_sales["avg_order_value"] = (
        monthly_sales["total_sales"]
        .div(monthly_sales["order_count"])
        .round(0)
    )

    source_total = float(
        completed_items["line_total"].sum()
    )
    grouped_total = float(
        monthly_sales["total_sales"].sum()
    )

    validation = pd.concat(
        [
            order_validation,
            pd.DataFrame(
                {
                    "check_item": [
                        "order_date 변환 실패 수",
                        "완료 주문 상세 금액 합계",
                        "월별 집계 금액 합계",
                        "총합 차이",
                    ],
                    "value": [
                        date_failures,
                        source_total,
                        grouped_total,
                        source_total - grouped_total,
                    ],
                }
            ),
        ],
        ignore_index=True,
    )

    return monthly_sales, validation


def _qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def scan_generated_code(code: str) -> pd.DataFrame:
    """Statically flag risky constructs without executing the supplied code.

    This is a screening step, not a proof that the code is safe.
    """
    findings: list[dict[str, object]] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return pd.DataFrame(
            [
                {
                    "severity": "critical",
                    "category": "syntax",
                    "line": exc.lineno,
                    "detail": f"문법 오류: {exc.msg}",
                }
            ]
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in RISKY_IMPORT_ROOTS:
                    findings.append(
                        {
                            "severity": "review",
                            "category": "import",
                            "line": getattr(node, "lineno", None),
                            "detail": (
                                f"외부 작업 가능 모듈 import: "
                                f"{alias.name}"
                            ),
                        }
                    )

        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in RISKY_IMPORT_ROOTS:
                findings.append(
                    {
                        "severity": "review",
                        "category": "import",
                        "line": getattr(node, "lineno", None),
                        "detail": (
                            f"외부 작업 가능 모듈 import: "
                            f"{node.module}"
                        ),
                    }
                )

        if isinstance(node, ast.Call):
            call_name = _qualified_name(node.func)
            risk = RISKY_CALLS.get(call_name)

            if risk is None and call_name.endswith(
                (".unlink", ".rmdir")
            ):
                risk = ("high", "파일 또는 폴더 삭제")

            if risk is not None:
                severity, detail = risk
                findings.append(
                    {
                        "severity": severity,
                        "category": "operation",
                        "line": getattr(node, "lineno", None),
                        "detail": f"{detail}: {call_name}",
                    }
                )

            if call_name == "open":
                mode_node = (
                    node.args[1]
                    if len(node.args) > 1
                    else next(
                        (
                            keyword.value
                            for keyword in node.keywords
                            if keyword.arg == "mode"
                        ),
                        None,
                    )
                )
                mode = _literal_string(mode_node) or "r"
                if any(flag in mode for flag in ("w", "a", "x", "+")):
                    findings.append(
                        {
                            "severity": "high",
                            "category": "file_write",
                            "line": getattr(node, "lineno", None),
                            "detail": (
                                f"파일 쓰기 모드 사용: open(..., "
                                f"{mode!r})"
                            ),
                        }
                    )

            string_args = [
                value
                for value in (
                    _literal_string(argument)
                    for argument in node.args
                )
                if value is not None
            ]
            if any(
                value.startswith(("http://", "https://"))
                for value in string_args
            ):
                findings.append(
                    {
                        "severity": "high",
                        "category": "network",
                        "line": getattr(node, "lineno", None),
                        "detail": (
                            f"외부 URL 사용: {call_name or '함수 호출'}"
                        ),
                    }
                )

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: Iterable[ast.AST]
            value_node: ast.AST | None
            if isinstance(node, ast.Assign):
                targets = node.targets
                value_node = node.value
            else:
                targets = [node.target]
                value_node = node.value

            value = _literal_string(value_node)
            if value is None:
                continue

            target_names = {
                _qualified_name(target).lower()
                for target in targets
            }
            if any(
                token in target_name
                for target_name in target_names
                for token in (
                    "api_key",
                    "apikey",
                    "password",
                    "secret",
                    "token",
                )
            ):
                findings.append(
                    {
                        "severity": "critical",
                        "category": "secret",
                        "line": getattr(node, "lineno", None),
                        "detail": (
                            "민감정보로 보이는 문자열이 코드에 "
                            "직접 할당됨"
                        ),
                    }
                )

    columns = ["severity", "category", "line", "detail"]
    return pd.DataFrame(findings, columns=columns)


def build_leakage_review_table() -> pd.DataFrame:
    """Summarize common leakage risks using prediction-time reasoning."""
    return pd.DataFrame(
        {
            "case": [
                "주문 취소 분류",
                "주문 금액 회귀",
                "고객 미래 구매 금액 예측",
                "상품 미래 판매량 예측",
            ],
            "target": [
                "is_cancelled",
                "order_total",
                "future_customer_amount",
                "future_quantity",
            ],
            "dangerous_feature": [
                "order_status 또는 취소 확정 이후 정보",
                "line_total, quantity, unit_price 및 같은 주문 집계값",
                "예측 기간의 구매 금액 또는 미래 집계값",
                "예측 기간의 판매량 또는 사후 집계값",
            ],
            "safe_direction": [
                "예측 시점 이전에 확정된 주문·고객 정보만 사용",
                "주문 상세가 확인되기 전 이용 가능한 정보만 사용",
                "기준일 이전 행동 지표만 사용",
                "예측 시작일 이전 상품·판매 이력만 사용",
            ],
        }
    )


def validate_feature_list(
    feature_columns: Iterable[str],
) -> None:
    """Reject missing or leakage-prone feature lists instead of silently shrinking them."""
    feature_list = list(feature_columns)
    if not feature_list:
        raise ValueError("입력값 목록이 비어 있습니다.")

    leaked = set(feature_list) & FORBIDDEN_MODEL_FEATURES
    if leaked:
        raise ValueError(
            "입력값에 목표값·식별자·예측 이후 정보가 "
            f"포함되어 있습니다: {sorted(leaked)}"
        )


def build_code_review_checklist() -> pd.DataFrame:
    """Return a reusable review checklist for generated analysis code."""
    items = [
        ("데이터 구조", "실제 데이터셋과 컬럼명만 사용했는가?"),
        ("데이터 구조", "필수 컬럼이 없을 때 즉시 중단하는가?"),
        ("키", "고유 키의 결측치와 중복을 확인했는가?"),
        ("병합", "병합 키와 관계를 확인하고 validate 옵션을 사용했는가?"),
        ("병합", "병합 전후 행 수와 미연결 행을 확인했는가?"),
        ("집계", "포함한 주문 상태와 제외 기준을 명시했는가?"),
        ("집계", "원본 범위와 집계 결과의 총합을 대조했는가?"),
        ("전처리", "숫자·날짜 변환 실패를 확인했는가?"),
        ("머신러닝", "예측 시점과 목표값을 명확히 정의했는가?"),
        ("머신러닝", "목표값 계산 재료와 사후 정보를 제외했는가?"),
        ("평가", "업무 문제에 맞는 분할과 지표를 사용했는가?"),
        ("실행 안전", "외부 통신·파일 변경·명령 실행을 검토했는가?"),
        ("실행 안전", "새 패키지 설치가 필요한 이유와 출처를 확인했는가?"),
        ("보안", "개인정보·API 키·내부 경로를 노출하지 않는가?"),
        ("해석", "관찰 결과와 원인 가설을 구분했는가?"),
        ("재현성", "프롬프트·수정 내용·실행 환경을 기록했는가?"),
    ]

    return pd.DataFrame(
        {
            "category": [category for category, _ in items],
            "check_item": [item for _, item in items],
            "status": ["미확인"] * len(items),
            "memo": [""] * len(items),
        }
    )


def build_error_fix_prompt_template() -> str:
    """Return a prompt template that avoids sharing raw sensitive data."""
    return """다음 분석 코드에서 오류 또는 검증 실패가 발생했습니다.

분석 목적:
- [계산하거나 예측하려는 내용을 작성]

실제 데이터 구조:
- [데이터셋별 필요한 컬럼만 작성]
- 원본 행, 개인정보, API 키, 내부 경로는 제공하지 않음

실행한 코드:
```python
[검토가 필요한 최소 코드만 붙여넣기]
```

오류 또는 검증 결과:
```text
[오류 메시지와 행 수·결측치·총합 차이 등 필요한 결과]
```

요청:
1. 오류 원인과 논리 문제를 구분해 설명해 주세요.
2. 실제 컬럼명만 사용한 최소 수정안을 제안해 주세요.
3. 병합 validate, 행 수, 미연결 행, 총합 대조 코드를 포함해 주세요.
4. 파일 삭제, 외부 통신, 명령 실행, 패키지 설치 코드는 추가하지 마세요.
5. 데이터에 없는 사실이나 원인을 추측하지 마세요.
"""


def build_validation_summary(
    inventory: pd.DataFrame,
    required_column_check: pd.DataFrame,
    primary_key_check: pd.DataFrame,
    relationship_check: pd.DataFrame,
    category_validation: pd.DataFrame,
    monthly_validation: pd.DataFrame,
    leakage_review: pd.DataFrame,
    static_scan: pd.DataFrame,
) -> str:
    """Build a Markdown audit summary from validation evidence."""
    static_text = (
        "탐지된 항목 없음"
        if static_scan.empty
        else static_scan.to_string(index=False)
    )

    return f"""# Chapter 12 LLM 분석 코드 검증 요약

## 1. 검증 목적

LLM이 제안한 분석 코드를 실행하기 전에 데이터 구조와 위험한 동작을 확인하고,
실행 후에는 병합 행 수, 미연결 데이터, 집계 범위와 총합을 검증했습니다.

## 2. 데이터셋 인벤토리

```text
{inventory.to_string(index=False)}
```

## 3. 필수 컬럼 점검

```text
{required_column_check.to_string(index=False)}
```

## 4. 고유 키 점검

```text
{primary_key_check.to_string(index=False)}
```

## 5. 키 관계 점검

```text
{relationship_check.to_string(index=False)}
```

## 6. 완료 주문 기준 카테고리 집계 검증

```text
{category_validation.to_string(index=False)}
```

## 7. 완료 주문 기준 월별 집계 검증

```text
{monthly_validation.to_string(index=False)}
```

## 8. 머신러닝 데이터 누수 검토

```text
{leakage_review.to_string(index=False)}
```

## 9. 생성 코드 정적 점검 예시

```text
{static_text}
```

정적 점검은 위험 후보를 빠르게 찾는 보조 절차이며, 코드가 안전하다는 보증이 아닙니다.
승인되지 않은 외부 통신, 파일 변경, 명령 실행은 격리된 환경에서도 실행하지 않습니다.

## 10. 집계 기준과 해석 주의사항

- 금액 집계에는 `order_status == "completed"`인 주문만 포함했습니다.
- `line_total` 합계는 완료 주문 상세 금액이며 회계상 순매출과 같다고 단정하지 않습니다.
- 할인, 배송비, 세금, 부분 환불 정보가 없다면 계산 가능한 범위만 설명합니다.
- LLM이 제안한 원인은 데이터로 별도 확인하기 전까지 가설로 표시합니다.
"""


def save_validation_outputs(
    outputs: dict[str, pd.DataFrame | str],
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """Save Chapter 12 validation evidence and reusable templates."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

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
        "code_review_checklist": "ch12_llm_code_review_checklist.csv",
    }

    paths: dict[str, Path] = {}
    for key, filename in file_map.items():
        value = outputs[key]
        if not isinstance(value, pd.DataFrame):
            raise TypeError(f"{key} 결과는 DataFrame이어야 합니다.")
        path = output_dir / filename
        value.to_csv(
            path,
            index=False,
            encoding="utf-8-sig",
        )
        paths[key] = path

    prompt_path = (
        output_dir / "ch12_error_fix_prompt_template.md"
    )
    prompt_path.write_text(
        str(outputs["error_fix_prompt"]),
        encoding="utf-8",
    )
    paths["error_fix_prompt"] = prompt_path

    summary_path = (
        output_dir / "ch12_code_validation_summary.md"
    )
    summary_path.write_text(
        str(outputs["validation_summary"]),
        encoding="utf-8",
    )
    paths["validation_summary"] = summary_path

    return paths


def run_llm_code_validation(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    code_for_static_scan: str = DEFAULT_STATIC_SCAN_EXAMPLE,
) -> dict[str, object]:
    """Run the complete Chapter 12 validation workflow."""
    datasets = load_validation_data(processed_dir)

    inventory = build_dataset_inventory(datasets)
    required_column_check = validate_required_columns(datasets)
    primary_key_check = validate_primary_keys(datasets)
    relationship_check = validate_relationship_keys(datasets)

    assert_validation_ready(
        required_column_check=required_column_check,
        primary_key_check=primary_key_check,
        relationship_check=relationship_check,
    )

    category_sales, category_validation = safe_category_sales(
        order_items=datasets["order_items"],
        products=datasets["products"],
        orders=datasets["orders"],
    )
    monthly_sales, monthly_validation = safe_monthly_sales(
        order_items=datasets["order_items"],
        orders=datasets["orders"],
    )

    leakage_review = build_leakage_review_table()
    static_scan = scan_generated_code(code_for_static_scan)
    code_review_checklist = build_code_review_checklist()
    error_fix_prompt = build_error_fix_prompt_template()
    validation_summary = build_validation_summary(
        inventory=inventory,
        required_column_check=required_column_check,
        primary_key_check=primary_key_check,
        relationship_check=relationship_check,
        category_validation=category_validation,
        monthly_validation=monthly_validation,
        leakage_review=leakage_review,
        static_scan=static_scan,
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
        "code_review_checklist": code_review_checklist,
        "error_fix_prompt": error_fix_prompt,
        "validation_summary": validation_summary,
    }
    output_paths = save_validation_outputs(
        outputs=outputs,
        report_dir=report_dir,
    )

    return {
        "datasets": datasets,
        "outputs": outputs,
        "output_paths": output_paths,
    }
