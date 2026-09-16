# 8장 실습. 작은 데이터 분석 프로젝트 완성하기

> 목표는 예쁜 보고서를 만드는 것이 아니라 **질문 → 원본 데이터 점검 → 전처리 → PK/FK 검증 → 안전한 병합 → 집계 → 총합 검증 → 시각화 → 해석 → 재실행**이 하나의 검증 가능한 흐름으로 연결되게 만드는 것입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter08/templates/chapter08_assignment.md`
- 주 제출물: `chapter08/chapter08.ipynb`

공식 Notebook:

```text
notebooks/ch08_midterm_project.ipynb
```

전체 재실행 스크립트:

```text
scripts/run_midterm_project.py
```

공통 프로젝트 로직:

```text
src/midterm_project.py
```

---

## STEP 0. 제출용 Notebook 준비

공식 Notebook을 개인 저장소의 다음 위치에 복사합니다.

```text
chapter08/chapter08.ipynb
```

외부 Evidence는 다음 폴더에 저장합니다.

```text
chapter08/images/
```

Notebook Kernel과 터미널의 Python 환경이 같은지 먼저 확인합니다.

---

## STEP 1. 프로젝트 질문과 계산 기준 고정

분석 질문 1~3개를 정하고 다음을 명시합니다.

```text
분석 대상
분석 범위
사용 데이터
사용 지표
완료 기준
```

금액성 분석의 기본 기준은 다음과 같습니다.

```text
order_status == "completed"
line_total = quantity × unit_price
```

`total_sales`라는 컬럼명이 있더라도 이번 프로젝트에서는 **completed 주문에 포함된 line_total 합계**라는 뜻으로 사용합니다. 회계상 순매출이라고 자동으로 해석하지 않습니다.

---

## STEP 2. 원본 데이터와 전처리 검증

Chapter 08 전체 프로젝트는 다음 원본 데이터 4종에서 다시 시작합니다.

```text
data/raw/customers.csv
data/raw/products.csv
data/raw/orders.csv
data/raw/order_items.csv
```

다음을 확인합니다.

- 파일 존재
- shape
- 컬럼
- 핵심 결측
- 전체 행 중복
- 전처리 전후 행 수

원본 파일을 직접 수정하지 않습니다.

---

## STEP 3. PK/FK Gate

주요 PK:

```text
customers.customer_id
products.product_id
orders.order_id
order_items.order_item_id
```

PK 성공 기준:

```text
missing_count == 0
duplicate_count == 0
status == PASS
```

주요 FK:

```text
orders.customer_id     → customers.customer_id
order_items.order_id   → orders.order_id
order_items.product_id → products.product_id
```

FK 미매칭이 있으면 후속 분석을 정상 완료로 처리하지 않습니다.

---

## STEP 4. 안전한 병합과 `line_total` 검증

병합에서는 다음을 함께 확인합니다.

```text
validate 관계
병합 전 행 수
병합 후 행 수
미매칭 행 수
PASS/FAIL
```

`left merge`라고 해서 항상 행 수가 유지되는 것은 아닙니다. 오른쪽 키가 중복되어 있으면 왼쪽 행이 증가할 수 있습니다.

또한 이미 `line_total` 컬럼이 있어도 다음 관계를 다시 확인합니다.

```text
line_total = quantity × unit_price
```

불일치가 있으면 금액 분석을 진행하지 않습니다.

---

## STEP 5. completed 범위와 주문 수 정의

금액성 분석은 다음 범위를 사용합니다.

```text
order_status == "completed"
```

주문 수는 주문 상세 행 수가 아니라 고유 주문 ID 수로 계산합니다.

```python
order_count=("order_id", "nunique")
```

다음은 서로 다릅니다.

```text
주문 상세 행 수
≠
주문 수
```

---

## STEP 6. 핵심 EDA 3개 수행

권장 결과:

```text
1. 카테고리별 completed 주문 기준 금액
2. 월별 completed 주문 기준 금액과 주문 수
3. completed 주문 기준 고객별 구매 금액
```

주문 상태별 주문 수는 **전체 orders**를 사용합니다.

각 결과 아래에 다음을 기록합니다.

```text
결과 관찰
나의 해석과 판단
업무·분석적 의미
한계
```

---

## STEP 7. Total consistency Gate

같은 completed source에서 만든 세 금액성 결과라면 다음 총합이 일치해야 합니다.

```text
completed source total
=
category total
=
monthly total
=
customer total
```

공식 프로젝트는 다음 Evidence를 저장합니다.

```text
reports/ch08_total_consistency_check.csv
```

값이 다르면 다음을 확인합니다.

- completed 필터 누락
- 병합 행 증식
- FK 미매칭
- category 결측
- 날짜 변환 실패
- 고객 연결 누락
- 서로 다른 실행 시점의 DataFrame 사용

값이 다르면 해석으로 넘어가지 않습니다.

---

## STEP 8. 날짜 Gate

월별 분석에는 유효한 `order_date`가 필요합니다.

공식 프로젝트는 다음 Evidence를 저장합니다.

```text
reports/ch08_date_checks.csv
```

completed 주문 중 날짜 오류가 있으면 월별 합계에서 금액이 빠질 수 있습니다.

```text
completed_total != monthly_total
```

날짜 오류를 조용히 제외한 상태를 정상 완료로 처리하지 않습니다.

---

## STEP 9. 공개 고객 결과 개인정보 Gate

내부 분석에는 `customer_id`가 필요할 수 있지만 공개 결과에는 남기지 않습니다.

공개 고객 CSV의 기본 컬럼:

```text
customer_label
city
order_count
total_sales
avg_order_value
```

공개 결과에서 제외:

```text
customer_id
name
email
phone
address
```

익명 라벨은 원본 ID를 붙이지 않고 순위 기반으로 생성합니다.

```text
Customer 01
Customer 02
Customer 03
```

저장된 `reports/ch08_customer_sales.csv`를 다시 읽어 금지 컬럼이 없는지 확인합니다.

---

## STEP 10. 대표 시각화 2~4개 작성

추천 그래프:

```text
카테고리별 completed 주문 기준 금액 → 막대그래프
월별 completed 주문 기준 금액 → 선그래프
상위 익명 고객 구매 금액 → 가로 막대그래프
```

그래프는 검증된 집계표에서 만듭니다.

각 그래프 아래에 다음을 작성합니다.

- 그래프 선택 이유
- 그래프와 원본 집계값 일치 여부
- 그래프에서 직접 관찰한 사실
- 그래프만으로 말할 수 없는 것

원인을 확인하지 못했다면 광고, 프로모션, 선호도, 수익성 등을 원인처럼 단정하지 않습니다.

---

## STEP 11. 최종 Validation 확인

공식 프로젝트는 다음 파일을 생성합니다.

```text
reports/ch08_project_validation.csv
```

대표 검증 항목:

```text
pk_integrity
fk_integrity
merge_checks_pass
line_total_consistency
completed_total_consistency
category_sales_ratio_pct_sum
completed_rows_with_invalid_order_date
public_customer_columns_safe
```

모든 핵심 항목이 `PASS`인지 확인합니다.

```text
FAIL 존재
→ 원인 확인
→ 수정
→ 전체 프로젝트 재실행
→ Validation 재확인
```

---

## STEP 12. LLM 보조 사용 기록

LLM을 사용했다면 다음을 남깁니다.

- 사용 목적
- Safe Context
- Prompt 요약
- LLM 제안
- 실제 반영 여부
- 사람이 수정한 내용
- 검증 근거

LLM에는 원본 고객 행이나 직접 식별정보를 제공하지 않습니다.

Safe Context 예:

```text
분석 질문
실제 컬럼 구조
completed 분석 범위
PK/FK 결과
병합 검증 결과
익명 집계 결과
total consistency 결과
최종 Validation 결과
```

LLM을 사용하지 않았다면 `미사용`과 이유를 기록합니다.

---

## STEP 13. 프로젝트 전체 재실행

Public 저장소 루트에서 실행합니다.

```powershell
python scripts/run_midterm_project.py
```

다음이 생성되는지 확인합니다.

```text
reports/ch08_dataset_summary.csv
reports/ch08_preprocessing_comparison.csv
reports/ch08_key_duplicate_checks.csv
reports/ch08_relationship_checks.csv
reports/ch08_merge_checks.csv
reports/ch08_line_total_check.csv
reports/ch08_date_checks.csv
reports/ch08_amount_scope_summary.csv
reports/ch08_total_consistency_check.csv
reports/ch08_project_validation.csv
reports/ch08_category_sales.csv
reports/ch08_monthly_sales.csv
reports/ch08_customer_sales.csv
reports/ch08_order_status_summary.csv
reports/ch08_interpretation_notes.csv
reports/figures/ch08_category_sales.png
reports/figures/ch08_monthly_sales.png
reports/figures/ch08_top_customers.png
reports/ch08_midterm_report.md
```

Notebook의 핵심 수치와 스크립트 결과가 같은 분석 범위를 사용하는지도 확인합니다.

---

## STEP 14. 최종 보고서 관점 정리

답안에 다음을 포함합니다.

1. 분석 질문
2. 데이터와 계산 범위
3. 전처리 검증
4. PK/FK·병합 검증
5. 핵심 EDA 결과
6. total consistency
7. 대표 시각화
8. 개인정보 검증
9. 핵심 인사이트
10. 업무·분석적 의미
11. 한계
12. 다음 분석 제안
13. LLM 활용 기록
14. 재현 방법
15. 최종 Validation

---

## 최종 제출 구조

```text
chapter08/
├─ chapter08.ipynb
└─ images/
   ├─ step02_data_validation.png
   ├─ graph01.png
   ├─ graph02.png
   └─ step06_reproduce.png
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter08/chapter08.ipynb
```

---

## 완료 체크

- [ ] 질문과 지표가 연결되어 있습니다.
- [ ] 원본 파일을 직접 수정하지 않았습니다.
- [ ] PK 결측·중복이 0건입니다.
- [ ] FK 미매칭이 0건입니다.
- [ ] 병합 관계·행 수·미매칭을 확인했습니다.
- [ ] `line_total = quantity × unit_price`가 일치합니다.
- [ ] 금액성 분석에 completed 범위를 사용했습니다.
- [ ] 주문 수를 `order_id.nunique()` 기준으로 계산했습니다.
- [ ] category/month/customer 총합이 source total과 일치합니다.
- [ ] completed 주문 날짜 오류가 0건입니다.
- [ ] 공개 고객 CSV에 원본 고객 ID와 직접 식별정보가 없습니다.
- [ ] 대표 그래프와 원본 집계값을 교차 확인했습니다.
- [ ] 관찰과 원인 가설을 구분했습니다.
- [ ] `ch08_project_validation.csv`가 모두 PASS입니다.
- [ ] 전체 스크립트를 다시 실행했습니다.
- [ ] Notebook과 스크립트의 핵심 수치가 일치합니다.
- [ ] 한계와 다음 분석을 작성했습니다.
- [ ] 최종 Notebook 파일 URL을 제출합니다.
