# 14장. 반복되는 분석 흐름을 자동화하기

데이터 분석은 한 번 실행하고 끝나는 작업처럼 보이지만, 실제 업무에서는 같은 흐름을 반복하는 경우가 많습니다. 매일 아침 전날 매출 데이터를 확인하고, 새 CSV 파일을 불러오고, 전처리하고, 지표를 계산하고, 그래프를 만들고, 보고서를 작성한 뒤, 담당자에게 전달하는 식입니다.

처음에는 이런 작업을 수동으로 실행해도 괜찮습니다. 하지만 반복 주기가 짧아지고, 처리 단계가 많아지고, 결과를 기다리는 사람이 생기면 수동 실행은 금방 불안정해집니다. 어떤 파일을 먼저 실행해야 하는지 헷갈릴 수 있고, 중간 오류를 놓칠 수 있으며, 보고서 파일이 생성되지 않았는데도 완료된 것으로 착각할 수 있습니다.

분석 자동화는 이런 반복 흐름을 정해진 순서와 조건에 따라 실행되도록 만드는 과정입니다. 이 장에서는 Make, n8n, Airflow를 분석 자동화 도구의 관점에서 살펴보고, 온라인 쇼핑몰 분석 흐름을 로컬 Airflow 파이프라인으로 직접 실행해 봅니다.

핵심은 특정 도구 하나를 외우는 것이 아닙니다. **반복되는 분석 작업을 단계로 나누고, 각 단계의 입력과 출력을 정리하며, 실패했을 때 어디에서 문제가 생겼는지 확인할 수 있는 구조를 만드는 것**입니다.

<figure class="figure">
  <img src="../assets/images/ch14/ch14_airflow_pipeline_overview.png" alt="분석 자동화와 파이프라인 전체 흐름도">
  <figcaption>그림 14-1. 분석 자동화와 파이프라인 전체 흐름도</figcaption>
</figure>

## 1. 자동화는 코드를 대신 쓰는 일이 아니다

자동화는 분석 코드를 없애는 것이 아닙니다. 오히려 잘 정리된 분석 코드가 있어야 자동화할 수 있습니다. 전처리 코드, 분석 코드, 시각화 코드, 보고서 생성 코드가 뒤섞여 있으면 자동화 도구가 실행 순서를 관리하기 어렵습니다.

자동화하기 좋은 분석 흐름은 다음처럼 나눌 수 있습니다.

| 단계 | 하는 일 | 입력 | 출력 |
| --- | --- | --- | --- |
| 입력 확인 | 원본 데이터가 있는지 확인 | `data/raw/*.csv` | 확인 결과 |
| 전처리 | 결측치, 타입, 중복 처리 | 원본 CSV | `data/processed/*_clean.csv` |
| 분석 | 주요 지표 계산 | 전처리 데이터 | `reports/*.csv` |
| 시각화 | 그래프 생성 | 분석 결과 CSV | `reports/figures/*.png` |
| 보고서 | Markdown 보고서 작성 | 표, 그래프, 해석 문장 | `reports/*.md` |
| 검증 | 결과 파일 존재 여부 확인 | 산출물 목록 | 검증 로그 |
| 전달 | 메일, Slack, Drive 등으로 공유 | 보고서 파일 | 알림 또는 발송 기록 |

자동화의 목적은 사람이 아무것도 하지 않게 만드는 것이 아닙니다. 반복 실행과 파일 전달 같은 기계적인 일을 줄이고, 사람은 데이터 품질과 결과 해석을 확인하는 데 집중하도록 만드는 것입니다.

## 2. Make, n8n, Airflow는 어디에 쓰이는가

분석 자동화 도구는 모두 같은 역할을 하는 것처럼 보이지만, 실제로는 잘 맞는 상황이 조금씩 다릅니다.

| 도구 | 잘 맞는 상황 | 예시 |
| --- | --- | --- |
| Make | 외부 서비스 연결과 알림 자동화 | 보고서 파일 생성 후 Gmail 발송, Slack 알림 |
| n8n | 노코드/로우코드 기반 워크플로우 구성 | API 호출, 데이터 저장, 내부 도구 연결 |
| Airflow | 코드 기반 데이터 파이프라인 운영 | 전처리 → 분석 → 시각화 → 보고서 생성 순서 관리 |

