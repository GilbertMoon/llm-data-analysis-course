# 15장 실습. 하나의 데이터 분석 프로젝트로 완성하기

> 목표는 기능을 많이 넣는 것이 아니라 **하나의 질문을 기준으로 데이터 범위·검증 Evidence·선택 단계·재현성·Manifest·Submission Gate를 끝까지 연결하는 것**입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter15/templates/chapter15_assignment.md`
- 주 제출물: `chapter15/chapter15.ipynb`

공식 Notebook:

```text
notebooks/ch15_final_project.ipynb
```

보조 스크립트:

```text
scripts/run_final_project.py
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 `chapter15/chapter15.ipynb`로 사용합니다. Validation·Manifest·Submission Status 등 Notebook 밖 Evidence는 필요하면 `chapter15/images/`에 저장합니다.

## STEP 1. 프로젝트 질문과 계산 범위 고정
프로젝트 질문을 한 문장으로 작성합니다.

기본 금액성 EDA 범위:

```text
order_status == completed
line_total = quantity × unit_price
표현 = completed 주문 기준 금액
```

이 값은 할인·배송비·세금·부분 환불·정산 시점을 모두 반영한 회계상 순매출이라고 단정하지 않습니다.

답안에 작성:
- 분석 질문
- 계산 범위
- 필수 단계
- 선택 단계
- 제출 완료 기준

## STEP 2. 전체 Final Project 실행
프로젝트 루트에서 실행합니다.

```powershell
python scripts/generate_sample_data.py
python scripts/run_final_project.py
```

실행 결과의 첫 확인 대상은 **Submission Status**입니다.

```text
READY
READY_WITH_WARNINGS
BLOCKED
```

`BLOCKED`이면 산출물이 많이 생성되었더라도 제출 완료 상태가 아닙니다.

## STEP 3. Project Run ID 기록
이번 실행의 `project_run_id`를 기록합니다.

예:

```text
ch15-YYYYMMDDTHHMMSSZ-xxxxxxxx
```

다음 Evidence가 같은 실행에 속하는지 확인합니다.

```text
ch15_project_validation.csv
ch15_project_run_metadata.csv
ch15_reproducibility_manifest.csv
ch15_final_report.md
ch15_project_deliverables.csv
ch15_submission_status.csv
```

Project Run ID는 Airflow Dag Run ID나 업무 데이터 기간과 같은 개념이 아닙니다.

## STEP 4. 데이터 구조와 PK/FK 검증
다음을 확인합니다.

```text
customers.customer_id
products.product_id
orders.order_id
order_items.order_item_id
```

관계:

```text
orders.customer_id → customers.customer_id
order_items.order_id → orders.order_id
order_items.product_id → products.product_id
```

merge 전후 행 수와 미매칭 key도 확인합니다.

필수 키·관계 오류는 경고만 남기고 계속 진행하는 항목이 아닙니다.

## STEP 5. completed 금액 총합 불변식 검증
핵심 불변식:

```text
completed source total
= category total
= monthly total
= customer total
= product total
```

같은 범위를 집계했다면 모두 일치해야 합니다.

불일치 시 확인 순서:

```text
completed 필터
→ line_total 계산
→ 날짜 변환
→ merge 중복/누락
→ groupby 범위
→ 오래된 산출물 여부
```

총합 불일치는 필수 Core `FAIL`입니다.

## STEP 6. EDA와 시각화 해석
최종 질문에 직접 연결되는 결과를 선택합니다.

대표 결과:

```text
category_sales
monthly_sales
customer_sales
product_sales
order_status_summary
```

각 결과에는 다음을 작성합니다.

```text
수치/그래프
→ 관찰
→ 해석과 판단
→ 업무·분석적 의미
→ 한계
```

금액성 그래프는 completed 범위를 유지하고, 주문 상태 분포는 전체 주문 범위를 사용할 수 있습니다. 지표 이름은 범위를 섞어 사용하지 않습니다.

## STEP 7. 공개 고객 결과 개인정보 점검
공개 고객 결과에는 기본적으로 다음 컬럼을 포함하지 않습니다.

```text
customer_id
name
email
phone
address
city
```

`Customer 01` 같은 익명 라벨을 사용합니다.

도시처럼 직접 식별자가 아니더라도 작은 집단이나 다른 속성과 결합하면 재식별 위험이 생길 수 있으므로 공개 결과에서는 더 보수적으로 최소화합니다.

## STEP 8. 선택 단계 — 주문 취소 분류
분류는 목적과 데이터가 충분할 때만 사용합니다.

계약:

```text
completed → 0
cancelled → 1
refunded 등 → 제외
```

확인할 것:
- prediction-time feature만 사용
- target/식별자/사후정보 제외
- Dummy baseline 포함
- train/validation/test 분리
- validation에서 모델 선택
- validation에서 threshold 선택
- 고정 후 final test 1회 평가
- 공개 prediction에 원본 식별자 없음

데이터 부족이면 `skipped`로 기록할 수 있습니다. 선택 단계의 계약 오류는 `warning`으로 남기고 그 결과를 핵심 결론 근거로 사용하지 않습니다.

## STEP 9. 선택 단계 — 외부 데이터
실제 파일:

```text
data/external/processed/holidays.csv
```

필수 데이터 컬럼:

```text
date
holiday_name
is_holiday
```

필수 provenance:

```text
provider
source_url
data_reference_date
license_or_terms
```

processed 파일과 별도 metadata 파일을 함께 사용할 수 있습니다.

확인할 것:
- 날짜 변환 실패
- 날짜 key 중복
- `is_holiday` 값 범위
- provenance 누락
- 내부 분석 기간 coverage
- 미매칭 날짜
- source SHA-256

