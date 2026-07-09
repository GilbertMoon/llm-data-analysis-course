"""Chapter 14 반복 분석 자동화 파이프라인 공통 함수 모음.

온라인 쇼핑몰 분석 흐름을 입력 확인, 전처리, 분석, 시각화, 보고서 생성, 산출물 검증 단계로
나누어 실행할 수 있도록 구성했습니다. Docker Compose 기반 Airflow DAG와 일반 Python 스크립트에서
함께 사용합니다.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


RAW_FILENAMES = ["customers.csv", "products.csv", "orders.csv", "order_items.csv"]
PROCESSED_FILENAMES = [
    "customers_clean.csv",
    "products_clean.csv",
    "orders_clean.csv",
    "order_items_clean.csv",
]
CH14_REPORT_FILES = [
    "ch14_daily_sales.csv",
    "ch14_category_sales.csv",
    "ch14_pipeline_task_summary.csv",
    "ch14_airflow_report.md",
    "ch14_airflow_validation_log.csv",
]
CH14_FIGURE_FILES = ["ch14_daily_sales.png"]


def get_base_dir_from_env(default: str | Path = ".") -> Path:
    """PROJECT_ROOT 환경변수가 있으면 우선 사용하고, 없으면 default 경로를 반환합니다.

    Docker Compose 기반 Airflow에서는 PROJECT_ROOT=/opt/airflow/project 로 설정됩니다.
    로컬 Python 실행에서는 프로젝트 루트 경로를 직접 넘기거나 현재 디렉터리를 사용합니다.
    """
    return Path(os.getenv("PROJECT_ROOT", str(default))).resolve()


def project_root_from_file(file_path: str | Path) -> Path:
    """scripts 폴더의 파일 경로를 기준으로 프로젝트 루트를 반환합니다."""
    return Path(file_path).resolve().parents[1]


def get_project_paths(base_dir: str | Path = ".") -> dict[str, Path]:
    """프로젝트 주요 폴더 경로를 반환하고 필요한 폴더를 생성합니다."""
    base_path = get_base_dir_from_env(base_dir) if str(base_dir) == "." else Path(base_dir).resolve()
    paths = {
        "base_dir": base_path,
        "raw_dir": base_path / "data" / "raw",
        "processed_dir": base_path / "data" / "processed",
        "report_dir": base_path / "reports",
        "figure_dir": base_path / "reports" / "figures",
        "docker_airflow_dir": base_path / "automation" / "airflow",
        "docker_dag_dir": base_path / "automation" / "airflow" / "dags",
    }
    for key in ["raw_dir", "processed_dir", "report_dir", "figure_dir", "docker_dag_dir"]:
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def expected_input_files(base_dir: str | Path = ".") -> list[Path]:
    """필수 원본 CSV 파일 경로를 반환합니다."""
    paths = get_project_paths(base_dir)
    return [paths["raw_dir"] / filename for filename in RAW_FILENAMES]


def expected_output_files(base_dir: str | Path = ".") -> list[Path]:
    """14장 파이프라인에서 생성되어야 하는 주요 산출물 경로를 반환합니다."""
    paths = get_project_paths(base_dir)
    processed_files = [paths["processed_dir"] / filename for filename in PROCESSED_FILENAMES]
    report_files = [paths["report_dir"] / filename for filename in CH14_REPORT_FILES]
    figure_files = [paths["figure_dir"] / filename for filename in CH14_FIGURE_FILES]
    return processed_files + report_files + figure_files


def check_input_files(base_dir: str | Path = ".") -> pd.DataFrame:
    """입력 파일 존재 여부를 확인하고 누락 파일이 있으면 오류를 발생시킵니다."""
    files = expected_input_files(base_dir)
    rows = []
    for path in files:
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        rows.append(
            {
                "file": str(path),
                "exists": exists,
                "size": size,
                "status": "ok" if exists and size > 0 else "error",
            }
        )

    result = pd.DataFrame(rows)
    failed = result[result["status"] != "ok"]
    if not failed.empty:
        missing = ", ".join(failed["file"].tolist())
        raise FileNotFoundError("입력 파일이 없습니다: " + missing)
    return result


def _strip_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """문자열 컬럼의 앞뒤 공백을 제거합니다."""
    result = df.copy()
    text_columns = result.select_dtypes(include="object").columns
    for col in text_columns:
        result[col] = result[col].where(result[col].isna(), result[col].astype(str).str.strip())
    return result


def run_preprocessing(base_dir: str | Path = ".") -> dict[str, Path]:
    """원본 CSV를 읽어 전처리 후 data/processed에 저장합니다."""
    paths = get_project_paths(base_dir)
    check_input_files(base_dir)

    customers = pd.read_csv(paths["raw_dir"] / "customers.csv")
    products = pd.read_csv(paths["raw_dir"] / "products.csv")
    orders = pd.read_csv(paths["raw_dir"] / "orders.csv")
    order_items = pd.read_csv(paths["raw_dir"] / "order_items.csv")

    customers = _strip_text_columns(customers)
    products = _strip_text_columns(products)
    orders = _strip_text_columns(orders)
    order_items = _strip_text_columns(order_items)

    if "age" in customers.columns:
        customers["age"] = pd.to_numeric(customers["age"], errors="coerce")
        customers["age"] = customers["age"].fillna(customers["age"].median())

    if "city" in customers.columns:
        customers["city"] = customers["city"].fillna("Unknown")

    if "signup_date" in customers.columns:
        customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="coerce")

    if "price" in products.columns:
        products["price"] = pd.to_numeric(products["price"], errors="coerce")
        products = products[products["price"] > 0]

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders = orders.dropna(subset=["order_id", "customer_id", "order_date"])

    if "order_status" in orders.columns:
        status_map = {
            "complete": "completed",
            "Complete": "completed",
            "COMPLETED": "completed",
            "완료": "completed",
            "cancel": "cancelled",
            "Cancel": "cancelled",
            "CANCELLED": "cancelled",
            "취소": "cancelled",
            "refund": "refunded",
            "Refund": "refunded",
            "REFUNDED": "refunded",
            "환불": "refunded",
        }
        orders["order_status"] = orders["order_status"].replace(status_map)

    order_items = order_items.dropna(subset=["order_id", "product_id", "quantity", "unit_price"])
    order_items["quantity"] = pd.to_numeric(order_items["quantity"], errors="coerce")
    order_items["unit_price"] = pd.to_numeric(order_items["unit_price"], errors="coerce")
    order_items = order_items.dropna(subset=["quantity", "unit_price"])
    order_items = order_items[order_items["quantity"] > 0]
    order_items = order_items[order_items["unit_price"] > 0]

    if "line_total" not in order_items.columns:
        order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]
    else:
        order_items["line_total"] = pd.to_numeric(order_items["line_total"], errors="coerce")
        order_items["line_total"] = order_items["line_total"].fillna(
            order_items["quantity"] * order_items["unit_price"]
        )

    outputs = {
        "customers": paths["processed_dir"] / "customers_clean.csv",
        "products": paths["processed_dir"] / "products_clean.csv",
        "orders": paths["processed_dir"] / "orders_clean.csv",
        "order_items": paths["processed_dir"] / "order_items_clean.csv",
    }
    customers.to_csv(outputs["customers"], index=False, encoding="utf-8-sig")
    products.to_csv(outputs["products"], index=False, encoding="utf-8-sig")
    orders.to_csv(outputs["orders"], index=False, encoding="utf-8-sig")
    order_items.to_csv(outputs["order_items"], index=False, encoding="utf-8-sig")
    return outputs


def run_analysis(base_dir: str | Path = ".") -> dict[str, Path]:
    """전처리 데이터에서 일자별 매출과 카테고리별 매출을 계산합니다."""
    paths = get_project_paths(base_dir)
    orders = pd.read_csv(paths["processed_dir"] / "orders_clean.csv", parse_dates=["order_date"])
    order_items = pd.read_csv(paths["processed_dir"] / "order_items_clean.csv")
    products = pd.read_csv(paths["processed_dir"] / "products_clean.csv")

    if "line_total" not in order_items.columns:
        order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]

    order_items["sales"] = order_items["line_total"]
    order_sales = order_items.merge(
        orders[["order_id", "order_date", "order_status"]],
        on="order_id",
        how="left",
    )
    order_sales["order_day"] = order_sales["order_date"].dt.date

    daily_sales = (
        order_sales.groupby("order_day", as_index=False)
        .agg(total_sales=("sales", "sum"), order_count=("order_id", "nunique"))
        .sort_values("order_day")
    )
    daily_sales["avg_order_value"] = (
        daily_sales["total_sales"] / daily_sales["order_count"]
    ).round(0)

    category_sales = (
        order_items.merge(products[["product_id", "category"]], on="product_id", how="left")
        .groupby("category", as_index=False)
        .agg(total_quantity=("quantity", "sum"), total_sales=("sales", "sum"))
        .sort_values("total_sales", ascending=False)
    )
    category_sales["sales_ratio"] = (
        category_sales["total_sales"] / category_sales["total_sales"].sum() * 100
    ).round(2)

    task_summary = create_pipeline_task_summary()

    outputs = {
        "daily_sales": paths["report_dir"] / "ch14_daily_sales.csv",
        "category_sales": paths["report_dir"] / "ch14_category_sales.csv",
        "task_summary": paths["report_dir"] / "ch14_pipeline_task_summary.csv",
    }
    daily_sales.to_csv(outputs["daily_sales"], index=False, encoding="utf-8-sig")
    category_sales.to_csv(outputs["category_sales"], index=False, encoding="utf-8-sig")
    task_summary.to_csv(outputs["task_summary"], index=False, encoding="utf-8-sig")
    return outputs


def generate_visualizations(base_dir: str | Path = ".") -> dict[str, Path]:
    """14장 일자별 매출 그래프를 생성합니다."""
    paths = get_project_paths(base_dir)
    daily_sales = pd.read_csv(paths["report_dir"] / "ch14_daily_sales.csv")
    daily_sales["order_day"] = pd.to_datetime(daily_sales["order_day"])

    figure_path = paths["figure_dir"] / "ch14_daily_sales.png"
    plt.figure(figsize=(10, 5))
    plt.plot(daily_sales["order_day"], daily_sales["total_sales"], marker="o")
    plt.title("Daily Sales Trend")
    plt.xlabel("Order Day")
    plt.ylabel("Total Sales")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(figure_path, dpi=150)
    plt.close()
    return {"daily_sales_figure": figure_path}


def generate_report(base_dir: str | Path = ".") -> Path:
    """14장 자동화 보고서 Markdown 파일을 생성합니다."""
    paths = get_project_paths(base_dir)
    daily_sales = pd.read_csv(paths["report_dir"] / "ch14_daily_sales.csv")
    category_sales = pd.read_csv(paths["report_dir"] / "ch14_category_sales.csv")
    task_summary = pd.read_csv(paths["report_dir"] / "ch14_pipeline_task_summary.csv")

    total_sales = daily_sales["total_sales"].sum()
    total_orders = daily_sales["order_count"].sum()
    top_category = category_sales.iloc[0]["category"] if len(category_sales) > 0 else "확인 불가"

    report_text = f"""# Chapter 14 Airflow 자동화 보고서

