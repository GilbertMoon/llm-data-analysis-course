# ch14 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch14_airflow_pipeline.md`  
> **상태**: GPT 타당성 재검토 반영본

---

## 검토 지침

**[필수 수정]** = 실행 오류가 발생하거나 학습 흐름에 직접 혼란을 주는 항목  
**[보완 권장]** = 수정하면 실습 안정성 또는 학습 효과가 높아지는 항목  
**[참고/선택]** = 강의 운영 방식에 따라 선택적으로 반영할 수 있는 항목  
**[반영 제외]** = 현재 원문 기준으로 사실관계가 맞지 않거나 필수 오류로 보기 어려운 항목

---

## 0. GPT 타당성 재검토 결과 요약

| Claude 지적 | 재검토 판단 | 조정 결과 |
|---|---|---|
| `book/output/html/ch14_airflow_pipeline.html`에 ch09 내용이 있다는 긴급 오류 | 현재 저장소에서 해당 경로는 확인되지 않으며, `book/chapters/ch14_airflow_pipeline.html`은 ch14 제목으로 정상 생성되어 있음 | 긴급 오류에서 제외. 빌드 산출물 경로 정책 확인 항목으로 조정 |
| 수업 시간 합계와 본문 불일치 | 표 합계와 본문 기준 시간이 실제로 맞지 않음 | 필수 수정 유지 |
| 전처리 스크립트 `price` 컬럼 참조 | `order_items` 예시 구조와 맞지 않아 `KeyError` 가능성이 큼 | 필수 수정 유지 |
| 분석 스크립트 `price` 컬럼 참조 | `unit_price` 또는 `line_total` 사용이 더 일관적임 | 필수 수정 유지 |
| `to_csv()` 인코딩 없음 | Windows Excel 친화성 보완에는 타당하나 실행 오류는 아님 | 보완 권장으로 하향 |
| DAG의 `/opt/airflow` 경로 하드코딩 | 원문에 “자신의 Airflow 실행 환경에 맞게 조정” 안내가 이미 있음 | 필수에서 보완 권장으로 하향 |
| `write_text(encoding="utf-8")` BOM 없음 | Markdown 파일은 UTF-8 사용이 일반적이며 BOM 강제는 필수 아님 | 참고/선택으로 하향 |
| Notebook 파일 언급 없음 | ch14는 Airflow DAG와 스크립트 중심 실습이므로 Notebook 미사용 자체는 오류가 아님 | 보완 권장으로 하향 |
| `__file__` Notebook 실행 불가 | 스크립트형 실습이면 자연스럽지만 초보자 혼동 방지를 위해 안내하면 좋음 | 보완 권장 유지 |
| Airflow 설치 방법 미안내 | 실습 진입 장벽에 영향이 큼 | 보완 권장 중 높은 우선순위 유지 |
| 한글 폰트, 취소 주문, 채점 기준, 용어 정리 | 학습 품질 개선에는 유효하나 실행 필수 오류는 아님 | 참고/선택 또는 보완 권장으로 유지 |

---

## 1. 필수 수정 항목

---

### [1-1] 수업 시간 합계와 본문 불일치 — [수업 시간 구성]

**판단**: 필수 수정 유지

**근거**  
수업 시간 구성 표에서 연습 문제 60~90분을 제외해도 다음 합계가 나온다.

- 30 + 40 + 35 + 30 + 45 + 45 + 40 + 30 = 295분
- 295분 = 4시간 55분

그런데 본문에는 “기본 수업은 약 3시간을 기준으로 구성되어 있습니다”라고 되어 있다. Airflow 설치, DAG 실행, 로그 확인까지 포함되는 장의 특성을 고려하면 3시간 기준과 표 구성이 맞지 않는다.

**수정 방향**

- 방법 A: 본문을 “기본 수업은 약 5시간을 기준으로 구성되어 있습니다”로 수정한다.
- 방법 B: 표의 각 항목 시간을 줄여 180분 내외로 재구성한다.
- 방법 C: “3시간 압축 운영안”과 “5시간 실습 확장안”을 분리한다.

