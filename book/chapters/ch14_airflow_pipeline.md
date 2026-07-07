# 14장. 반복되는 분석 흐름을 자동화하기

데이터 분석은 한 번 실행하고 끝나는 작업처럼 보이지만, 실제 업무에서는 같은 흐름을 반복하는 경우가 많습니다. 매일 아침 전날 매출 데이터를 확인하고, 새 CSV 파일을 불러오고, 전처리하고, 지표를 계산하고, 그래프를 만들고, 보고서를 작성한 뒤, 담당자에게 전달하는 식입니다.

처음에는 이런 작업을 수동으로 실행해도 괜찮습니다. 하지만 반복 주기가 짧아지고, 처리 단계가 많아지고, 결과를 기다리는 사람이 생기면 수동 실행은 금방 불안정해집니다. 어떤 파일을 먼저 실행해야 하는지 헷갈릴 수 있고, 중간 오류를 놓칠 수 있으며, 보고서 파일이 생성되지 않았는데도 완료된 것으로 착각할 수 있습니다.

분석 자동화는 이런 반복 흐름을 정해진 순서와 조건에 따라 실행되도록 만드는 과정입니다. 이 장에서는 Make, n8n, Airflow를 분석 자동화 도구의 관점에서 살펴보고, 온라인 쇼핑몰 분석 흐름을 작은 파이프라인으로 구성하는 방법을 다룹니다.

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

## 3. 파이프라인은 실행 순서를 명확히 하는 구조다

파이프라인은 여러 작업을 순서대로 연결한 흐름입니다. 온라인 쇼핑몰 분석에서는 다음과 같은 파이프라인을 생각할 수 있습니다.

```text
check_input_files
→ run_preprocessing
→ run_analysis
→ generate_visualizations
→ generate_report
→ validate_outputs
→ notify_or_send_report
```

이 순서가 중요한 이유는 각 단계가 이전 단계의 결과를 사용하기 때문입니다. 전처리가 실패했는데 분석이 실행되면 잘못된 데이터로 집계가 이루어질 수 있습니다. 그래프가 만들어지지 않았는데 보고서만 생성되면 보고서에서 이미지가 깨질 수 있습니다. 보고서가 정상적으로 생성되었는지 확인하지 않고 메일을 발송하면 빈 파일을 전달할 수도 있습니다.

<figure class="figure">
  <img src="../assets/images/ch14/ch14_airflow_task_dependency.png" alt="분석 파이프라인의 Task 의존성 흐름">
  <figcaption>그림 14-2. 분석 파이프라인의 Task 의존성 흐름</figcaption>
</figure>

좋은 파이프라인은 작업을 많이 나누는 것이 아니라, 실패 지점을 확인할 수 있을 만큼 적절히 나누는 것입니다.

## 4. Python 스크립트와 자동화 도구의 역할을 나눈다

자동화를 처음 시도할 때 자주 하는 실수는 자동화 도구 안에 모든 분석 로직을 넣는 것입니다. Airflow DAG 파일 안에 pandas 전처리 코드와 그래프 생성 코드, 보고서 생성 코드가 모두 들어가면 파일이 길어지고 테스트하기 어려워집니다.

더 안정적인 방식은 분석 로직과 실행 관리를 분리하는 것입니다.

| 영역 | Python 스크립트 역할 | 자동화 도구 역할 |
| --- | --- | --- |
| 입력 확인 | 파일 존재 여부 확인 함수 작성 | 입력 확인 작업 실행 |
| 전처리 | 결측치, 중복, 타입 처리 | 전처리 스크립트 실행 순서 관리 |
| 분석 | pandas 집계와 지표 계산 | 분석 단계 성공/실패 관리 |
| 시각화 | 그래프 PNG 저장 | 시각화 단계 실행 |
| 보고서 | Markdown 보고서 생성 | 보고서 생성 후 검증 단계 연결 |
| 오류 처리 | 예외 발생 시 종료 | 실패 감지, 재시도, 로그 제공 |
| 전달 | 직접 담당하지 않거나 별도 스크립트 작성 | Make/n8n으로 이메일·Slack·Drive 연결 |

분석 로직은 `scripts/` 폴더에 두고, 자동화 도구는 그 스크립트를 정해진 순서대로 실행하도록 구성하면 관리가 쉬워집니다.

<figure class="figure">
  <img src="../assets/images/ch14/ch14_python_airflow_role_split.png" alt="Python 분석 스크립트와 자동화 도구의 역할 분담">
  <figcaption>그림 14-3. Python 분석 스크립트와 자동화 도구의 역할 분담</figcaption>
</figure>

## 5. 분석 스크립트는 독립적으로 실행 가능해야 한다

자동화 도구에 연결하기 전에는 각 Python 스크립트가 독립적으로 실행되는지 먼저 확인해야 합니다. 예를 들어 전처리 스크립트는 원본 CSV를 읽어 `data/processed`에 정제 파일을 저장해야 합니다.