## 1. 실행 개요

온라인 쇼핑몰 데이터 분석 파이프라인을 입력 확인, 전처리, 분석, 시각화, 보고서 생성, 산출물 검증 단계로 나누어 실행했습니다.

## 2. 주요 결과

- 총매출: {total_sales:,.0f}
- 총 주문 수: {total_orders:,.0f}
- 매출 1위 카테고리: {top_category}

## 3. 파이프라인 Task 요약

```text
{task_summary.to_string(index=False)}
```

## 4. 카테고리별 매출

```text
{category_sales.to_string(index=False)}
```

## 5. 생성된 산출물

- `data/processed/customers_clean.csv`
- `data/processed/products_clean.csv`
- `data/processed/orders_clean.csv`
- `data/processed/order_items_clean.csv`
- `reports/ch14_daily_sales.csv`
- `reports/ch14_category_sales.csv`
- `reports/figures/ch14_daily_sales.png`
- `reports/ch14_airflow_report.md`
- `reports/ch14_airflow_validation_log.csv`

## 6. Docker/Airflow 실행 환경

이 보고서는 로컬 Python 실행 또는 Docker Compose 기반 Airflow DAG 실행으로 재생성할 수 있습니다. Docker 설치 방법은 별도 블로그 글을 참고하고, 이 저장소에서는 `automation/airflow/docker-compose.yml` 기준으로 Airflow를 실행합니다.

