# 12장 실습. LLM이 만든 분석 코드를 검증하는 방법

> 목표는 생성 코드를 바로 실행하는 것이 아니라 **분석 타당성과 실행 안전을 분리해 검증하고, 사람이 승인한 코드만 제한된 환경에서 실행한 뒤 사후 결과까지 다시 확인하는 것**입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter12/templates/chapter12_assignment.md`
- 주 제출물: `chapter12/chapter12.ipynb`

공식 Notebook:

```text
notebooks/ch12_report_generation.ipynb
```

파일명은 초기 프로젝트 명칭을 유지하지만 현재 실제 내용은 **LLM 생성 분석 코드 검증 실습**입니다.

공통 검증 코드:

```text
src/llm_code_validation.py
src/llm_code_validation_policy.py
scripts/run_llm_code_validation.py
```

이번 장의 핵심:

```text
코드 실행 성공 ≠ 분석 타당성
정적 스캔 0건 ≠ 코드 안전
자동 검증 PASS ≠ 실행 승인
```

---

## STEP 0. 제출용 Notebook과 processed 입력 준비

공식 Notebook을 개인 저장소의 다음 위치에 복사합니다.

```text
chapter12/chapter12.ipynb
```

Public 저장소 루트에서 실행합니다.

```powershell
python --version
python -m pip install -r requirements.txt
python scripts/preprocess_data.py
```

필수 입력:

```text
data/processed/customers_clean.csv
data/processed/products_clean.csv
data/processed/orders_clean.csv
data/processed/order_items_clean.csv
```

Chapter 12는 processed 입력이 없을 때 raw로 자동 fallback하지 않습니다.

---

## STEP 1. Generated Code를 실행하지 않고 먼저 읽기

LLM이 만든 코드 또는 검증 대상 코드를 먼저 읽습니다.

```text
어떤 파일을 읽는가?
어떤 파일을 생성·수정·삭제하는가?
어떤 dataset과 column을 사용하는가?
어떤 key로 merge하는가?
어떤 주문 상태를 포함하는가?
네트워크 요청이 있는가?
OS/Shell 명령이 있는가?
subprocess를 실행하는가?
새 package 설치를 요구하는가?
Secret·환경변수·민감 경로를 읽는가?
```

**아직 실행하지 않습니다.**

답안에는 코드 목적, 입력, 출력, 주요 컬럼·키·분석 범위를 먼저 기록합니다.

---

## STEP 2. 실제 Schema · PK · FK 검증

공식 Notebook에서 다음 Evidence를 확인합니다.

```python
from src.llm_code_validation import (
    assert_validation_ready,
    build_dataset_inventory,
    load_validation_data,
    validate_primary_keys,
    validate_relationship_keys,
    validate_required_columns,
)

datasets = load_validation_data("data/processed")

inventory = build_dataset_inventory(datasets)
required_column_check = validate_required_columns(datasets)
primary_key_check = validate_primary_keys(datasets)
relationship_check = validate_relationship_keys(datasets)

assert_validation_ready(
    required_column_check,
    primary_key_check,
    relationship_check,
)
```

주요 PK:

```text
customers.customer_id
products.product_id
orders.order_id
order_items.order_item_id
```

특히 `order_items.order_item_id`도 **필수 컬럼 존재와 PK 고유성 검증 대상**입니다.

관계:

```text
orders.customer_id      → customers.customer_id
order_items.order_id    → orders.order_id
order_items.product_id  → products.product_id
```

필수 컬럼이나 key가 없으면 조용히 제외하지 않고 fail-fast합니다.

---

## STEP 3. merge · completed 범위 · 총합 검증

주문 상세 금액 관계:

```text
line_total = quantity × unit_price
```

카테고리와 월별 집계를 검증합니다.

```python
from src.llm_code_validation import (
    safe_category_sales,
    safe_monthly_sales,
)

category_sales, category_validation = safe_category_sales(
    datasets["order_items"],
    datasets["products"],
    datasets["orders"],
)

