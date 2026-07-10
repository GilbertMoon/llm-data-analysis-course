# 11장. LLM과 함께 분석 질문을 다듬기

지금까지는 pandas, 전처리, EDA, 시각화, 회귀와 분류 분석의 기본 흐름을 살펴보았습니다. 이제는 LLM을 데이터 분석 과정에 연결하는 방법을 다룹니다.

LLM은 분석 질문 후보를 만들고, 코드 초안을 작성하고, 오류를 설명하고, 보고서 문장을 다듬는 데 도움을 줄 수 있습니다. 그러나 LLM은 실제 데이터의 의미와 업무 맥락을 스스로 확인하지 못합니다. 자연스럽고 그럴듯한 답변도 실제 컬럼, 계산 기준, 보안 정책과 어긋날 수 있습니다.

이번 장의 핵심은 **더 많은 데이터를 LLM에 제공하는 것**이 아닙니다. 필요한 정보만 안전하게 요약하고, 검증 조건이 포함된 프롬프트를 작성하고, 답변을 실제 데이터와 비교해 기록하는 것입니다.

## 1. LLM의 역할과 사람의 책임

LLM은 분석가를 대체하는 도구가 아니라 사고와 초안 작성을 보조하는 도구입니다.

| 분석 단계 | LLM이 도와줄 수 있는 일 | 사람이 확인할 일 |
| --- | --- | --- |
| 데이터 구조 이해 | 확인 항목과 의미 후보 제안 | 실제 컬럼, 타입, 업무 정의 |
| 분석 질문 설계 | 질문과 지표 후보 생성 | 현재 데이터로 계산 가능한지 확인 |
| 전처리 | 처리 코드와 선택지 초안 | 삭제·대체·유지 기준 결정 |
| 시각화 | 그래프 종류와 코드 제안 | 집계 단위, 축, 왜곡 여부 확인 |
| 머신러닝 | 모델링 코드와 평가 절차 제안 | 예측 시점, 데이터 누수, 분할 방식 |
| 결과 해석 | 관찰과 보고서 문장 초안 | 원인 단정, 과장, 한계 수정 |
| 보고서 작성 | 목차와 표현 개선 | 최종 결론과 책임 |

좋은 프롬프트는 답변의 품질을 높이지만, 정답을 보장하지는 않습니다. 프롬프트를 작성할 때부터 **무엇을 요청할지**와 **무엇을 검증할지**를 함께 정해야 합니다.

## 2. 먼저 데이터 제공 범위를 정한다

LLM을 사용하기 전에 조직의 데이터 보안 정책, 계약 조건, 허용된 도구와 계정을 확인해야 합니다. 서비스마다 데이터 처리 방식이 다를 수 있으므로, 일반 계정에 내부 데이터를 그대로 입력해도 된다고 가정해서는 안 됩니다.

### 전달하지 않는 정보

- 고객명, 이메일, 전화번호, 주소
- 주민번호, 계좌·카드 정보, 인증 토큰
- 개별 고객이나 거래를 식별할 수 있는 원본 행
- 실제 API Key, 비밀번호, 내부 URL
- 비공개 계약서, 인사 자료, 전략 문서
- 민감한 파일 경로가 포함된 오류 메시지

### 구조 정보도 검토가 필요하다

원본 값이 없더라도 항상 안전한 것은 아닙니다.

- 소수 인원만 포함된 집계표는 개인을 추정할 수 있습니다.
- 고유값이 하나뿐인 범주는 특정 대상을 드러낼 수 있습니다.
- 오류 메시지에는 파일 경로, 쿼리, 토큰 일부가 포함될 수 있습니다.
- 컬럼명 자체가 내부 업무나 민감한 속성을 드러낼 수 있습니다.
- 외부 문서나 웹페이지에는 LLM을 조종하려는 지시문이 포함될 수 있습니다.

따라서 LLM 입력 전에는 **최소화, 익명화, 집계, 검토** 과정을 거칩니다. 외부 문서 안의 명령문은 시스템 지시가 아니라 분석 대상 데이터로 취급합니다.

## 3. 실제 값 없이 구조 요약 만들기