**권장**  
ch14는 Airflow 실행 환경 준비가 포함되므로 방법 C가 가장 적절하다.

---

### [1-2] 전처리 스크립트에서 `price` 컬럼 참조 오류 — [섹션 7.1]

**판단**: 필수 수정 유지

**문제**  
전처리 스크립트에서 다음 코드가 사용된다.

```python
order_items = order_items.dropna(subset=["order_id", "product_id", "quantity", "price"])
```

그러나 기존 장의 주문 상세 데이터 구조는 일반적으로 다음 컬럼을 사용한다.

```text
order_id, product_id, quantity, unit_price, line_total
```

`price`는 상품 테이블의 가격 컬럼으로 사용되는 경우가 많고, `order_items`에서는 `unit_price` 또는 `line_total`을 기준으로 처리하는 편이 자연스럽다. 이 상태로 실행하면 `KeyError`가 발생할 가능성이 높다.

**수정 방향**

```python
order_items = order_items.dropna(
    subset=["order_id", "product_id", "quantity", "unit_price"]
)
```

추가로 `line_total`이 없을 때만 계산하도록 안내하면 더 안정적이다.

```python
if "line_total" not in order_items.columns:
    order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]
```

---

### [1-3] 분석 스크립트에서 `price` 컬럼 참조 오류 — [섹션 7.2]

**판단**: 필수 수정 유지

**문제**  
분석 스크립트에서 다음 코드가 사용된다.

```python
order_items["sales"] = order_items["quantity"] * order_items["price"]
```

`order_items_clean.csv`가 `unit_price` 또는 `line_total` 구조라면 `price` 컬럼이 없어 오류가 발생한다.

**수정 방향**

가장 단순한 수정은 다음과 같다.

```python
order_items["sales"] = order_items["quantity"] * order_items["unit_price"]
```

다만 전처리 단계에서 이미 `line_total`을 생성했다면 다음 방식이 더 일관적이다.

```python
order_items["sales"] = order_items["line_total"]
```

**권장**  
학생 혼동을 줄이려면 ch14 전체에서 매출 기준 컬럼명을 하나로 통일한다.

- 원본 주문 상세: `unit_price`, `quantity`
- 전처리 산출: `line_total`
- 분석 산출: `sales`

---

## 2. 보완 권장 항목

---

### [2-1] `to_csv()` 저장 시 인코딩 안내 — [섹션 7.1, 7.2]

**판단**: 필수에서 보완 권장으로 하향

**이유**  
`encoding="utf-8-sig"`는 Windows Excel에서 한글 CSV를 열 때 유용하지만, pandas 실행 자체를 막는 오류는 아니다. 따라서 “필수 수정”보다는 “Windows Excel 사용자를 위한 보완”으로 보는 것이 적절하다.

**보완 방향**

```python
orders.to_csv(PROCESSED_DIR / "orders_clean.csv", index=False, encoding="utf-8-sig")
order_items.to_csv(PROCESSED_DIR / "order_items_clean.csv", index=False, encoding="utf-8-sig")
products.to_csv(PROCESSED_DIR / "products_clean.csv", index=False, encoding="utf-8-sig")
customers.to_csv(PROCESSED_DIR / "customers_clean.csv", index=False, encoding="utf-8-sig")
daily_sales.to_csv(REPORT_DIR / "ch14_daily_sales.csv", index=False, encoding="utf-8-sig")
```

---

### [2-2] DAG의 `/opt/airflow` 경로 하드코딩 설명 보완 — [섹션 7.5]

**판단**: 필수에서 보완 권장으로 하향

**이유**  
원문에는 “학습자는 경로를 자신의 Airflow 실행 환경에 맞게 조정해야 합니다”라는 설명이 이미 있다. 따라서 완전 누락은 아니다. 다만 초보자에게는 `/opt/airflow`가 Docker 컨테이너 내부 경로라는 점이 낯설 수 있으므로 주석을 추가하면 좋다.

**보완 방향**

