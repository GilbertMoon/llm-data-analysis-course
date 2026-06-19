# ch14 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch14_airflow_pipeline.md`

---

## ⚠️ 긴급 빌드 오류 — ch14 HTML 파일 내용 오류

**현상**  
`book/output/html/ch14_airflow_pipeline.html` 파일을 열면 ch14 Airflow 강의 내용이 아닌 **ch09 HTML 검수 요청 프롬프트**가 그대로 들어 있다:

```
첨부된 ch09_llm_prompt_analysis.html, ch09_llm_prompt_analysis.md, 
ch09_llm_prompt_analysis_images.md를 기준으로 Chapter 9 HTML 파일을 최종 검수하고 보완해 주세요.
```

이는 `scripts/build_book_html.py` 실행 시 ch14 소스가 아닌 잘못된 파일이 입력으로 사용되었거나, 이전 빌드 결과가 덮어쓰여졌음을 의미한다.

**즉각 조치 필요**  
```bash
# HTML 재빌드
python scripts/build_book_html.py
# 또는 ch14만 개별 재빌드
```
재빌드 후 `ch14_airflow_pipeline.html`의 `<title>` 태그가 "14장 Airflow 기반 데이터 분석 파이프라인"인지 확인한다.

이하 검토는 **Markdown 소스 `ch14_airflow_pipeline.md` 기준**으로 작성되었다.

---

## 검토 지침 (Codex Prompt Format)

**[필수 수정]** = 학습에 직접적 혼란을 야기하는 항목  
**[보완 권장]** = 추가 시 학습 효과가 크게 향상되는 항목

---

## 1. 필수 수정 항목

---

### [1-1] 수업 시간 합계와 본문 불일치 — [수업 시간 구성 표]

**문제**  
수업 시간 구성 표 합계 (연습 문제 60~90분 제외):  
30+40+35+30+45+45+40+30 = **295분 = 4시간 55분**  
본문: "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"  
약 2시간 격차. ch01~ch14 전 장 반복 문제.

**수정 지시**  
방법 A: 각 항목 시간을 줄여 합계 180분 이내로 재편성한다.  
방법 B: 본문을 "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"로 수정한다.

---

### [1-2] 전처리 스크립트에서 `price` 컬럼 참조 오류 — [섹션 7.1]

**문제**  
섹션 7.1 전처리 스크립트에서:
```python
order_items = order_items.dropna(subset=["order_id", "product_id", "quantity", "price"])
```
실제 `order_items_clean.csv` / `order_items.csv`의 컬럼은 `order_id, product_id, quantity, unit_price, line_total`이다. `price` 컬럼은 `products` 테이블에 있으므로 `KeyError`가 발생한다.

**수정 지시**  
```python
# 수정 전
order_items = order_items.dropna(subset=["order_id", "product_id", "quantity", "price"])

# 수정 후
order_items = order_items.dropna(subset=["order_id", "product_id", "quantity", "unit_price"])
```

---

### [1-3] 분석 스크립트에서 `price` 컬럼 참조 오류 — [섹션 7.2]

**문제**  
섹션 7.2 분석 스크립트에서:
```python
order_items["sales"] = order_items["quantity"] * order_items["price"]
```
`order_items`에는 `price` 컬럼이 없다. `unit_price` 컬럼을 사용해야 하며, 이미 전처리된 데이터라면 `line_total`을 그대로 사용하는 것이 더 일관성 있다.

**수정 지시**  
선택 A — `unit_price` 사용:
```python
order_items["sales"] = order_items["quantity"] * order_items["unit_price"]
```

선택 B — 이미 계산된 `line_total` 사용:
```python
# line_total이 이미 quantity * unit_price 결과이므로 바로 사용
# order_items["sales"] = order_items["line_total"]  # 컬럼 이름만 달리함
daily_sales = (
    merged.assign(order_day=merged["order_date"].dt.date)
    .groupby("order_day", as_index=False)["line_total"]
    .sum()
    .sort_values("order_day")
)
```

선택 B가 전처리된 데이터의 `line_total`을 재계산 없이 활용하므로 더 일관성 있다.

---

### [1-4] `to_csv()` 저장에 인코딩 없음 — [섹션 7.1, 7.2]

**문제**  
섹션 7.1에서 4개 CSV 저장(`orders_clean.csv`, `order_items_clean.csv`, `products_clean.csv`, `customers_clean.csv`), 섹션 7.2에서 `ch14_daily_sales.csv` 저장 — 모두 `encoding` 없음. 한글 데이터가 포함된 경우 Windows Excel에서 깨진다.