```python
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

orders = pd.read_csv(RAW_DIR / "orders.csv")
order_items = pd.read_csv(RAW_DIR / "order_items.csv")
products = pd.read_csv(RAW_DIR / "products.csv")
customers = pd.read_csv(RAW_DIR / "customers.csv")

orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
orders = orders.dropna(subset=["order_id", "customer_id", "order_date"])
order_items = order_items.dropna(subset=["order_id", "product_id", "quantity", "unit_price"])

if "line_total" not in order_items.columns:
    order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]

orders.to_csv(PROCESSED_DIR / "orders_clean.csv", index=False, encoding="utf-8-sig")
order_items.to_csv(PROCESSED_DIR / "order_items_clean.csv", index=False, encoding="utf-8-sig")
products.to_csv(PROCESSED_DIR / "products_clean.csv", index=False, encoding="utf-8-sig")
customers.to_csv(PROCESSED_DIR / "customers_clean.csv", index=False, encoding="utf-8-sig")

print("전처리 완료:", PROCESSED_DIR)
```

분석 스크립트는 전처리 결과를 읽어 일자별 매출을 계산합니다.

```python
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

orders = pd.read_csv(PROCESSED_DIR / "orders_clean.csv", parse_dates=["order_date"])
order_items = pd.read_csv(PROCESSED_DIR / "order_items_clean.csv")

if "line_total" in order_items.columns:
    order_items["sales"] = order_items["line_total"]
else:
    order_items["sales"] = order_items["quantity"] * order_items["unit_price"]

merged = order_items.merge(
    orders[["order_id", "order_date"]],
    on="order_id",
    how="left"
)

daily_sales = (
    merged.assign(order_day=merged["order_date"].dt.date)
    .groupby("order_day", as_index=False)["sales"]
    .sum()
    .sort_values("order_day")
)

daily_sales.to_csv(REPORT_DIR / "ch14_daily_sales.csv", index=False, encoding="utf-8-sig")
print("분석 완료:", REPORT_DIR / "ch14_daily_sales.csv")
```

이처럼 각 스크립트가 독립적으로 실행되어야 Airflow나 다른 자동화 도구에 연결했을 때도 문제를 찾기 쉽습니다.

## 6. Airflow로 실행 순서를 관리한다

Airflow는 여러 작업을 DAG로 정의합니다. DAG는 Directed Acyclic Graph의 약자로, 작업들이 어떤 순서로 실행되는지 표현하는 구조입니다. 분석 자동화에서는 DAG를 “분석 작업의 실행 지도” 정도로 이해하면 됩니다.

Airflow에서 자주 만나는 개념은 다음과 같습니다.

| 개념 | 의미 | 예시 |
| --- | --- | --- |
| DAG | 전체 작업 흐름 | 쇼핑몰 분석 파이프라인 |
| Task | DAG 안의 개별 실행 단위 | 전처리 실행, 보고서 생성 |
| Operator | Task를 실행하는 방식 | BashOperator, PythonOperator |
| Dependency | Task 사이의 실행 순서 | 전처리 후 분석 실행 |
| Schedule | DAG 실행 주기 | 매일 09시, 수동 실행 |

아래는 분석 스크립트들을 순서대로 실행하는 DAG 예시입니다. 실제 운영 환경에서는 경로와 실행 방식이 달라질 수 있으므로, 핵심 구조를 이해하는 데 집중하면 됩니다.

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from pathlib import Path
import csv

BASE_DIR = Path("/opt/airflow")
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"
FIGURE_DIR = REPORT_DIR / "figures"

REQUIRED_INPUT_FILES = [
    RAW_DIR / "orders.csv",
    RAW_DIR / "order_items.csv",
    RAW_DIR / "products.csv",
    RAW_DIR / "customers.csv",
]

REQUIRED_OUTPUT_FILES = [
    REPORT_DIR / "ch14_daily_sales.csv",
    REPORT_DIR / "ch14_airflow_report.md",
    FIGURE_DIR / "ch14_daily_sales.png",
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
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ch14_analysis_pipeline",
    description="온라인 쇼핑몰 분석 자동화 파이프라인",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["chapter14", "data-analysis", "pipeline"],
) as dag:

    check_input_files_task = PythonOperator(
        task_id="check_input_files",
        python_callable=check_input_files,
    )

    run_preprocessing = BashOperator(
        task_id="run_preprocessing",
        bash_command="python /opt/airflow/scripts/ch14_preprocessing.py",
    )

    run_analysis = BashOperator(
        task_id="run_analysis",
        bash_command="python /opt/airflow/scripts/ch14_analysis.py",
    )

    generate_visualizations = BashOperator(
        task_id="generate_visualizations",
        bash_command="python /opt/airflow/scripts/ch14_visualization.py",
    )

    generate_report = BashOperator(
        task_id="generate_report",
        bash_command="python /opt/airflow/scripts/ch14_report.py",
    )

    validate_outputs_task = PythonOperator(
        task_id="validate_outputs",
        python_callable=validate_outputs,
    )

    check_input_files_task >> run_preprocessing >> run_analysis >> generate_visualizations >> generate_report >> validate_outputs_task