```python
# BASE_DIR은 Airflow 컨테이너 내부의 작업 경로입니다.
# Docker Compose에서 현재 프로젝트 폴더를 /opt/airflow로 마운트한 경우에 사용합니다.
# 자신의 환경에서 마운트 경로가 다르면 이 값을 수정해야 합니다.
BASE_DIR = Path("/opt/airflow")
```

---

### [2-3] ch14 Notebook 활용 방식 안내 — [전체]

**판단**: 필수에서 보완 권장으로 하향

**이유**  
ch14는 Notebook 중심 장이 아니라 Airflow DAG와 독립 Python 스크립트 중심 장이다. 따라서 Notebook 언급이 없다고 해서 반드시 오류는 아니다. 다만 저장소에 `notebooks/ch14_airflow_pipeline.ipynb`가 있다면, 학생이 어떤 용도로 사용해야 하는지 한 줄 안내가 있으면 좋다.

**보완 방향**

```markdown
이번 장은 Airflow DAG와 Python 스크립트 중심 실습입니다.
`notebooks/ch14_airflow_pipeline.ipynb`는 개념 확인과 코드 조각 테스트용으로 사용할 수 있으며,
실제 DAG 실행은 Airflow 환경에서 진행합니다.
```

---

### [2-4] Airflow 실행 환경 안내 보완 — [섹션 5.2]

**판단**: 보완 권장 유지, 우선순위 높음

**이유**  
Airflow는 pandas, matplotlib처럼 단순 `pip install`만으로 끝내기 어려운 경우가 많다. Docker Compose 기반 실습 환경을 제공한다면, 교재에서 해당 폴더와 실행 절차를 명확히 안내하는 것이 좋다.

**보완 방향**

```markdown
이 교재에서는 Docker Compose 기반 Airflow 환경 사용을 권장합니다.
실습 환경이 제공된 경우 `automation/airflow/` 폴더의 안내에 따라 Airflow를 실행합니다.

DAG 파일은 Airflow의 `dags/` 폴더에 위치해야 하며,
`ch14_analysis_pipeline_dag.py`를 해당 폴더에 배치하면 Web UI에서 확인할 수 있습니다.
```

---

### [2-5] `__file__` 사용 코드의 실행 위치 안내 — [섹션 7.1~7.4]

**판단**: 보완 권장 유지

**이유**  
`Path(__file__).resolve().parents[1]`는 `.py` 파일 실행에는 적절하지만, Notebook 셀에서 그대로 실행하면 `__file__`이 정의되지 않아 오류가 발생한다. ch14가 스크립트 중심 장이라는 점을 명확히 안내하면 된다.

**보완 방향**

```python
# 이 코드는 Notebook 셀이 아니라 .py 스크립트 파일로 실행하는 것을 전제로 합니다.
# 예: python scripts/ch14_preprocessing.py
BASE_DIR = Path(__file__).resolve().parents[1]
```

---

### [2-6] 취소 주문 처리 기준 안내 — [섹션 7.2]

**판단**: 보완 권장 유지

**이유**  
취소 주문 포함 여부는 분석 목적에 따라 달라진다. 모든 장에서 무조건 제외해야 하는 것은 아니지만, 매출 분석에서는 기준을 명시하는 것이 좋다.

**보완 방향**

```python
print("주문 상태 분포:")
print(orders["order_status"].value_counts())

# 매출 분석에서 취소 주문을 제외하려면 아래 조건을 사용합니다.
# orders = orders[orders["order_status"] != "cancelled"]
```

---

## 3. 참고/선택 보완 항목

---

### [3-1] `write_text(encoding="utf-8")`를 `utf-8-sig`로 강제 변경

**판단**: 참고/선택으로 하향

**이유**  
Markdown 파일은 UTF-8 저장이 일반적이며, BOM이 반드시 필요한 것은 아니다. Excel에서 직접 여는 CSV와 달리 Markdown 보고서 파일은 `utf-8` 유지가 더 자연스럽다. Windows 메모장 호환성까지 고려할 때만 `utf-8-sig`를 선택하면 된다.

---