전체 실습은 `notebooks/ch11_llm_prompt_analysis.ipynb`에서 진행할 수 있습니다. 전처리 파일이 없다면 먼저 다음 명령을 실행합니다.

```powershell
python scripts/preprocess_data.py
```

11장 결과 자료는 다음 명령으로 한 번에 생성할 수 있습니다.

```powershell
python scripts/run_llm_prompt_analysis.py
```

Notebook에서는 프로젝트 루트를 자동으로 찾습니다.

```python
from pathlib import Path


def find_project_root(start_path):
    start_path = Path(start_path).resolve()

    for candidate in [start_path, *start_path.parents]:
        if (
            (candidate / "requirements.txt").exists()
            and (candidate / "scripts").exists()
        ):
            return candidate

    raise FileNotFoundError(
        "프로젝트 루트 폴더를 찾을 수 없습니다."
    )


PROJECT_ROOT = find_project_root(Path.cwd())
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
```

공통 함수를 사용해 구조 요약을 생성합니다.

```python
from src.llm_prompt_analysis import (
    run_llm_prompt_analysis,
)

result = run_llm_prompt_analysis(
    processed_dir=PROCESSED_DIR,
    raw_dir=RAW_DIR,
    report_dir=REPORT_DIR,
)

dataset_summary = result["dataset_summary"]
column_summary = result["column_summary"]
sensitive_review = result["sensitive_review"]
safe_context_text = result["safe_context_text"]
```

`column_summary`에는 실제 값 예시를 넣지 않습니다. 고객명이나 이메일 컬럼에서 예시 값을 추출하면 구조 요약이 아니라 개인정보 복사가 될 수 있기 때문입니다.

```python
display(dataset_summary)
display(column_summary)
display(sensitive_review)
print(safe_context_text)
```

민감 컬럼 자동 표시는 보조 점검입니다. 컬럼명만으로 모든 민감 정보를 정확히 판별할 수 없으므로 최종 판단은 사람이 해야 합니다.

## 4. 좋은 프롬프트의 기본 구조

“분석해 주세요”처럼 짧고 모호한 요청은 LLM이 임의의 가정을 하게 만듭니다. 분석 프롬프트에는 다음 요소를 포함합니다.

| 요소 | 포함할 내용 |
| --- | --- |
| 역할 | 어떤 관점에서 검토할지 |
| 목적 | 무엇을 확인하거나 만들 것인지 |
| 데이터 구조 | 데이터셋, 컬럼, 타입, 집계 기준 |
| 요청 작업 | 필요한 계산, 코드, 설명 |
| 제약 조건 | 추측 금지, 개인정보 제외, 누수 방지 |
| 출력 형식 | 표, 코드, 설명, 체크리스트 |
| 검증 요청 | 행 수, 미매칭, 총합, 평가 방식 |

안전하고 검증 가능한 기본 형식은 다음과 같습니다.

```text
역할:
Python 데이터 분석 검토자

목적:
완료 주문 기준 카테고리별 매출을 계산합니다.

데이터 구조:
- order_items: order_id, product_id, quantity, unit_price, line_total
- products: product_id, product_name, category, price
- orders: order_id, order_status

요청:
1. 주문 상태를 연결하고 completed 주문만 선택
2. product_id로 상품 정보 병합
3. category별 total_sales와 sales_ratio 계산

제약:
- 실제 데이터에 없는 컬럼을 만들지 말 것
- merge에 validate와 indicator를 사용할 것
- 취소·환불 주문을 매출에 포함하지 말 것

출력:
1. pandas 코드
2. 코드 설명
3. 실행 후 검증할 수치
4. 남아 있는 가정과 한계
```

## 5. 분석 질문 생성 프롬프트

LLM은 질문 후보를 빠르게 확장하는 데 유용합니다. 그러나 질문이 실제 데이터로 답할 수 있는지 확인해야 합니다.