## 7. 해석 시 주의할 점

이 보고서는 자동으로 생성된 요약입니다. 매출 변화의 원인을 단정하려면 외부 데이터, 프로모션 정보, 계절성, 재고 상황 등 추가 데이터와 사람의 검토가 필요합니다.

![Daily Sales](figures/ch14_daily_sales.png)
"""

    report_path = paths["report_dir"] / "ch14_airflow_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    return report_path


def validate_outputs(base_dir: str | Path = ".") -> pd.DataFrame:
    """14장 산출물 존재 여부와 파일 크기를 검증합니다."""
    paths = get_project_paths(base_dir)
    rows = []
    for path in expected_output_files(base_dir):
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        rows.append(
            {
                "file": str(path),
                "exists": exists,
                "size": size,
                "status": "ok" if exists and size > 0 else "error",
            }
        )

    validation_log = pd.DataFrame(rows)
    log_path = paths["report_dir"] / "ch14_airflow_validation_log.csv"
    validation_log.to_csv(log_path, index=False, encoding="utf-8-sig")

    failed = validation_log[validation_log["status"] != "ok"]
    if not failed.empty:
        failed_files = ", ".join(failed["file"].tolist())
        raise RuntimeError("결과 파일 검증 실패: " + failed_files)
    return validation_log


def create_pipeline_task_summary() -> pd.DataFrame:
    """14장 자동화 Task 구조를 표로 반환합니다."""
    return pd.DataFrame(
        {
            "task_id": [
                "check_input_files",
                "run_preprocessing",
                "run_analysis",
                "generate_visualizations",
                "generate_report",
                "validate_outputs",
            ],
            "purpose": [
                "원본 CSV 4개 존재 여부 확인",
                "문자열 공백, 날짜, 숫자형, line_total 전처리",
                "일자별 매출과 카테고리별 매출 계산",
                "일자별 매출 추이 그래프 생성",
                "Markdown 자동 보고서 생성",
                "주요 산출물 존재 여부와 파일 크기 검증",
            ],
            "main_input": [
                "data/raw/*.csv",
                "data/raw/*.csv",
                "data/processed/*_clean.csv",
                "reports/ch14_daily_sales.csv",
                "reports/ch14_daily_sales.csv, reports/ch14_category_sales.csv",
                "data/processed, reports, reports/figures 산출물",
            ],
            "main_output": [
                "입력 확인 결과",
                "data/processed/*_clean.csv",
                "reports/ch14_daily_sales.csv, reports/ch14_category_sales.csv",
                "reports/figures/ch14_daily_sales.png",
                "reports/ch14_airflow_report.md",
                "reports/ch14_airflow_validation_log.csv",
            ],
        }
    )


def create_airflow_setup_guide() -> pd.DataFrame:
    """Docker Compose 기반 Airflow 실습 순서를 요약합니다."""
    return pd.DataFrame(
        {
            "step": [
                "Docker 설치",
                "Docker 동작 확인",
                "Python 파이프라인 사전 검증",
                "Airflow 환경 파일 준비",
                "Airflow 이미지 빌드 및 DB 초기화",
                "Airflow 실행",
                "Airflow UI 접속",
                "DAG 실행",
                "산출물 검증",
                "종료 또는 초기화",
            ],
            "command_or_action": [
                "별도 블로그 글 참고: https://blog.naver.com/dev-dog/224341211248",
                "docker --version && docker compose version && docker run hello-world",
                "python scripts/generate_sample_data.py && python scripts/run_ch14_pipeline.py",
                "cd automation/airflow && cp .env.example .env",
                "docker compose up airflow-init",
                "docker compose up",
                "http://localhost:8080 / airflow / airflow",
                "Airflow UI에서 ch14_local_analysis_pipeline 수동 실행",
                "reports/ch14_airflow_validation_log.csv 확인",
                "docker compose down 또는 docker compose down --volumes --remove-orphans",
            ],
            "note": [
                "강의안에는 Docker 설치 과정을 길게 포함하지 않음",
                "설치 성공 여부를 최소 명령으로 확인",
                "Airflow 문제가 아니라 분석 코드 문제가 없는지 먼저 확인",
                "Windows는 copy .env.example .env 사용 가능",
                "최초 1회 또는 초기화 후 실행",
                "터미널을 열어 둔 상태로 UI 접속",
                "초기 계정은 수업용 기본값",
                "실패 Task 로그를 확인",
                "모든 status가 ok인지 확인",
                "완전 초기화는 볼륨까지 삭제하므로 주의",
            ],
        }
    )


def run_local_pipeline(base_dir: str | Path = ".") -> dict[str, object]:
    """Airflow 없이 14장 파이프라인을 로컬 Python으로 순서대로 실행합니다."""
    input_check = check_input_files(base_dir)
    preprocessing_outputs = run_preprocessing(base_dir)
    analysis_outputs = run_analysis(base_dir)
    figure_outputs = generate_visualizations(base_dir)
    report_path = generate_report(base_dir)
    validation_log = validate_outputs(base_dir)
    setup_guide = create_airflow_setup_guide()

    paths = get_project_paths(base_dir)
    setup_guide_path = paths["report_dir"] / "ch14_airflow_setup_guide.csv"
    setup_guide.to_csv(setup_guide_path, index=False, encoding="utf-8-sig")

    return {
        "input_check": input_check,
        "preprocessing_outputs": preprocessing_outputs,
        "analysis_outputs": analysis_outputs,
        "figure_outputs": figure_outputs,
        "report_path": report_path,
        "validation_log": validation_log,
        "setup_guide": setup_guide,
        "setup_guide_path": setup_guide_path,
    }


def write_validation_log_csv(rows: list[dict[str, object]], output_path: str | Path) -> None:
    """Airflow DAG 내부에서 사용할 수 있는 CSV 검증 로그 저장 함수입니다."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "exists", "size", "status"])
        writer.writeheader()
        writer.writerows(rows)