### [3-2] 시각화 스크립트 한글 폰트 안내

**판단**: 참고/선택 유지

**이유**  
현재 그래프 제목과 축 라벨이 영문이므로 한글 폰트 설정이 없어도 실행 오류가 발생하지 않는다. 한글 제목으로 바꿀 경우에만 ch07의 폰트 설정 안내를 참고하도록 연결하면 충분하다.

---

### [3-3] 연습 문제 채점 기준 추가

**판단**: 참고/선택 유지

**이유**  
ch14 연습 문제는 기본, 실습, 심화로 이미 구조화되어 있다. 채점 기준을 추가하면 과제 운영에는 도움이 되지만, 본문 실행 오류는 아니다.

---

### [3-4] 핵심 용어 정리 섹션 추가

**판단**: 참고/선택 유지

**이유**  
DAG, Task, Operator, Dependency, Schedule은 본문 3.2에서 이미 표로 설명되어 있다. 별도 용어 정리 표는 복습용으로는 좋지만 필수 누락은 아니다.

---

### [3-5] `book/output/html/ch14_airflow_pipeline.html` 긴급 오류 지적

**판단**: 현재 기준 반영 제외 또는 별도 빌드 산출물 확인

**이유**  
리뷰 원문은 `book/output/html/ch14_airflow_pipeline.html`에 ch09 내용이 들어 있다고 지적했으나, 현재 저장소에서는 해당 경로가 확인되지 않는다. 반면 `book/chapters/ch14_airflow_pipeline.html`은 ch14 제목으로 정상 생성되어 있다.

따라서 이 항목은 현재 `ch14_review.md`의 필수 수정 사항으로 유지하기보다, 빌드 스크립트가 실제로 어느 경로에 HTML을 생성해야 하는지 확인하는 별도 관리 항목으로 분리하는 것이 적절하다.

---

## 4. 최종 우선순위 요약

| 우선순위 | 항목 | 최종 분류 |
|---|---|---|
| 🔴 높음 | [1-2] 전처리 스크립트 `price` 컬럼 참조 오류 | 필수 수정 |
| 🔴 높음 | [1-3] 분석 스크립트 `price` 컬럼 참조 오류 | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계와 본문 기준 불일치 | 필수 수정 |
| 🟠 중간 | [2-4] Airflow 실행 환경/Docker Compose 안내 보완 | 보완 권장 |
| 🟠 중간 | [2-2] `/opt/airflow` 경로 의미와 수정 기준 안내 | 보완 권장 |
| 🟡 보완 | [2-3] ch14 Notebook 활용 방식 안내 | 보완 권장 |
| 🟡 보완 | [2-5] `__file__` 사용 코드 실행 위치 안내 | 보완 권장 |
| 🟡 보완 | [2-6] 취소 주문 처리 기준 안내 | 보완 권장 |
| 🟢 참고 | CSV 인코딩, Markdown BOM, 한글 폰트, 채점 기준, 용어 정리 | 참고/선택 |
| ⚪ 별도 확인 | `book/output/html/` 빌드 산출물 경로 정책 | 별도 관리 |

---

## 5. 전반적 평가

ch14는 Chapter 13의 Make 자동화에서 한 단계 더 나아가, 데이터 분석 파이프라인을 Airflow DAG와 Task 단위로 운영하는 흐름을 잘 설명하고 있다. 특히 Python 분석 스크립트와 Airflow DAG의 역할 분담, Task 의존성, 실패 재시도, 결과 파일 검증 Task를 함께 다룬 점은 실무형 강의에 적합하다.

다만 현재 본문 코드에는 `price` 컬럼 참조 오류가 두 군데 있어 실제 실습 실행 시 바로 실패할 수 있다. 이 부분은 반드시 `unit_price` 또는 `line_total` 기준으로 통일해야 한다. Airflow 실행 환경은 초보자에게 진입 장벽이 높으므로 Docker Compose 기반 환경, `/opt/airflow` 경로 의미, `.py` 스크립트 실행 위치를 더 분명히 안내하면 학습 안정성이 크게 높아진다.