Make와 n8n은 여러 앱을 연결하는 데 강합니다. Google Drive에 파일이 올라오면 Slack으로 알림을 보내거나, 특정 웹훅이 호출되면 이메일을 발송하는 흐름에 적합합니다. 반면 Airflow는 데이터 파이프라인처럼 여러 코드 작업을 정해진 순서대로 실행하고, 실패한 작업의 로그를 확인하고, 필요한 작업만 재실행하는 데 적합합니다.

실무에서는 이 도구들을 함께 사용할 수도 있습니다. 예를 들어 Airflow가 분석 파이프라인을 실행해 보고서를 만들고, Make나 n8n이 그 보고서를 감지해 담당자에게 발송하는 식입니다.

## 3. Docker는 언제 필요하고, 왜 이번 실습에서는 제외하는가

Airflow는 실무 환경에서 Docker, Kubernetes, 클라우드 관리형 서비스와 함께 자주 사용됩니다. 이런 방식은 실행 환경을 일정하게 유지하고, 여러 사람이 같은 환경에서 파이프라인을 운영하는 데 유리합니다.

하지만 Docker를 사용하려면 Docker Desktop 설치, 이미지 다운로드, 컨테이너와 볼륨 개념, 포트 연결, 권한 문제를 함께 설명해야 합니다. 데이터 분석 자동화의 핵심을 처음 배우는 단계에서는 Docker 자체가 별도의 학습 부담이 될 수 있습니다.

따라서 이 장의 실습은 Docker를 사용하지 않습니다. 대신 로컬 Python 가상환경에 Airflow를 설치하고, `airflow standalone`으로 웹 UI와 스케줄러를 실행합니다. 이 방식은 운영용 배포 방식은 아니지만, DAG, Task, 의존성, 실행 로그, 실패 확인을 배우기에는 충분합니다.

Windows 환경에서는 Airflow를 네이티브 PowerShell에서 바로 실행할 때 문제가 생길 수 있습니다. 가능하면 WSL2의 Ubuntu 터미널이나 macOS/Linux 터미널을 기준으로 실습하는 것을 권장합니다. Windows 사용자는 VS Code에서 WSL에 연결해 동일한 프로젝트 폴더를 열어 진행하면 됩니다.

## 4. 이번 장에서 완성할 로컬 Airflow 실습

이번 실습에서는 온라인 쇼핑몰 데이터 분석을 다음 순서로 자동화합니다.

```text
check_input_files
→ run_preprocessing
→ run_analysis
→ generate_visualizations
→ generate_report
→ validate_outputs
```

각 Task의 역할은 다음과 같습니다.

| Task | 역할 | 성공 조건 |
| --- | --- | --- |
| `check_input_files` | 원본 CSV 4개가 있는지 확인 | 모든 입력 파일 존재 |
| `run_preprocessing` | 원본 CSV를 전처리 파일로 저장 | `data/processed/*_clean.csv` 생성 |
| `run_analysis` | 일자별 매출과 카테고리별 매출 계산 | `reports/ch14_daily_sales.csv`, `reports/ch14_category_sales.csv` 생성 |
| `generate_visualizations` | 일자별 매출 그래프 생성 | `reports/figures/ch14_daily_sales.png` 생성 |
| `generate_report` | Markdown 보고서 생성 | `reports/ch14_airflow_report.md` 생성 |
| `validate_outputs` | 결과 파일 존재와 크기 검증 | 검증 로그 생성, 오류 없으면 성공 |

실습의 목표는 Airflow 설치 자체가 아닙니다. 분석 작업을 작은 단위로 나누고, Airflow가 그 작업들을 어떤 순서로 실행하고, 실패했을 때 어디에서 멈추는지 확인하는 것입니다.

<figure class="figure">
  <img src="../assets/images/ch14/ch14_airflow_task_dependency.png" alt="분석 파이프라인의 Task 의존성 흐름">
  <figcaption>그림 14-2. 분석 파이프라인의 Task 의존성 흐름</figcaption>