**수정 지시**  
```python
# 섹션 7.1
orders.to_csv(PROCESSED_DIR / "orders_clean.csv", index=False, encoding="utf-8-sig")
order_items.to_csv(PROCESSED_DIR / "order_items_clean.csv", index=False, encoding="utf-8-sig")
products.to_csv(PROCESSED_DIR / "products_clean.csv", index=False, encoding="utf-8-sig")
customers.to_csv(PROCESSED_DIR / "customers_clean.csv", index=False, encoding="utf-8-sig")

# 섹션 7.2
daily_sales.to_csv(REPORT_DIR / "ch14_daily_sales.csv", index=False, encoding="utf-8-sig")
```

---

### [1-5] DAG에서 `/opt/airflow` 경로 하드코딩 — [섹션 7.5]

**문제**  
DAG 파일에서 경로를 다음처럼 하드코딩했다:
```python
BASE_DIR = Path("/opt/airflow")
```
Docker 컨테이너 기반 Airflow 환경(공식 이미지 기본 경로)을 전제로 하는데, 다른 설정의 Docker 이미지나 로컬 Airflow 설치 환경에서는 경로가 다를 수 있다. 학생이 경로를 변경해야 함을 설명하지 않는다.

**수정 지시**  
코드 앞에 다음 주석을 추가한다:

```python
# ⚠️ BASE_DIR은 Airflow 컨테이너의 마운트 경로에 맞게 수정해야 합니다.
# Docker Compose 환경에서 volumes에 설정한 마운트 경로를 사용하세요.
# 예: docker-compose.yml에서 - ./:/opt/airflow 로 마운트한 경우 Path("/opt/airflow")
# 예: Windows 환경에서 직접 설치한 경우 Path("C:/Users/계정명/airflow")
BASE_DIR = Path("/opt/airflow")
```

또한 `automation/airflow/docker-compose.yml`이 workspace에 이미 존재하므로, 교재 섹션 5.2에서 이 파일을 명시적으로 참조한다.

---

### [1-6] 보고서 `write_text(encoding="utf-8")` — BOM 없음 — [섹션 7.4]

**문제**  
섹션 7.4 보고서 생성 스크립트에서:
```python
(REPORT_DIR / "ch14_airflow_report.md").write_text(report_text, encoding="utf-8")
```
ch12 [1-7], ch13 [1-4]와 동일한 문제.

**수정 지시**  
```python
# 수정 전
(REPORT_DIR / "ch14_airflow_report.md").write_text(report_text, encoding="utf-8")

# 수정 후
(REPORT_DIR / "ch14_airflow_report.md").write_text(report_text, encoding="utf-8-sig")
```

---

### [1-7] Notebook 파일 언급 없음 — [섹션 전체]

**문제**  
`notebooks/ch14_airflow_pipeline.ipynb`가 workspace에 존재하지만, ch14 강의안에서 이 Notebook을 언급하지 않는다. 대신 `scripts/ch14_*.py`와 `dags/` 파일 중심으로 실습이 진행된다. 

다른 장들은 "이번 장의 전체 실습은 다음 Notebook에서 진행합니다"라고 명시하는데, ch14만 Notebook 언급이 없어 학생이 ch14 Notebook을 어떻게 활용해야 하는지 알 수 없다.

**수정 지시**  
두 가지 선택지:

선택 A — Notebook을 실습 탐색 용도로 명시:
```markdown
이번 장의 개념 탐색과 스크립트 테스트는 다음 Notebook에서 진행할 수 있습니다.

notebooks/ch14_airflow_pipeline.ipynb

단, 실제 Airflow DAG 실행은 Notebook이 아닌 Airflow 환경에서 진행합니다.
```

선택 B — Notebook 파일을 ch14 실습과 무관하게 처리하고, `notebooks/` 폴더 설명에 "ch14는 Airflow 환경 기반 실습이므로 Notebook 대신 scripts/와 dags/ 파일을 사용합니다"를 명시한다.

---

## 2. 보완 권장 항목

---

### [2-1] `__file__` 사용 — Notebook에서 실행 불가 — [섹션 7.1~7.4]

**문제**  
섹션 7.1~7.4의 Python 스크립트에서 `Path(__file__).resolve().parents[1]`로 `BASE_DIR`을 설정한다. 이 코드는 `.py` 파일로 실행할 때는 정상 동작하지만, Notebook에서 직접 셀로 실행하면 `NameError: name '__file__' is not defined`가 발생한다.