외부 데이터가 없으면 가짜 결과를 만들지 않고 `skipped`로 기록합니다. 미매칭 날짜를 자동으로 일반일로 채우지 않습니다.

## STEP 10. 선택 단계 — LLM Evidence
LLM을 사용하지 않아도 됩니다.

실제 사용했다면 다음을 기록합니다.

```text
execution_status
executed_at
provider
model
prompt_version
step
input_summary
response_summary
validation_result
revision_note
final_use
```

빈 템플릿은 사용 Evidence가 아닙니다.

```text
execution_status = not_executed
final_use = not_used
```

API Key·Token·Password·원본 개인정보는 LLM 로그에 기록하지 않습니다.

## STEP 11. 자동화 설계와 실행 Evidence 구분

```text
reports/ch15_automation_plan.md
```

이 파일은 설계 Evidence입니다.

```text
Automation Plan
≠
Automation Execution Evidence
```

실제 자동화를 구현했다면 Run ID, 실행 로그, Validation, 전달 Evidence를 별도로 제출합니다.

## STEP 12. Project Validation 확인
파일:

```text
reports/ch15_project_validation.csv
```

상태 의미:

```text
PASS = 기준 충족
SKIP = 선택 단계 미사용
WARN = 선택 단계 계약/coverage/해석 제한
FAIL = 필수 오류 또는 보안·산출물 오류
```

필수 `FAIL`이 하나라도 남아 있으면 최종 제출 가능 상태가 아닙니다.

## STEP 13. Reproducibility Manifest 확인
파일:

```text
reports/ch15_reproducibility_manifest.csv
```

확인 항목:
- raw 입력 파일 상대 경로
- 크기
- 수정 시각
- SHA-256
- Python 버전
- pandas / scikit-learn / matplotlib 버전
- random_state

이 정보는 어떤 입력과 환경에서 실행했는지 추적하는 Evidence입니다. 동일 환경 정보가 결과 동일성을 자동 보장하는 것은 아닙니다.

## STEP 14. Deliverable Manifest 확인
파일:

```text
reports/ch15_project_deliverables.csv
```

확인 항목:

```text
deliverable
project_run_id
required
path
exists
size_bytes
nonempty
sha256
```

중요:

```text
SHA-256
→ 파일 변경 추적 Evidence

SHA-256
≠ 분석 타당성 Validation
```

Public Manifest 경로에는 사용자 홈 디렉터리 같은 절대 로컬 경로를 남기지 않습니다.

## STEP 15. Submission Gate 확인
파일:

```text
reports/ch15_submission_status.csv
```

### READY
필수 Validation과 required artifact 기준 충족.

### READY_WITH_WARNINGS
필수 제출 조건은 충족했지만 선택 단계 또는 해석 제한이 남음.

### BLOCKED
필수 `FAIL` 또는 required artifact 누락/빈 파일이 있음.

`READY`는 이 교육 프로젝트의 제출 Gate 통과이며 운영 배포 승인과 같은 뜻이 아닙니다.

## STEP 16. Final Report 확인
파일:

```text
reports/ch15_final_report.md
```

보고서에는 다음 흐름이 보여야 합니다.

```text
질문과 Scope
→ 데이터 품질
→ completed EDA
→ 선택 단계 상태
→ Validation
→ 한계
→ Submission Status
```

결과가 높다는 이유만으로 수익성·원인·운영 적용 가능성을 과장하지 않습니다.

## STEP 17. 같은 입력으로 재실행
다시 실행합니다.

```powershell
python scripts/run_final_project.py
```

확인할 것:
- 새로운 Project Run ID
- 같은 입력에서 핵심 completed 총합 의미 유지
- 필수 산출물 재생성
- 기존 사람이 편집한 LLM 사용 로그를 조용히 덮어쓰지 않음
- Validation 재실행
- Manifest와 Submission Status 갱신

## STEP 18. 최종 판단
답안에는 다음을 작성합니다.

1. 프로젝트 질문에 대한 답
2. completed 금액 Scope
3. PK/FK·merge Evidence
4. 다섯 총합 일치 Evidence
5. 핵심 EDA/그래프 3개
6. 공개 결과 개인정보 처리
7. 선택 분류 실행/SKIP/WARN 이유
8. 외부 데이터 실행/SKIP/WARN 이유
9. LLM 실제 사용 여부와 사람 검증
10. 자동화 계획과 실행 Evidence 구분
11. Reproducibility Manifest의 의미와 한계
12. Deliverable Manifest의 의미와 한계
13. Submission Status와 근거
14. 현재 Evidence로 말할 수 없는 것
15. 다시 실행하는 방법

## 최종 제출 구조

```text
chapter15/
├─ chapter15.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter15/chapter15.ipynb
```

## 완료 체크
- [ ] 질문과 completed 금액 범위 고정
- [ ] Project Run ID 기록
- [ ] `order_item_id` 포함 PK/FK·merge 검증
- [ ] source/category/monthly/customer/product 총합 일치
- [ ] 핵심 EDA/시각화 해석
- [ ] 공개 고객 결과에서 식별 가능 정보 최소화
- [ ] 선택 단계 실행/SKIP/WARN을 사실대로 기록
- [ ] 외부 데이터 provenance·coverage 검증
- [ ] LLM 미실행을 사용 Evidence로 표현하지 않음
- [ ] 자동화 계획과 실행 Evidence 구분
- [ ] Project Validation 확인
- [ ] Reproducibility Manifest 확인
- [ ] Deliverable Manifest와 분석 Validation 구분
- [ ] READY / READY_WITH_WARNINGS / BLOCKED 근거 작성
- [ ] 재실행 절차 확인
- [ ] 최종 Notebook URL 제출