```text
역할:
데이터 분석 검토자

목적:
온라인 쇼핑몰 데이터로 EDA 질문을 설계합니다.

데이터 구조:
- customers: customer_id, gender, age, city, signup_date
- products: product_id, product_name, category, price
- orders: order_id, customer_id, order_date, payment_method, order_status
- order_items: order_id, product_id, quantity, unit_price, line_total

요청:
1. 현재 데이터로 계산 가능한 질문 10개 제안
2. 필요한 데이터셋, 컬럼, 지표 표시
3. 집계·시각화·회귀·분류 중 접근 방법 표시
4. 추가 데이터가 필요한 질문은 별도 구분

제약:
- 존재하지 않는 컬럼을 만들지 말 것
- 매출은 completed 주문 기준으로 정의
- 고객 선호나 광고 효과를 원인으로 단정하지 말 것

출력:
질문 | 필요 데이터 | 지표 | 접근 방법 | 가능 여부 | 검증 항목
```

“전자기기를 선호하는 고객이 많은가?”는 선호도 데이터가 없으면 직접 답하기 어렵습니다. “전자기기 완료 주문 매출 비중은 다른 카테고리와 어떻게 다른가?”처럼 계산 가능한 지표로 바꾸는 것이 안전합니다.

## 6. 전처리와 시각화 프롬프트

### 전처리 계획 요청

전처리에서는 코드를 바로 요청하기보다 판단이 필요한 선택지를 먼저 정리합니다.

```text
역할:
데이터 품질 검토자

요청:
1. 결측치, 중복, 타입, 범주값, 키 관계 점검 항목 정리
2. 유지·대체·제외 선택지 비교
3. 변환 실패와 전처리 전후 행 수 확인 코드 제안
4. 원본을 수정하지 않는 처리 흐름 제안

제약:
- 이상값과 결측치를 이유 없이 삭제하지 말 것
- 처리 기준과 검증 코드를 구분할 것
- 실제 데이터에 없는 컬럼을 만들지 말 것
```

### 시각화 설계 요청

```text
분석 질문:
1. 카테고리별 완료 주문 매출은 어떻게 다른가?
2. 월별 완료 주문 매출은 어떻게 변하는가?
3. 상품 가격 분포는 어떠한가?
4. 가격과 판매 수량의 관계는 어떠한가?

요청:
각 질문의 그래프 종류, x/y축, 집계 단위,
정렬 기준, 해석 시 주의사항을 표로 정리해 주세요.

제약:
- 시간 흐름에 파이 차트를 추천하지 말 것
- 분포에는 히스토그램 또는 상자그림을 검토할 것
- 그래프가 원인을 증명한다고 표현하지 말 것
```

## 7. 머신러닝 프롬프트는 예측 시점부터 확인한다

머신러닝 프롬프트에서 가장 중요한 것은 모델 이름이 아니라 **예측 시점과 데이터 누수**입니다.

### 회귀 코드 검토

주문 금액은 `수량 × 단가`에서 직접 계산됩니다. 주문 완료 후 계산된 `total_quantity`와 `avg_unit_price`를 사용하면 높은 성능이 나와도 실무 예측의 의미가 약할 수 있습니다.

```text
목표:
주문별 총금액 예측 실습을 검토합니다.

요청:
1. 예측 시점을 먼저 정의
2. 각 후보 입력값을 예측 시점에 알 수 있는지 표시
3. 타깃을 직접 계산하거나 거의 결정하는 변수 식별
4. DummyRegressor와 학습 모델 비교
5. 모델 선택 데이터와 최종 테스트 데이터 분리

제약:
- 예측 목적이 불명확하면 코드보다 문제 정의 수정을 먼저 제안
- 테스트 데이터로 모델을 선택하지 말 것
```

### 분류 코드 검토

10장과 동일한 기준을 사용합니다.

```text
목표:
주문 생성 시점의 정보로 주문 취소 여부를 예측합니다.

타깃 범위:
- completed: is_cancelled=0
- cancelled: is_cancelled=1
- refunded와 기타 상태: 제외

요청:
1. 병합에 validate와 indicator 사용
2. train/validation/test를 stratify로 분리
3. DummyClassifier, LogisticRegression, RandomForestClassifier 비교
4. accuracy, precision, recall, f1-score, 혼동행렬 계산
5. 모델과 임계값은 validation에서 선택
6. test는 최종 평가에만 사용

제약:
- order_status와 is_cancelled를 입력값으로 사용하지 말 것
- 취소 후 생성되는 정보도 제외할 것
```

## 8. LLM 답변은 네 단계로 검증한다