</figure>

## 5. 실습 프로젝트 구조 준비하기

먼저 프로젝트 루트에 다음 폴더가 있다고 가정합니다.

```text
my-llm-data-analysis-course/
├─ data/
│  ├─ raw/
│  └─ processed/
├─ scripts/
├─ reports/
│  └─ figures/
├─ .airflow/
│  └─ dags/
└─ requirements.txt
```

아직 폴더가 없다면 터미널에서 다음 명령으로 만들 수 있습니다.

```bash
mkdir -p data/raw data/processed scripts reports/figures .airflow/dags
```

Windows PowerShell에서는 다음처럼 실행할 수 있습니다.

```powershell
New-Item -ItemType Directory -Force data/raw, data/processed, scripts, reports/figures, .airflow/dags
```

`data/raw/` 폴더에는 다음 4개 CSV 파일이 있어야 합니다.

```text
customers.csv
products.csv
orders.csv
order_items.csv
```

앞 장에서 샘플 데이터를 생성했다면 이미 준비되어 있을 수 있습니다. 없다면 먼저 샘플 데이터 생성 스크립트를 실행합니다.

```bash
python scripts/generate_sample_data.py
```

Airflow 실행 과정에서 `.airflow/` 폴더에는 설정 파일, 로그, DB 파일 등이 만들어질 수 있습니다. 이 폴더는 실습 실행 환경에 해당하므로 일반적으로 Git에 올리지 않는 것이 좋습니다. `.gitignore`에 다음 항목을 추가해 둡니다.

```text
.airflow/
```

## 6. 전처리 스크립트 만들기

Airflow가 실행할 코드는 Notebook보다 독립 실행 가능한 Python 스크립트로 준비하는 것이 좋습니다. 먼저 `scripts/ch14_preprocessing.py` 파일을 만듭니다.

```python
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

customers = pd.read_csv(RAW_DIR / "customers.csv")
products = pd.read_csv(RAW_DIR / "products.csv")
orders = pd.read_csv(RAW_DIR / "orders.csv")
order_items = pd.read_csv(RAW_DIR / "order_items.csv")

for df in [customers, products, orders, order_items]:
    text_columns = df.select_dtypes(include="object").columns
    for col in text_columns:
        df[col] = df[col].astype(str).str.strip()

orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
orders = orders.dropna(subset=["order_id", "customer_id", "order_date"])
order_items = order_items.dropna(subset=["order_id", "product_id", "quantity", "unit_price"])

order_items["quantity"] = pd.to_numeric(order_items["quantity"], errors="coerce")
order_items["unit_price"] = pd.to_numeric(order_items["unit_price"], errors="coerce")
order_items = order_items.dropna(subset=["quantity", "unit_price"])

if "line_total" not in order_items.columns:
    order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]
else:
    order_items["line_total"] = pd.to_numeric(order_items["line_total"], errors="coerce")
    order_items["line_total"] = order_items["line_total"].fillna(
        order_items["quantity"] * order_items["unit_price"]
    )

customers.to_csv(PROCESSED_DIR / "customers_clean.csv", index=False, encoding="utf-8-sig")
products.to_csv(PROCESSED_DIR / "products_clean.csv", index=False, encoding="utf-8-sig")
orders.to_csv(PROCESSED_DIR / "orders_clean.csv", index=False, encoding="utf-8-sig")
order_items.to_csv(PROCESSED_DIR / "order_items_clean.csv", index=False, encoding="utf-8-sig")

print("전처리 완료:", PROCESSED_DIR)
```

이 스크립트는 원본 데이터를 읽고, 문자열 공백을 정리하고, 날짜와 숫자형을 변환하고, 전처리된 CSV 파일을 `data/processed/`에 저장합니다.

## 7. 분석 스크립트 만들기

다음으로 `scripts/ch14_analysis.py` 파일을 만듭니다.