```

이 코드에서 가장 중요한 부분은 마지막 줄입니다.

```python
check_input_files_task >> run_preprocessing >> run_analysis >> generate_visualizations >> generate_report >> validate_outputs_task
```

이 한 줄이 전체 분석 파이프라인의 실행 순서를 정의합니다.

## 7. Make와 n8n은 전달과 연결에 강하다

Airflow가 코드 기반 분석 파이프라인을 담당한다면, Make와 n8n은 결과물을 외부 서비스와 연결하는 데 유용합니다. 예를 들어 Airflow가 `reports/ch14_airflow_report.md`를 생성한 뒤, Make나 n8n이 해당 파일을 감지해 Gmail, Slack, Google Drive, Notion 등으로 전달할 수 있습니다.

자동화 흐름을 나누면 다음처럼 정리할 수 있습니다.

| 구간 | 담당 도구 예시 | 역할 |
| --- | --- | --- |
| 데이터 처리 | Python, Airflow | 전처리, 분석, 시각화, 보고서 생성 |
| 결과 검증 | Python, Airflow | 파일 생성 여부, 크기, 로그 확인 |
| 외부 전달 | Make, n8n | 메일 발송, Slack 알림, Drive 업로드 |
| 운영 확인 | Airflow UI, Make/n8n 실행 로그 | 실패 지점과 재실행 여부 확인 |

Make나 n8n에서 바로 모든 분석을 처리하려고 하면 복잡해질 수 있습니다. 반대로 Airflow에서 메일 발송과 외부 앱 연계까지 모두 처리하려고 해도 운영이 무거워질 수 있습니다. 분석 파이프라인과 외부 서비스 연결을 적절히 나누면 구조가 단순해집니다.

## 8. 결과 파일 검증이 자동화의 핵심이다

자동화에서 가장 위험한 상황은 “성공한 것처럼 보이지만 결과가 잘못된 경우”입니다. 코드가 오류 없이 끝났어도 보고서 파일이 비어 있거나, 그래프 이미지가 생성되지 않았거나, CSV에 행이 없을 수 있습니다.

따라서 자동화 흐름에는 결과 파일 검증이 반드시 포함되어야 합니다.

검증할 항목은 다음과 같습니다.

- 입력 CSV 파일이 존재하는가?
- 전처리 결과 파일이 생성되었는가?
- 분석 결과 CSV의 행 수가 0보다 큰가?
- 그래프 이미지 파일이 생성되었는가?
- 보고서 Markdown 파일이 생성되었는가?
- 파일 크기가 0이 아닌가?
- 실패 시 로그를 확인할 수 있는가?
- 보고서 발송 전에 최종 산출물이 모두 있는가?

<figure class="figure">
  <img src="../assets/images/ch14/ch14_pipeline_monitoring_retry_flow.png" alt="파이프라인 모니터링과 재시도 흐름">
  <figcaption>그림 14-4. 파이프라인 모니터링과 재시도 흐름</figcaption>
</figure>

자동화는 실행보다 검증이 더 중요합니다. 실행은 한 번 성공할 수 있지만, 검증이 없으면 실패를 늦게 발견하게 됩니다.

## 9. LLM과 함께 파이프라인을 설계한다

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

LLM이 만든 자동화 설계는 바로 믿지 말고 실제 프로젝트 구조와 비교해야 합니다. 특히 파일 경로, 실행 환경, Docker 볼륨, API 인증, 메일 발송 권한, 실제 컬럼명은 반드시 사람이 확인해야 합니다.

## 10. 자동화 결과를 해석하는 방법

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

## 11. 다음 장으로 이어지는 흐름

이 장에서는 반복되는 분석 흐름을 자동화하는 방법을 살펴보았습니다. Make, n8n, Airflow는 서로 경쟁하는 도구라기보다 각자 잘하는 영역이 다른 도구입니다. Make와 n8n은 외부 서비스 연결과 알림에 강하고, Airflow는 코드 기반 분석 파이프라인의 실행 순서와 상태 관리에 강합니다.

이제 데이터 분석의 기본 흐름, 머신러닝 모델링, LLM 코드 생성과 검증, 외부 데이터 수집, 자동화까지 경험했습니다. 다음 장에서는 이 모든 요소를 기말 프로젝트로 통합합니다. 기말 프로젝트에서는 EDA, 시각화, 머신러닝, LLM 활용, 외부 데이터 또는 자동화 아이디어를 하나의 분석 프로젝트 안에서 연결합니다.