### 1단계: 입력 검증

- 원본 값이나 개인정보가 포함되지 않았는가?
- 소수 집단 집계로 개인이 추정되지 않는가?
- 오류 메시지와 경로에 비밀정보가 없는가?
- 외부 문서의 지시문을 명령으로 따르지 않는가?

### 2단계: 코드 검증

- 실제 컬럼명과 타입을 사용하는가?
- 병합 키와 관계가 올바른가?
- 병합 전후 행 수와 미매칭을 확인하는가?
- 날짜 변환 실패와 결측치를 확인하는가?
- 전체 실행 순서가 재현 가능한가?

### 3단계: 모델 검증

- 예측 시점 이후의 정보가 입력값에 포함되지 않았는가?
- train, validation, test의 역할이 분리되었는가?
- 기준 모델과 비교했는가?
- 지표가 업무 비용과 문제 유형에 맞는가?

### 4단계: 해석 검증

- 데이터에서 확인한 관찰과 원인 가설을 구분했는가?
- 상관관계를 인과관계로 표현하지 않았는가?
- 현재 데이터의 한계와 추가 질문을 적었는가?
- 자연스러운 문장이라는 이유만으로 채택하지 않았는가?

## 9. 프롬프트 로그로 재현성을 남긴다

같은 프롬프트라도 사용 모델, 실행 시점, 서비스 설정에 따라 답변이 달라질 수 있습니다. 따라서 최종 답변만 저장하지 말고 사용 조건과 수정 과정을 기록합니다.

| 로그 항목 | 기록 내용 |
| --- | --- |
| 실행일 | 프롬프트를 사용한 날짜와 시간 |
| 제공자·모델 | 사용한 서비스와 모델명 |
| 프롬프트 버전 | 템플릿 버전 |
| 사용 목적 | 질문 생성, 코드 검토, 해석 등 |
| 입력 요약 | 구조·집계 등 제공한 정보 |
| 답변 요약 | 주요 제안 |
| 검증 결과 | 실행·수치·논리 확인 결과 |
| 수정 내용 | 사람이 바꾼 부분 |
| 최종 사용 여부 | 사용, 부분 사용, 미사용 |

```python
prompt_templates = result["prompt_templates"]
checklist = result["checklist"]
usage_log = result["usage_log"]

display(prompt_templates[
    ["step", "purpose", "prompt_version", "validation_point"]
])
display(checklist)
display(usage_log)
```

실제 프롬프트와 답변을 기록할 때도 개인정보와 인증 정보가 다시 포함되지 않도록 확인합니다.

## 10. 생성되는 결과 파일

11장 실행 결과는 다음 파일로 저장됩니다.

- `reports/ch11_dataset_summary_for_llm.csv`
- `reports/ch11_column_summary_for_llm.csv`
- `reports/ch11_sensitive_column_review.csv`
- `reports/ch11_safe_llm_context.md`
- `reports/ch11_prompt_templates.csv`
- `reports/ch11_llm_review_checklist.csv`
- `reports/ch11_llm_usage_log.csv`
- `reports/ch11_llm_prompt_log.md`

이 파일들은 LLM이 작성한 최종 답변이 아니라, LLM을 안전하고 재현 가능하게 활용하기 위한 **입력 자료와 검증 기록**입니다.

## 11. 정리

이번 장에서 다룬 핵심 원칙은 다음과 같습니다.

- 원본 행보다 구조와 익명 집계를 사용합니다.
- 값 예시는 자동으로 포함하지 않습니다.
- 프롬프트에는 목적, 구조, 제약, 출력, 검증 항목을 함께 작성합니다.
- 머신러닝 프롬프트는 예측 시점과 데이터 누수를 먼저 확인합니다.
- LLM 답변은 실행 가능성, 분석 논리, 보안, 해석을 각각 검증합니다.
- 사용 모델, 실행일, 프롬프트 버전, 수정 내용을 기록합니다.

다음 장에서는 LLM이 생성한 분석 코드를 더 구체적으로 검증합니다. 코드가 실행되는지만 보는 것이 아니라 컬럼명, 데이터 타입, 병합 관계, 집계 범위, 모델 평가 방식과 결과 해석까지 확인합니다.