```python
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

orders = pd.read_csv(PROCESSED_DIR / "orders_clean.csv", parse_dates=["order_date"])
order_items = pd.read_csv(PROCESSED_DIR / "order_items_clean.csv")
products = pd.read_csv(PROCESSED_DIR / "products_clean.csv")

order_items["sales"] = order_items["line_total"]

order_sales = order_items.merge(
    orders[["order_id", "order_date", "order_status"]],
    on="order_id",
    how="left"
)

order_sales["order_day"] = order_sales["order_date"].dt.date

daily_sales = (
    order_sales
    .groupby("order_day", as_index=False)
    .agg(
        total_sales=("sales", "sum"),
        order_count=("order_id", "nunique")
    )
    .sort_values("order_day")
)

daily_sales["avg_order_value"] = (
    daily_sales["total_sales"] / daily_sales["order_count"]
).round(0)

category_sales = (
    order_items
    .merge(products[["product_id", "category"]], on="product_id", how="left")
    .groupby("category", as_index=False)
    .agg(
        total_quantity=("quantity", "sum"),
        total_sales=("sales", "sum")
    )
    .sort_values("total_sales", ascending=False)
)

daily_sales.to_csv(REPORT_DIR / "ch14_daily_sales.csv", index=False, encoding="utf-8-sig")
category_sales.to_csv(REPORT_DIR / "ch14_category_sales.csv", index=False, encoding="utf-8-sig")

print("분석 완료:", REPORT_DIR)
```

이 스크립트는 전처리된 데이터를 읽어 일자별 매출과 카테고리별 매출을 계산합니다.

## 8. 시각화 스크립트 만들기

다음으로 `scripts/ch14_visualization.py` 파일을 만듭니다.

```python
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE_DIR / "reports"
FIGURE_DIR = REPORT_DIR / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

daily_sales = pd.read_csv(REPORT_DIR / "ch14_daily_sales.csv")
daily_sales["order_day"] = pd.to_datetime(daily_sales["order_day"])

plt.figure(figsize=(10, 5))
plt.plot(daily_sales["order_day"], daily_sales["total_sales"], marker="o")
plt.title("Daily Sales Trend")
plt.xlabel("Order Day")
plt.ylabel("Total Sales")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "ch14_daily_sales.png", dpi=150)
plt.close()

print("시각화 완료:", FIGURE_DIR / "ch14_daily_sales.png")
```

운영체제나 폰트 설정에 따라 한글 그래프 제목이 깨질 수 있으므로, 이 예제에서는 그래프 제목과 축 이름을 영어로 작성했습니다.

## 9. 보고서 생성 스크립트 만들기

다음으로 `scripts/ch14_report.py` 파일을 만듭니다.

```python
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE_DIR / "reports"
FIGURE_DIR = REPORT_DIR / "figures"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

daily_sales = pd.read_csv(REPORT_DIR / "ch14_daily_sales.csv")
category_sales = pd.read_csv(REPORT_DIR / "ch14_category_sales.csv")

total_sales = daily_sales["total_sales"].sum()
total_orders = daily_sales["order_count"].sum()
top_category = category_sales.iloc[0]["category"] if len(category_sales) > 0 else "확인 불가"

report_text = f"""# Chapter 14 Airflow 자동화 보고서

## 1. 실행 개요

Airflow DAG를 사용해 온라인 쇼핑몰 데이터 분석 파이프라인을 실행했습니다.

## 2. 주요 결과

- 총매출: {total_sales:,.0f}
- 총 주문 수: {total_orders:,.0f}
- 매출 1위 카테고리: {top_category}

## 3. 생성된 산출물

- `reports/ch14_daily_sales.csv`
- `reports/ch14_category_sales.csv`
- `reports/figures/ch14_daily_sales.png`
- `reports/ch14_airflow_report.md`

## 4. 해석 시 주의할 점

이 보고서는 자동으로 생성된 요약입니다. 매출 변화의 원인을 단정하려면 추가 데이터와 사람의 검토가 필요합니다.

![Daily Sales](figures/ch14_daily_sales.png)
"""

(REPORT_DIR / "ch14_airflow_report.md").write_text(report_text, encoding="utf-8")

print("보고서 생성 완료:", REPORT_DIR / "ch14_airflow_report.md")
```