monthly_sales, monthly_validation = safe_monthly_sales(
    datasets["order_items"],
    datasets["orders"],
)
```

확인할 내용:

```text
부모 key 고유성
validate="many_to_one"
merge 전후 행 수
미매칭 수
category 결측
날짜 변환 실패
order_status == "completed"
source total
category grouped total
monthly grouped total
```

성공 관계:

```text
completed source total
= category grouped total
= monthly grouped total
```

이 금액을 할인·세금·배송비·부분 환불까지 반영한 회계상 순매출이라고 단정하지 않습니다.

---

## STEP 4. Generated Code를 실행하지 않고 AST Static Scan

공식 위험 예제는 **실행하지 않는 문자열**입니다.

```python
from src.llm_code_validation import (
    DEFAULT_STATIC_SCAN_EXAMPLE,
    scan_generated_code,
)

static_scan = scan_generated_code(
    DEFAULT_STATIC_SCAN_EXAMPLE
)
```

대표 탐지 대상:

```text
eval / exec / compile
os.system / subprocess
requests / urllib / socket
파일 쓰기·삭제·교체
to_csv / to_excel / write_text
하드코딩 API Key / token / password
pip / ensurepip
```

심각도:

```text
critical / high
→ BLOCKED

review
→ 사람 검토

0 findings
→ SAFE가 아니라 REVIEW
```

정적 스캔은 screening 도구이며 안전 인증기가 아닙니다.

---

## STEP 5. 회귀와 분류 Feature Contract를 따로 검토

모든 모델에 같은 금지 Feature 목록을 사용하지 않습니다.

```python
from src.llm_code_validation import (
    build_feature_audit,
    build_leakage_review_table,
    validate_feature_list,
)
```

### Chapter 09 회귀

대표 금지 입력:

```text
order_total
line_total
quantity
unit_price
item_count
total_quantity
avg_unit_price
order_status
order_id
customer_id
```

```python
validate_feature_list(
    regression_features,
    problem="regression",
)
```

### Chapter 10 분류

대표 금지 입력:

```text
order_status
is_cancelled
order_id
customer_id
product_id
row-level line_total
row-level quantity
row-level unit_price
cancel_reason
cancelled_at
```

`item_count`, `total_quantity`, `order_amount`는 **주문 생성 시 이미 확정되어 있다는 교육용 예측 시점 가정** 아래 REVIEW할 수 있습니다.

```python
validate_feature_list(
    classification_features,
    problem="classification",
)
```

Feature Leakage는 컬럼 이름만이 아니라 **Prediction Time**을 기준으로 판단합니다.

---

## STEP 6. Sandbox와 Package 공급망 검토

권장 Sandbox 조건:

```text
복사한 소량 샘플
read-only input 가능하면 적용
credential 없는 환경
disposable environment
쓰기 경로 allowlist
network deny by default
CPU / memory / timeout / process / disk limit
실행 전 baseline
실행 후 변경 비교
```

Package 설치 제안도 바로 실행하지 않습니다.

```text
필요성
공식 source
정확한 package name
typosquatting
exact version
Python compatibility
transitive dependency
install script
isolated environment
requirements / lock
조직 정책
```

초기 결정:

```text
DO_NOT_INSTALL_UNTIL_REVIEWED
```

---

## STEP 7. 전체 Evidence와 Execution Gate 확인

일괄 Evidence 생성:

```powershell
python scripts/run_llm_code_validation.py
```

이 스크립트는 정적 스캔 대상 Generated Code를 실행하지 않습니다.

Notebook에서 강화된 정책 레이어를 사용할 수 있습니다.

```python
from src.llm_code_validation_policy import run_llm_code_validation

result = run_llm_code_validation(
    processed_dir="data/processed",
    report_dir="reports",
)

display(result["outputs"]["execution_gate"])
```

Execution Gate:

```text
schema_and_keys
aggregate_validation
ml_leakage
static_scan
sandbox_and_package
human_approval
execution_decision
```

판정:

```text
FAIL 또는 BLOCKED 존재
→ DO_NOT_EXECUTE