**보완 지시**  
스크립트 파일 앞에 다음 주석을 추가한다:

```python
# 이 스크립트는 python scripts/ch14_preprocessing.py 명령으로 실행하세요.
# Notebook 셀에서 직접 실행하면 __file__이 정의되지 않아 오류가 발생합니다.
# Notebook에서 테스트하려면 BASE_DIR을 직접 설정하세요:
# BASE_DIR = Path("..")  # notebooks/ 폴더에서 실행 시
```

---

### [2-2] Airflow 설치 방법 미안내 — [섹션 5.2]

**문제**  
섹션 5.2에서 Docker 기반 Airflow 환경이나 강사 준비 환경을 언급하지만, 실제 설치 방법 안내가 없다. workspace에 이미 `automation/airflow/docker-compose.yml`이 존재하는데 교재에서 이를 참조하지 않는다.

**보완 지시**  
섹션 5.2에 다음 안내를 추가한다:

```markdown
## Airflow Docker 환경 실행

이 교재에서는 Docker Compose를 사용해 Airflow를 실행합니다.

```bash
# automation/airflow/ 폴더로 이동
cd automation/airflow

# Airflow 초기화 (최초 1회)
docker compose up airflow-init

# Airflow 시작
docker compose up -d

# Airflow Web UI 접속
# http://localhost:8080 (기본 계정: airflow / airflow)
```

📁 DAG 파일 위치: `automation/airflow/dags/`
📁 이 폴더에 `ch14_analysis_pipeline_dag.py`를 복사하면 Airflow가 자동으로 인식합니다.
```

---

### [2-3] 시각화 스크립트에서 한글 폰트 미설정 — [섹션 7.3]

**문제**  
섹션 7.3에서 그래프 제목이 영문("Daily Sales")으로 작성되어 있다. 한글 제목으로 변경하면 ch07에서 지적한 한글 폰트 문제(`Malgun Gothic` 하드코딩)가 발생할 수 있다. 현재 영문으로 두는 것은 실용적이지만, 교재 전반에서 한글 폰트 처리 방법을 일관되게 제시하지 않는다는 문제가 있다.

**보완 지시**  
섹션 7.3 상단에 다음 안내를 추가한다:

```python
# 그래프 제목은 영문으로 설정합니다.
# 한글 제목을 사용하려면 ch07에서 다룬 폰트 설정이 필요합니다.
# Windows: plt.rc("font", family="Malgun Gothic")
# macOS: plt.rc("font", family="AppleGothic")
```

---

### [2-4] 취소 주문 처리 기준 언급 없음 — [섹션 7.1, 7.2]

**문제**  
ch06~ch13에서 반복 언급된 취소 주문 처리 기준이 ch14 분석 스크립트(섹션 7.2)에서도 없다. `daily_sales` 집계 시 `order_status = 'cancelled'` 필터링이 없으면 취소 주문도 매출로 계산된다.

**보완 지시**  
섹션 7.2 `daily_sales` 집계 전에 다음 코드를 추가한다:

```python
# 주문 상태 확인
print("주문 상태 분포:")
print(orders["order_status"].value_counts())

# 매출 분석에 포함할 주문 상태를 결정합니다.
# 취소 주문을 제외하려면 아래 줄의 주석을 해제하세요.
# orders = orders[orders["order_status"] != "cancelled"]
```

---

### [2-5] 연습 문제 힌트/채점 기준 없음 — [섹션 11]

**문제**  
ch01~ch13과 동일. ch14는 기본 문제(11.1), 실습 문제(11.2), 심화 문제(11.3)로 3단계로 구분되어 있어 다른 장보다 잘 구조화되어 있다. 그러나 각 문제에 채점 기준이 없다.

**보완 지시**  
심화 문제 평가 기준 예시:

```
평가 기준 (Airflow 파이프라인 개선안):
- 원본 데이터 없을 때 이후 Task 실행 방지 로직이 있는가? (20%)
- 분석 결과 행 수 0 조건이 구현되었는가? (20%)
- 결과 파일 검증 Task가 포함되었는가? (20%)
- Make 연계 조건이 검증 통과 후에 연결되는가? (20%)
- 로그 기록 및 운영 문서 작성이 포함되었는가? (20%)
```

---