자동 보고서는 결과 전달 속도를 높여 주지만, 해석의 최종 책임은 사람에게 있습니다. 특히 자동 보고서가 원인을 단정하지 않도록 주의해야 합니다.

## 10. 먼저 Python 스크립트만 실행해 보기

Airflow에 연결하기 전에 각 스크립트가 독립적으로 실행되는지 확인합니다.

```bash
python scripts/ch14_preprocessing.py
python scripts/ch14_analysis.py
python scripts/ch14_visualization.py
python scripts/ch14_report.py
```

정상적으로 실행되면 다음 파일이 생성되어야 합니다.

```text
data/processed/customers_clean.csv
data/processed/products_clean.csv
data/processed/orders_clean.csv
data/processed/order_items_clean.csv
reports/ch14_daily_sales.csv
reports/ch14_category_sales.csv
reports/figures/ch14_daily_sales.png
reports/ch14_airflow_report.md
```

이 단계에서 오류가 난다면 Airflow 문제가 아니라 Python 스크립트 문제입니다. Airflow에 연결하기 전에 반드시 여기에서 먼저 해결해야 합니다.

## 11. 로컬 Airflow 설치하기

Airflow는 의존성이 많은 애플리케이션이므로 기존 `.venv`와 분리해 별도의 가상환경을 만드는 것을 권장합니다. 아래 명령은 macOS, Linux, WSL2 Ubuntu 기준입니다.

```bash
python3 -m venv .venv-airflow
source .venv-airflow/bin/activate
python -m pip install --upgrade pip
```

Airflow는 설치 시 버전과 Python 버전에 맞는 constraints 파일을 사용하는 방식이 안정적입니다. 아래 예시는 Airflow 3.3.0 기준입니다. 실습 시점에 Airflow 공식 문서에서 최신 안정 버전과 Python 지원 버전을 확인한 뒤 버전 번호를 조정할 수 있습니다.

```bash
AIRFLOW_VERSION=3.3.0
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
pip install pandas matplotlib
```

설치가 끝나면 Airflow 버전을 확인합니다.

```bash
airflow version
```

만약 `airflow` 명령을 찾지 못한다면 다음처럼 Python 모듈 방식으로 실행할 수도 있습니다.

```bash
python -m airflow version
```

## 12. Airflow 홈 폴더 설정하기

Airflow는 DAG, 로그, 설정 파일을 저장할 홈 폴더가 필요합니다. 이 실습에서는 프로젝트 내부의 `.airflow/` 폴더를 Airflow 홈으로 사용합니다.

```bash
export AIRFLOW_HOME="$(pwd)/.airflow"
mkdir -p "$AIRFLOW_HOME/dags"
```

현재 설정이 잘 적용되었는지 확인합니다.

```bash
echo $AIRFLOW_HOME
```

Windows WSL2 Ubuntu에서도 위 명령을 그대로 사용할 수 있습니다. PowerShell 네이티브 환경에서 진행하는 경우에는 Airflow 실행 문제가 생길 수 있으므로 WSL2 사용을 권장합니다.

## 13. DAG 파일 작성하기

이제 `.airflow/dags/ch14_local_analysis_pipeline.py` 파일을 만듭니다.