자동 차단 항목 없음
→ HUMAN_REVIEW_REQUIRED
```

기본 위험 예제를 검사하면 `DO_NOT_EXECUTE`가 나오는 것이 정상입니다.

```text
DO_NOT_EXECUTE
≠ 자동화 실패
= 현재 검사한 코드에 차단 사유가 있음
```

자동 Evidence만으로 `EXECUTE` 상태를 만들지 않습니다.

---

## STEP 8. 사람의 APPROVE / REVISE / BLOCK 판단

실행 전 다음 중 하나를 선택하고 근거를 기록합니다.

```text
APPROVE — 제한 실행 후보
REVISE — 수정 후 재검토
BLOCK — 현재 상태에서는 실행하지 않음
```

판단에는 두 축이 모두 필요합니다.

```text
분석 타당성
+
실행 안전
```

LLM 초안과 사람이 수정한 내용을 구분해서 남깁니다.

사람 수정 Log의 초기 상태:

```text
execution_approved = False
```

실제로 검토·승인한 뒤에만 변경합니다.

---

## STEP 9. APPROVE된 코드만 제한 실행

중요:

```text
DEFAULT_STATIC_SCAN_EXAMPLE을 실행하지 않습니다.
검토·수정·승인한 자신의 분석 코드만 실행합니다.
```

실행 전 기록:

```text
코드 버전
입력 파일
출력 허용 경로
네트워크 허용 여부
Python·핵심 package 버전
시작 시각
baseline 파일 목록 또는 hash/크기
```

실행 후 기록:

```text
종료 시각
exit code
timeout 여부
생성·수정·삭제 파일
허용 경로 밖 변경
```

---

## STEP 10. Post-execution Validation

정상 종료 메시지만 보지 않습니다.

```text
입력/출력 행 수
merge 전후 행 수
미매칭 수
completed 범위
line_total 관계
source total
category/monthly grouped total
예상한 파일만 생성되었는가
원본이 보존되었는가
외부 전송 흔적이 없는가
Secret이 로그에 남지 않았는가
```

```text
코드 실행 성공
≠
분석 결과 검증 완료
```

---

## STEP 11. 오류를 LLM에게 물을 때도 최소 Context만 공유

공통 Prompt Template:

```python
from src.llm_code_validation import build_error_fix_prompt_template

print(build_error_fix_prompt_template())
```

공유할 내용:

```text
분석 목적
필요한 최소 schema
최소 재현 코드
비식별 오류 메시지
행 수·미매칭·총합 차이 Evidence
```

공유하지 않을 내용:

```text
고객 원본 행
API Key / Token / DB password
내부 URL
개인 사용자 절대 경로
전체 환경변수
민감 설정 파일
```

---

## STEP 12. Evidence와 최종 판단

대표 결과 파일:

```text
reports/ch12_dataset_inventory.csv
reports/ch12_required_column_check.csv
reports/ch12_primary_key_check.csv
reports/ch12_relationship_key_check.csv
reports/ch12_category_sales_validated.csv
reports/ch12_category_sales_validation.csv
reports/ch12_monthly_sales_validated.csv
reports/ch12_monthly_sales_validation.csv
reports/ch12_ml_leakage_review.csv
reports/ch12_generated_code_static_scan.csv
reports/ch12_execution_gate.csv
reports/ch12_sandbox_execution_checklist.csv
reports/ch12_package_install_review.csv
reports/ch12_human_revision_log.csv
reports/ch12_llm_code_review_checklist.csv
reports/ch12_error_fix_prompt_template.md
reports/ch12_code_validation_summary.md
```

최종 판단:

```text
현재 범위에서 사용 가능
추가 검증 후 사용 가능
사용 보류
```

신뢰할 수 있는 범위와 아직 신뢰할 수 없는 부분을 분리해서 작성합니다.

---

## 최종 제출

```text
chapter12/
├─ chapter12.ipynb
└─ images/
   ├─ step03_risk_scan.png
   ├─ step06_limited_run.png
   └─ step07_post_validation.png
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter12/chapter12.ipynb
```

## 완료 체크
- [ ] Read Before Run 수행
- [ ] processed 입력 확인
- [ ] `order_items.order_item_id` 포함 필수 컬럼·PK 검증
- [ ] FK와 부모 key 고유성 검증
- [ ] merge validate·행 수·미매칭 검증
- [ ] completed 범위와 line_total 검증
- [ ] source total과 grouped total 대조
- [ ] AST Static Scan
- [ ] 정적 스캔 0건을 SAFE로 오해하지 않음
- [ ] 회귀·분류 Feature Contract 구분
- [ ] Sandbox·Package 검토
- [ ] Execution Gate 확인
- [ ] APPROVE / REVISE / BLOCK 판단 기록
- [ ] LLM 초안과 사람 수정 기록
- [ ] APPROVE된 코드만 제한 실행
- [ ] Post-execution Validation
- [ ] 최종 신뢰 범위와 한계 작성
- [ ] 최종 Notebook URL 제출
