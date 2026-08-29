# 15장 실습. 하나의 데이터 분석 프로젝트로 완성하기

> 목표는 기능을 많이 넣는 것이 아니라 **하나의 질문을 기준으로 데이터 범위·핵심 계산·선택 단계·검증 Evidence·Manifest·제출 상태·재실행 절차를 끝까지 연결하는 것**입니다.

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
공식 Notebook을 복사해 `chapter15/chapter15.ipynb`로 사용합니다. 최종 Validation/Manifest/상태 Evidence는 필요하면 `chapter15/images/`에 저장합니다.

## STEP 1. 최종 프로젝트 질문과 범위 고정
프로젝트 질문을 먼저 작성합니다.

금액성 EDA 기본 범위:

```text
order_status == completed
line_total = quantity × unit_price
표현 = completed 주문 기준 금액
```

이 값은 할인·배송비·세금·부분 환불·정산 시점을 모두 반영한 회계상 순매출이라고 단정하지 않습니다.

답안에 반드시 작성:
- 분석 질문
- 데이터 범위
- 완료 기준
- 필수 단계
- 선택 단계

## STEP 2. 데이터와 PK/FK 검증
다음을 확인합니다.

```text
customers.customer_id
orders.order_id
products.product_id
order_items.order_item_id

orders.customer_id → customers.customer_id
order_items.order_id → orders.order_id
order_items.product_id → products.product_id
```

merge 전후 행 수와 미매칭 key를 확인합니다.

## STEP 3. completed 금액 총합 불변식 검증
최종 프로젝트의 핵심 검증입니다.

```text
completed_total
=
category_total
=
monthly_total
=
customer_total
=
product_total
```

같은 범위를 집계했다면 모두 일치해야 합니다.

불일치하면 Core FAIL로 판단하고 다음 단계보다 원인을 먼저 찾습니다.

확인 순서 예:

```text
completed 필터
→ line_total 계산
→ merge 중복/누락
→ groupby 범위
→ 결측/타입
```

## STEP 4. EDA와 시각화 완성
최종 질문에 직접 연결되는 EDA와 그래프를 선택합니다.

각 핵심 결과에 대해:

```text
수치/그래프
→ 결과 관찰
→ 나의 해석과 판단
→ 업무·분석적 의미
→ 한계
```

을 작성합니다.

## STEP 5. 공개 결과의 개인정보 점검
Public 제출 결과에는 직접·간접 식별정보가 남지 않도록 확인합니다.

특히 고객 결과에서는 다음을 공개하지 않는 것을 기본으로 합니다.

```text
customer_id
name
email
phone
address
```

현재 프로젝트 코드에서 익명 라벨을 제공하는 경우 공개 결과는 익명화된 표현을 사용합니다.

## STEP 6. 선택 단계 — 분류 모델
분류가 프로젝트 질문에 도움이 되는 경우에만 실행합니다.

확인할 것:
- 타깃 정의
- prediction-time feature
- leakage 제거
- Dummy baseline
- validation에서 모델/threshold 선택
- final test 독립 사용
- public prediction에서 원본 식별자 제외

데이터가 충분하지 않다면 결과를 꾸미지 않고 다음처럼 기록할 수 있습니다.

```text
skipped / insufficient_data
```

선택 단계가 SKIP되었다고 전체 프로젝트 실패는 아닙니다.

## STEP 7. 선택 단계 — 외부 데이터
실제 공식 출처와 provenance가 준비된 경우에만 사용합니다.

최소 기록:
- provider
- source_url
- data_reference_date
- license_or_terms
- raw/processed 경로
- key/date 검증
- coverage

외부 데이터가 없으면 가짜 데이터를 만들어 채우지 않고 `skipped`로 기록합니다.

## STEP 8. 선택 단계 — LLM Evidence
LLM을 실제로 사용한 경우에만 사용 Evidence를 남깁니다.

기록할 것:
- provider/model
- executed_at
- prompt_version
- Safe Context
- LLM 결과
- validation
- 사람이 수정한 내용
- final use

실제로 실행하지 않았다면:

```text
execution_status = not_executed
final_use = not_used
```

처럼 사실대로 기록합니다.

## STEP 9. 자동화 계획과 실행 Evidence 구분
자동화 계획 문서가 있어도 실제 자동화가 실행되었다는 증거는 아닙니다.

```text
automation plan = 설계 Evidence
실제 DAG/run/log/Validation = 실행 Evidence
```

두 가지를 혼동하지 않습니다.

## STEP 10. Project Validation 실행
필수 검증 항목을 실행하고 PASS/WARN/FAIL을 구분합니다.

필수 FAIL이 하나라도 남으면 제출 상태를 READY로 표시하지 않습니다.

가능하면 실행:

```powershell
python scripts/run_final_project.py
```

최종 상태 판단 전 Validation 결과를 먼저 확인합니다.

## STEP 11. Manifest 확인
프로젝트 산출물 목록과 존재 여부를 확인합니다.

대표 Manifest:

```text
ch15_project_deliverables.csv
```

확인 항목 예:
- required
- path
- exists
- size
- nonempty
- SHA-256

중요:

```text
SHA-256 일치/기록
=
파일 변경 추적 Evidence

SHA-256 존재
≠
분석 타당성 PASS
```

## STEP 12. Submission Status 결정
최종 상태는 다음 중 하나로 판단합니다.

### READY
필수 Validation PASS, 필수 산출물 정상, 제출을 막는 문제가 없음.

### READY_WITH_WARNINGS
필수 검증은 통과했지만 선택 단계 SKIP이나 명시할 경고/한계가 있음.

### BLOCKED
필수 Validation FAIL, 필수 산출물 누락/비정상, 재현 불가 등 제출을 막는 문제가 있음.

답안에 **왜 이 상태를 선택했는지 Evidence를 연결해 설명**합니다.

## STEP 13. 처음부터 재실행
가능하면 깨끗한 상태 또는 재현 가능한 절차로 핵심 흐름을 다시 실행합니다.

확인할 것:
- 필요한 입력/환경 설명
- 실행 순서
- 같은 의미의 핵심 총합
- 필수 산출물 재생성
- Validation 결과
- Manifest 갱신

## STEP 14. 최종 분석 결론과 한계
최종 답안에는 다음을 반드시 포함합니다.

1. 프로젝트 질문에 대한 결론
2. 결론을 뒷받침하는 핵심 수치/그래프
3. 업무적으로 어떤 행동/추가 검토를 제안하는가
4. 사용하지 않은 선택 단계와 그 이유
5. 현재 결과로 말할 수 없는 것
6. 추가 데이터/검증이 필요한 것
7. Submission Status와 근거
8. 다른 사람이 재현할 수 있는 실행 방법

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
- [ ] PK/FK와 merge 검증
- [ ] completed/category/monthly/customer/product 총합 일치
- [ ] EDA/시각화 결과 해석
- [ ] 개인정보 제거
- [ ] 선택 단계 실행/SKIP 이유 사실대로 기록
- [ ] LLM 미실행을 PASS처럼 표현하지 않음
- [ ] 자동화 계획과 실행 Evidence 구분
- [ ] Project Validation 확인
- [ ] Manifest와 분석 타당성 구분
- [ ] READY / READY_WITH_WARNINGS / BLOCKED 근거 작성
- [ ] 재실행 절차 확인
- [ ] 최종 Notebook URL 제출