```python
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import csv

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"
FIGURE_DIR = REPORT_DIR / "figures"

REQUIRED_INPUT_FILES = [
    RAW_DIR / "customers.csv",
    RAW_DIR / "products.csv",
    RAW_DIR / "orders.csv",
    RAW_DIR / "order_items.csv",
]

REQUIRED_OUTPUT_FILES = [
    BASE_DIR / "data" / "processed" / "customers_clean.csv",
    BASE_DIR / "data" / "processed" / "products_clean.csv",
    BASE_DIR / "data" / "processed" / "orders_clean.csv",
    BASE_DIR / "data" / "processed" / "order_items_clean.csv",
    REPORT_DIR / "ch14_daily_sales.csv",
    REPORT_DIR / "ch14_category_sales.csv",
    FIGURE_DIR / "ch14_daily_sales.png",
    REPORT_DIR / "ch14_airflow_report.md",
]


def check_input_files():
    missing_files = [str(path) for path in REQUIRED_INPUT_FILES if not path.exists()]
    if missing_files:
        raise FileNotFoundError("입력 파일이 없습니다: " + ", ".join(missing_files))
    print("입력 파일 확인 완료")


def validate_outputs():
    validation_rows = []

    for path in REQUIRED_OUTPUT_FILES:
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        validation_rows.append({
            "file": str(path),
            "exists": exists,
            "size": size,
            "status": "ok" if exists and size > 0 else "error",
        })

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = REPORT_DIR / "ch14_airflow_validation_log.csv"

    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "exists", "size", "status"])
        writer.writeheader()
        writer.writerows(validation_rows)

    failed = [row["file"] for row in validation_rows if row["status"] != "ok"]
    if failed:
        raise RuntimeError("결과 파일 검증 실패: " + ", ".join(failed))

    print("결과 파일 검증 완료:", log_path)


default_args = {
    "owner": "data-analysis-class",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="ch14_local_analysis_pipeline",
    description="Docker 없이 로컬에서 실행하는 온라인 쇼핑몰 분석 파이프라인",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["chapter14", "local", "data-analysis"],
) as dag:

    check_input_files_task = PythonOperator(
        task_id="check_input_files",
        python_callable=check_input_files,
    )

    run_preprocessing = BashOperator(
        task_id="run_preprocessing",
        bash_command=f"python {BASE_DIR / 'scripts' / 'ch14_preprocessing.py'}",
    )

    run_analysis = BashOperator(
        task_id="run_analysis",
        bash_command=f"python {BASE_DIR / 'scripts' / 'ch14_analysis.py'}",
    )

    generate_visualizations = BashOperator(
        task_id="generate_visualizations",
        bash_command=f"python {BASE_DIR / 'scripts' / 'ch14_visualization.py'}",
    )

    generate_report = BashOperator(
        task_id="generate_report",
        bash_command=f"python {BASE_DIR / 'scripts' / 'ch14_report.py'}",
    )

    validate_outputs_task = PythonOperator(
        task_id="validate_outputs",
        python_callable=validate_outputs,
    )

    check_input_files_task >> run_preprocessing >> run_analysis >> generate_visualizations >> generate_report >> validate_outputs_task
```

이 DAG 파일에서 가장 중요한 부분은 마지막 줄입니다.

```python
check_input_files_task >> run_preprocessing >> run_analysis >> generate_visualizations >> generate_report >> validate_outputs_task
```

이 한 줄이 전체 분석 파이프라인의 실행 순서를 정의합니다.

## 14. Airflow Standalone 실행하기

Airflow를 실행하기 전에 가상환경과 `AIRFLOW_HOME`이 설정되어 있는지 확인합니다.

```bash
source .venv-airflow/bin/activate
export AIRFLOW_HOME="$(pwd)/.airflow"
```

이제 Airflow를 standalone 모드로 실행합니다.

```bash
airflow standalone
```

`airflow standalone`은 로컬 실습에 필요한 여러 구성 요소를 한 번에 실행합니다. 처음 실행하면 Airflow 설정 파일, 내부 DB, 관리자 계정 정보가 생성됩니다. 터미널에 관리자 계정과 비밀번호가 표시되거나, 비밀번호 파일 위치가 안내될 수 있습니다.

Airflow 웹 UI는 기본적으로 다음 주소에서 확인합니다.

```text
http://localhost:8080
```

Airflow가 실행 중인 터미널은 그대로 두고, 새 터미널을 하나 더 엽니다. 새 터미널에서도 같은 가상환경과 `AIRFLOW_HOME`을 설정해야 합니다.

```bash
source .venv-airflow/bin/activate
export AIRFLOW_HOME="$(pwd)/.airflow"
```

DAG가 인식되는지 확인합니다.

```bash
airflow dags list | grep ch14
```

`ch14_local_analysis_pipeline`이 보이면 DAG 파일을 Airflow가 정상적으로 읽은 것입니다.

## 15. Airflow UI에서 DAG 실행하기