### [2-6] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch13과 동일. ch14 신규 용어: DAG(Directed Acyclic Graph), Task, BashOperator, PythonOperator, Dependency, Schedule, catchup, retries, retry_delay, 파이프라인, 파이프라인 모니터링.

**보완 지시**  
섹션 12(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| DAG | 유향 비순환 그래프. Airflow에서 전체 작업 흐름을 정의 |
| Task | DAG 안의 개별 실행 단위 |
| BashOperator | 셸 명령을 실행하는 Operator |
| PythonOperator | Python 함수를 실행하는 Operator |
| Dependency | Task 실행 순서를 정의하는 `>>` 연산자 |
| Schedule | DAG 실행 주기 (`@daily`, cron 등) |
| catchup | 과거 미실행 DAG 자동 실행 여부 |
| retries | 실패 시 재시도 횟수 |
| retry_delay | 재시도 전 대기 시간 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🚨 긴급 | [빌드 오류] `ch14_airflow_pipeline.html`에 ch09 내용이 들어 있음 | 즉각 수정 |
| 🔴 높음 | [1-2] 전처리 스크립트 `price` 컬럼 참조 오류 → `KeyError` 발생 | 필수 수정 |
| 🔴 높음 | [1-3] 분석 스크립트 `price` 컬럼 참조 오류 → `KeyError` 발생 | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (295분 vs "약 3시간") | 필수 수정 |
| 🟠 중간 | [1-4] `to_csv()` 인코딩 5회 누락 | 필수 수정 |
| 🟠 중간 | [1-5] DAG 경로 하드코딩 미설명 | 필수 수정 |
| 🟠 중간 | [1-7] Notebook 파일 활용 방법 미안내 | 필수 수정 |
| 🟡 낮음 | [1-6] `write_text(encoding="utf-8")` BOM 없음 (반복) | 필수 수정 |
| 🔴 높음 | [2-2] Airflow Docker 환경 설치 방법 미안내 | 보완 권장 |
| 🟢 권장 | [2-1] `__file__` 사용 — Notebook 실행 불가 경고 없음 | 보완 권장 |
| 🟢 권장 | [2-4] 취소 주문 처리 기준 없음 (ch06~ch14 반복) | 보완 권장 |
| 🟢 참고 | [2-3] 시각화 한글 폰트 미설정 | 보완 권장 |
| 🟢 참고 | [2-5] 연습 문제 채점 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-6] 핵심 용어 정리 섹션 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 섹션 3.2의 DAG/Task/Operator/Dependency/Schedule 5개 개념을 표 하나로 명확히 정의한 것이 탁월하다.
- 섹션 3.3의 Python 분석 스크립트 vs Airflow DAG 역할 분담 표가 ch13의 Python vs Make 역할 표와 유사한 구조로 일관성 있게 확장되었다.
- 섹션 7.5 DAG 코드에서 `_check_input_files`와 `_validate_outputs` 함수를 PythonOperator에 연결해 검증 로직이 DAG 안에 직접 통합된 것이 실용적이다.
- 섹션 7.5의 Task 의존성 `>>` 한 줄이 전체 파이프라인을 표현한 패턴(`check_input_files >> ... >> validate_outputs`)이 비전공자에게 Airflow 개념을 직관적으로 전달한다.
- 연습 문제가 기본(11.1), 실습(11.2), 심화(11.3) 3단계로 구분된 것이 다른 장보다 잘 구조화되어 있다.
- 섹션 9의 결과 해석 표에서 "Airflow UI의 DAG Runs, Graph, Log"를 구체적으로 참조한 것이 실습 후 확인 방법을 명확히 안내한다.

**전체적 방향 제안**  
ch14는 ch13에서 Make로 외부 앱 연계를 배운 학생이 더 강력한 파이프라인 도구인 Airflow로 자연스럽게 진화하는 구성이 잘 설계되어 있다. 가장 긴급한 두 가지 이슈는 **(1) HTML 빌드 오류** — 즉시 재빌드가 필요하다 **(2) `price` 컬럼 참조 오류** — 전처리/분석 스크립트 2개 모두에서 `KeyError`가 발생하므로 학생이 DAG를 실행하면 첫 실습부터 실패한다. 이 두 가지를 수정하면 ch14의 학습 경험이 크게 향상된다. `automation/airflow/docker-compose.yml`이 이미 workspace에 존재하므로 교재에서 명시적으로 참조하면 Airflow 설치 진입 장벽을 크게 낮출 수 있다.