브라우저에서 `http://localhost:8080`에 접속한 뒤 로그인합니다. DAG 목록에서 `ch14_local_analysis_pipeline`을 찾습니다.

실행 순서는 다음과 같습니다.

1. `ch14_local_analysis_pipeline` DAG를 찾습니다.
2. DAG를 활성화합니다.
3. 수동 실행 버튼을 눌러 DAG를 실행합니다.
4. Graph 또는 Grid 화면에서 Task 실행 순서를 확인합니다.
5. 실패한 Task가 있다면 해당 Task를 클릭해 로그를 확인합니다.

CLI로 실행하고 싶다면 새 터미널에서 다음 명령을 사용할 수 있습니다.

```bash
airflow dags trigger ch14_local_analysis_pipeline
```

실행 상태는 다음 명령으로 확인할 수 있습니다.

```bash
airflow dags list-runs -d ch14_local_analysis_pipeline
```

## 16. 결과 파일 확인하기

DAG 실행이 성공했다면 다음 파일들이 생성됩니다.

```text
data/processed/customers_clean.csv
data/processed/products_clean.csv
data/processed/orders_clean.csv
data/processed/order_items_clean.csv
reports/ch14_daily_sales.csv
reports/ch14_category_sales.csv
reports/figures/ch14_daily_sales.png
reports/ch14_airflow_report.md
reports/ch14_airflow_validation_log.csv
```

검증 로그를 확인합니다.

```bash
cat reports/ch14_airflow_validation_log.csv
```

각 파일의 `status`가 `ok`라면 파이프라인 산출물이 정상적으로 생성된 것입니다.

## 17. 실패 상황을 일부러 만들어 보기

자동화 실습에서 중요한 것은 성공보다 실패를 읽는 능력입니다. 다음처럼 입력 파일 하나를 잠시 다른 이름으로 바꿔 봅니다.

```bash
mv data/raw/customers.csv data/raw/customers_backup.csv
```

다시 DAG를 실행합니다.

```bash
airflow dags trigger ch14_local_analysis_pipeline
```

이번에는 `check_input_files` 단계에서 실패해야 합니다. Airflow UI에서 실패한 Task를 클릭하고 로그를 확인합니다. 로그에 `입력 파일이 없습니다`라는 메시지가 보이면 정상입니다.

실습이 끝나면 파일명을 다시 복구합니다.

```bash
mv data/raw/customers_backup.csv data/raw/customers.csv
```

이 실습을 통해 Airflow가 단순히 코드를 실행하는 도구가 아니라, 어느 단계에서 실패했는지 확인하고 다시 실행할 수 있게 도와주는 도구라는 점을 이해할 수 있습니다.

## 18. Make와 n8n은 전달과 연결에 강하다

Airflow가 코드 기반 분석 파이프라인을 담당한다면, Make와 n8n은 결과물을 외부 서비스와 연결하는 데 유용합니다. 예를 들어 Airflow가 `reports/ch14_airflow_report.md`를 생성한 뒤, Make나 n8n이 해당 파일을 감지해 Gmail, Slack, Google Drive, Notion 등으로 전달할 수 있습니다.

자동화 흐름을 나누면 다음처럼 정리할 수 있습니다.

| 구간 | 담당 도구 예시 | 역할 |
| --- | --- | --- |
| 데이터 처리 | Python, Airflow | 전처리, 분석, 시각화, 보고서 생성 |
| 결과 검증 | Python, Airflow | 파일 생성 여부, 크기, 로그 확인 |
| 외부 전달 | Make, n8n | 메일 발송, Slack 알림, Drive 업로드 |
| 운영 확인 | Airflow UI, Make/n8n 실행 로그 | 실패 지점과 재실행 여부 확인 |

Make나 n8n에서 바로 모든 분석을 처리하려고 하면 복잡해질 수 있습니다. 반대로 Airflow에서 메일 발송과 외부 앱 연계까지 모두 처리하려고 해도 운영이 무거워질 수 있습니다. 분석 파이프라인과 외부 서비스 연결을 적절히 나누면 구조가 단순해집니다.

## 19. LLM과 함께 파이프라인을 설계한다

LLM은 자동화 파이프라인을 설계할 때 좋은 초안 도구가 될 수 있습니다. 어떤 단계를 Task로 나눌지, 어떤 결과 파일을 검증해야 할지, Make나 n8n을 어디에 연결하면 좋을지 아이디어를 얻을 수 있습니다.

파이프라인 설계를 요청할 때는 다음처럼 질문할 수 있습니다.

```text
온라인 쇼핑몰 주문 데이터를 매일 분석하는 자동화 파이프라인을 설계하려고 합니다.

입력 파일:
- orders.csv
- order_items.csv
- products.csv
- customers.csv

필요한 작업:
- 입력 파일 확인
- 데이터 전처리
- 매출 분석
- 시각화 생성
- Markdown 보고서 생성
- 결과 파일 검증
- 보고서 발송 또는 Slack 알림

요청:
1. 전체 작업을 단계별 Task로 나누어 주세요.
2. 각 Task의 입력과 출력을 표로 정리해 주세요.
3. Airflow가 담당할 부분과 Make/n8n이 담당할 부분을 나누어 주세요.
4. 실패했을 때 확인해야 할 로그와 검증 항목을 제안해 주세요.
5. 지나치게 복잡한 설치 절차보다 운영 흐름 중심으로 설명해 주세요.
```

LLM이 만든 자동화 설계는 바로 믿지 말고 실제 프로젝트 구조와 비교해야 합니다. 특히 파일 경로, 실행 환경, API 인증, 메일 발송 권한, 실제 컬럼명은 반드시 사람이 확인해야 합니다.

## 20. 자동화 결과를 해석하는 방법

파이프라인이 성공했다고 해서 분석 결과가 항상 타당한 것은 아닙니다. 자동화 결과를 볼 때는 다음 세 가지를 나누어 확인합니다.

| 구분 | 확인할 질문 |
| --- | --- |
| 실행 성공 | 모든 Task가 성공했는가? |
| 산출물 성공 | 필요한 CSV, 그래프, 보고서가 생성되었는가? |
| 분석 품질 | 결과 수치와 해석이 데이터에 맞는가? |

Airflow UI에서 모든 Task가 초록색으로 보이더라도, 보고서의 해석이 잘못되었거나 CSV 값이 비어 있으면 분석 품질은 낮습니다. Make나 n8n에서 메일 발송이 성공했더라도, 첨부 파일이 잘못되었으면 자동화는 실패한 것입니다.

따라서 자동화 결과는 다음 순서로 확인하는 것이 좋습니다.

1. 파이프라인이 실행되었는지 확인합니다.
2. 실패한 Task가 있는지 확인합니다.
3. 결과 파일이 생성되었는지 확인합니다.
4. 결과 파일의 크기와 행 수를 확인합니다.
5. 주요 지표가 상식적인 범위인지 확인합니다.
6. 보고서 해석이 데이터에 없는 원인을 단정하지 않는지 확인합니다.
7. 외부 발송이 필요한 경우 올바른 대상에게 전달되었는지 확인합니다.

## 21. 다음 장으로 이어지는 흐름

이 장에서는 반복되는 분석 흐름을 자동화하는 방법을 살펴보았습니다. Docker를 사용하지 않고 로컬 Airflow 환경에서 입력 확인, 전처리, 분석, 시각화, 보고서 생성, 결과 검증까지 하나의 DAG로 연결했습니다. Make와 n8n은 외부 서비스 연결과 알림에 강하고, Airflow는 코드 기반 분석 파이프라인의 실행 순서와 상태 관리에 강하다는 점도 확인했습니다.

이제 데이터 분석의 기본 흐름, 머신러닝 모델링, LLM 코드 생성과 검증, 외부 데이터 수집, 자동화까지 경험했습니다. 다음 장에서는 이 모든 요소를 기말 프로젝트로 통합합니다. 기말 프로젝트에서는 EDA, 시각화, 머신러닝, LLM 활용, 외부 데이터 또는 자동화 아이디어를 하나의 분석 프로젝트 안에서 연결합니다.
