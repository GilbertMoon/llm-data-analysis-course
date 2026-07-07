# 11장. LLM과 함께 분석 질문을 다듬기

지금까지는 pandas, 전처리, EDA, 시각화, 머신러닝 기초를 차례로 다루었습니다. 이제는 이 과정을 LLM과 함께 진행하는 방법을 살펴봅니다. LLM은 분석 질문을 정리하고, 데이터 구조를 설명하고, 코드 초안을 만들고, 결과 해석의 방향을 제안하는 데 도움을 줄 수 있습니다.

하지만 LLM에게 분석을 그대로 맡겨서는 안 됩니다. LLM은 실제 데이터를 직접 이해하는 분석가가 아니라, 사용자가 제공한 설명과 패턴을 바탕으로 그럴듯한 답변을 생성하는 도구입니다. 따라서 좋은 프롬프트는 LLM이 추측할 여지를 줄이고, 사람이 검증할 수 있는 형태의 답변을 만들도록 돕는 장치입니다.

이번 장에서는 온라인 쇼핑몰 데이터 분석 프로젝트를 기준으로, LLM에게 어떤 정보를 제공해야 하는지, 어떤 방식으로 질문해야 하는지, 어떤 답변을 조심해야 하는지 살펴봅니다. 핵심은 “AI가 대신 분석한다”가 아니라, **분석가가 LLM을 안전하게 활용해 사고의 속도와 검토 범위를 넓히는 것**입니다.

## 이 장에서 생각해 볼 질문

LLM을 데이터 분석에 활용하기 전에 다음 질문을 먼저 생각해 봅니다.

- LLM에게 원본 데이터를 그대로 넣어도 괜찮을까?
- 데이터 구조를 어떻게 요약해서 전달해야 할까?
- 좋은 분석 프롬프트에는 어떤 요소가 들어가야 할까?
- LLM이 제안한 분석 질문은 실제 데이터로 답할 수 있을까?
- LLM이 만든 pandas, 시각화, 머신러닝 코드 초안은 어떻게 검토해야 할까?
- LLM이 작성한 해석 문장에서 과장이나 원인 단정은 어떻게 찾을까?
- LLM 활용 내역은 왜 기록해야 할까?

## 1. LLM은 분석 과정에서 무엇을 도와줄 수 있는가

LLM은 데이터 분석의 모든 단계를 대신하지는 못하지만, 각 단계에서 출발점을 만들어 줄 수 있습니다. 특히 처음 데이터를 받았을 때 무엇부터 확인해야 할지 막막하거나, 작성한 코드를 설명하고 싶거나, 결과 해석 문장을 다듬고 싶을 때 유용합니다.

| 분석 단계 | LLM이 도와줄 수 있는 일 | 사람이 반드시 확인할 일 |
| --- | --- | --- |
| 데이터 구조 이해 | 컬럼 의미 추정, 확인할 항목 제안 | 실제 컬럼명과 타입 확인 |
| 분석 질문 만들기 | 가능한 분석 질문 후보 제안 | 현재 데이터로 답할 수 있는지 검토 |
| 전처리 | 결측치, 날짜, 문자열 처리 코드 초안 | 처리 기준이 분석 목적에 맞는지 판단 |
| 시각화 | 질문에 맞는 그래프 추천 | 그래프 종류와 축 의미 검증 |
| 머신러닝 | 회귀/분류 모델링 코드 초안 | 데이터 누수, 평가 방식, 지표 해석 검증 |
| 결과 해석 | 보고서 문장 초안 작성 | 원인 단정과 과장 표현 수정 |
| 보고서 작성 | 문장 구조와 목차 제안 | 데이터에 근거한 최종 결론 작성 |

LLM을 잘 활용하려면 “무엇을 요청할지”보다 “무엇을 검증할지”를 함께 생각해야 합니다. 코드가 실행된다고 해서 분석이 맞는 것은 아니고, 문장이 자연스럽다고 해서 해석이 타당한 것도 아닙니다.

## 2. 원본 데이터 대신 구조를 전달하기

LLM에게 실제 고객명, 이메일, 전화번호, 주소, 주문 상세 전체 데이터를 그대로 입력하는 것은 피해야 합니다. 실습 데이터라면 위험이 작을 수 있지만, 실무에서는 개인정보와 내부 거래 정보가 포함될 가능성이 높습니다.

LLM에게 제공하기 좋은 정보는 원본 데이터가 아니라 **구조 요약**입니다.

| 입력 가능 정보 | 예시 |
| --- | --- |
| 데이터셋 이름 | customers, products, orders, order_items |
| 컬럼명 | customer_id, order_date, category |
| 데이터 크기 | 150행 6열 |
| 데이터 타입 | age: int, order_date: object |
| 결측치 개수 | age 결측치 3개 |
| 집계 결과 | 카테고리별 매출 요약표 |
| 오류 메시지 | KeyError, TypeError 등 |
| 분석 목적 | 월별 매출 분석, 주문 취소 여부 예측 |

주의해야 할 정보는 다음과 같습니다.

| 주의 정보 | 예시 |
| --- | --- |
| 개인정보 | 이름, 이메일, 전화번호, 주소 |
| 거래 상세 원본 | 개별 주문 내역 전체 |
| 민감한 내부 정보 | 실제 매출 원본, 고객 식별 가능 데이터 |
| 인증 정보 | API Key, 비밀번호, 토큰 |
| 비공개 문서 | 계약서, 인사 정보, 내부 전략 문서 |

LLM에게는 가능한 한 “데이터의 모양”과 “분석 목적”을 전달하고, 개인이나 거래를 식별할 수 있는 원본 값은 제외하는 것이 좋습니다.

## 3. 좋은 프롬프트의 구조

좋은 프롬프트는 단순히 “분석해 줘”라고 묻지 않습니다. LLM이 추측하지 않고 답할 수 있도록 배경, 데이터 구조, 요청 작업, 제약 조건, 출력 형식을 함께 제공합니다.

| 구성 요소 | 설명 | 예시 |
| --- | --- | --- |
| 역할 | 어떤 관점으로 답할지 지정 | Python 데이터 분석 멘토 |
| 목적 | 무엇을 하려는지 설명 | 카테고리별 매출 분석 |
| 데이터 구조 | 데이터셋과 컬럼 정보 제공 | order_items, products 컬럼 목록 |
| 요청 작업 | 작성할 코드나 해석 작업 명시 | merge 후 groupby 집계 |
| 제약 조건 | 추측 금지, 컬럼명 생성 금지 등 | 실제 데이터에 없는 컬럼명을 만들지 말 것 |
| 출력 형식 | 원하는 답변 형태 지정 | 코드, 설명, 검증 항목 |
| 검증 요청 | 확인해야 할 위험 요소 포함 | 병합 전후 행 수 확인 코드 포함 |

나쁜 프롬프트는 정보가 부족하고 요청이 모호합니다.

```text
데이터 분석 코드 짜줘.
```

이 프롬프트에는 데이터 구조, 분석 목적, 컬럼명, 원하는 결과가 없습니다. LLM은 임의로 컬럼명을 만들어낼 수 있고, 실제 데이터와 맞지 않는 코드를 생성할 가능성이 큽니다.

더 안전한 프롬프트는 다음과 같습니다.

```text
온라인 쇼핑몰 데이터에서 카테고리별 매출을 계산하려고 합니다.

데이터 구조:
- order_items: order_id, product_id, quantity, unit_price, line_total
- products: product_id, product_name, category, price

요청:
1. product_id 기준으로 두 DataFrame을 병합
2. category별 line_total 합계 계산
3. 매출이 큰 순서로 정렬
4. sales_ratio 컬럼 생성

주의:
- 실제 데이터에 없는 컬럼명을 만들지 마세요.
- 병합 전후 행 수 확인 코드를 포함해 주세요.
- 병합 후 category 결측치 확인 코드를 포함해 주세요.

출력 형식:
1. pandas 코드
2. 코드 설명
3. 실행 후 확인해야 할 사항
```

좋은 프롬프트는 LLM이 추측할 여지를 줄이고, 사람이 검증할 수 있는 답변을 만들도록 돕습니다.

## 4. 데이터 구조 요약 만들기

이번 장의 코드는 `notebooks/ch11_llm_prompt_analysis.ipynb`로 구성하는 것이 좋습니다. 현재 저장소의 노트북 파일명은 기존 목차 기준으로 남아 있을 수 있으므로, 이후 새 목차에 맞춰 정리할 수 있습니다.

먼저 필요한 패키지를 불러옵니다.

```python
from pathlib import Path
import pandas as pd
```

실행 위치에 따라 기준 폴더를 설정합니다.

```python
current_dir = Path.cwd()

if current_dir.name == "notebooks":
    base_dir = current_dir.parent
else:
    base_dir = current_dir

processed_dir = base_dir / "data" / "processed"
raw_dir = base_dir / "data" / "raw"
report_dir = base_dir / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

print("processed_dir:", processed_dir)
print("raw_dir:", raw_dir)
print("report_dir:", report_dir)
```

전처리된 데이터가 있으면 `data/processed`에서 불러옵니다.

```python
customers = pd.read_csv(processed_dir / "customers_clean.csv")
products = pd.read_csv(processed_dir / "products_clean.csv")
orders = pd.read_csv(processed_dir / "orders_clean.csv")
order_items = pd.read_csv(processed_dir / "order_items_clean.csv")
```

전처리 파일이 없다면 원본 데이터를 사용할 수 있습니다.

```python
customers = pd.read_csv(raw_dir / "customers.csv")
products = pd.read_csv(raw_dir / "products.csv")
orders = pd.read_csv(raw_dir / "orders.csv")
order_items = pd.read_csv(raw_dir / "order_items.csv")
```

데이터셋을 딕셔너리로 정리합니다.

```python
datasets = {
    "customers": customers,
    "products": products,
    "orders": orders,
    "order_items": order_items
}
```

LLM 입력용 데이터 구조 요약표를 만듭니다.

```python
dataset_summary = []

for name, df in datasets.items():
    dataset_summary.append({
        "dataset": name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_list": ", ".join(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicated_rows": int(df.duplicated().sum())
    })

dataset_summary = pd.DataFrame(dataset_summary)
dataset_summary
```

컬럼별 데이터 타입 요약도 만듭니다.

```python
column_summary_rows = []

for name, df in datasets.items():
    for col in df.columns:
        column_summary_rows.append({
            "dataset": name,
            "column": col,
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isna().sum()),
            "unique_count": int(df[col].nunique())
        })

column_summary = pd.DataFrame(column_summary_rows)
column_summary
```

요약표를 저장합니다.

```python
dataset_summary.to_csv(report_dir / "ch11_dataset_summary_for_llm.csv", index=False)
column_summary.to_csv(report_dir / "ch11_column_summary_for_llm.csv", index=False)
```

이 표들은 LLM에게 원본 데이터 대신 제공할 수 있는 안전한 구조 정보입니다.

## 5. 분석 질문을 생성하는 프롬프트

LLM은 분석 질문을 확장하는 데 유용합니다. 다만 현재 데이터로 답할 수 없는 질문까지 제안할 수 있으므로, 반드시 “현재 데이터로 가능한지 표시해 달라”고 요청하는 것이 좋습니다.

```text
온라인 쇼핑몰 데이터로 EDA를 수행하려고 합니다.

데이터셋 구조:
- customers: customer_id, gender, age, city, signup_date
- products: product_id, product_name, category, price
- orders: order_id, customer_id, order_date, payment_method, order_status
- order_items: order_id, product_id, quantity, unit_price, line_total

요청:
1. 현재 데이터로 분석 가능한 질문 10개를 제안해 주세요.
2. 각 질문에 필요한 데이터셋과 컬럼을 함께 적어 주세요.
3. 집계, 시각화, 회귀, 분류 중 어떤 방식으로 접근할 수 있는지 표시해 주세요.
4. 현재 데이터로 답할 수 없는 질문은 제외하거나, 추가 데이터가 필요하다고 표시해 주세요.

주의:
- 실제 데이터에 없는 컬럼을 만들지 마세요.
- 고객 선호도, 광고 효과, 프로모션 효과처럼 현재 데이터에 없는 원인을 단정하지 마세요.
```

좋은 분석 질문은 데이터로 답할 수 있어야 합니다. 예를 들어 “전자기기를 선호하는 고객이 많은가?”라는 질문은 선호도 데이터가 없다면 직접 답하기 어렵습니다. 대신 “전자기기 카테고리의 매출 비중은 다른 카테고리와 어떻게 다른가?”처럼 현재 데이터로 확인 가능한 질문으로 바꿀 수 있습니다.

## 6. 전처리 프롬프트

전처리 프롬프트는 단순히 “전처리해 줘”라고 요청하기보다, 어떤 문제를 확인하고 어떤 기준으로 처리할지 명확히 적어야 합니다.

```text
다음 온라인 쇼핑몰 데이터의 전처리 계획을 세우려고 합니다.

데이터 구조:
- customers: customer_id, gender, age, city, signup_date
- products: product_id, product_name, category, price
- orders: order_id, customer_id, order_date, payment_method, order_status
- order_items: order_id, product_id, quantity, unit_price, line_total

요청:
1. 각 데이터셋에서 확인해야 할 결측치, 중복, 데이터 타입 문제를 정리해 주세요.
2. order_date와 signup_date를 날짜형으로 변환할 때 확인할 사항을 알려 주세요.
3. 문자열 범주값의 표기 차이를 확인하는 코드를 제안해 주세요.
4. 전처리 후 저장할 파일명을 제안해 주세요.

주의:
- 결측치나 이상값을 무조건 삭제하지 마세요.
- 삭제, 대체, 유지 중 어떤 선택지가 있는지 비교해 주세요.
- 실제 데이터에 없는 컬럼명을 만들지 마세요.
```

이런 프롬프트는 전처리 코드를 바로 얻는 것보다, 전처리 계획을 먼저 정리하는 데 도움이 됩니다.

## 7. 시각화 프롬프트

시각화 프롬프트는 분석 질문과 그래프 선택 기준을 함께 전달해야 합니다.

```text
온라인 쇼핑몰 데이터 분석 결과를 시각화하려고 합니다.

분석 질문:
1. 카테고리별 매출은 어떻게 다른가?
2. 월별 매출은 어떻게 변하는가?
3. 상품 가격은 어떤 구간에 몰려 있는가?
4. 상품 가격과 판매 수량은 관계가 있는가?
5. 구매 금액 상위 고객은 누구인가?

요청:
1. 각 질문에 적합한 그래프 종류를 추천해 주세요.
2. 그래프를 선택한 이유를 설명해 주세요.
3. matplotlib 코드 작성 시 필요한 x축, y축 컬럼을 정리해 주세요.
4. 그래프 해석 시 주의할 점을 알려 주세요.

주의:
- 월별 매출을 파이 차트로 추천하지 마세요.
- 상품 가격 분포는 선 그래프가 아니라 히스토그램으로 검토해 주세요.
- 고객명이 포함되는 그래프는 익명화 필요성을 언급해 주세요.
```

LLM이 그래프를 추천하더라도 최종 선택은 분석 질문을 기준으로 검토해야 합니다. 시간 흐름은 선 그래프, 범주별 비교는 막대그래프, 분포는 히스토그램, 두 숫자형 변수의 관계는 산점도가 기본 출발점입니다.

## 8. 머신러닝 프롬프트

머신러닝 프롬프트에서는 예측 대상과 입력값을 명확히 구분해야 합니다. 특히 회귀나 분류에서는 정답 컬럼이 입력값에 섞이는 데이터 누수를 조심해야 합니다.

### 회귀 분석 프롬프트 예시

```text
온라인 쇼핑몰 주문 데이터를 사용해 주문별 총금액을 예측하는 회귀 모델을 만들려고 합니다.

데이터 구조:
- order_items: order_id, product_id, quantity, unit_price, line_total
- orders: order_id, customer_id, order_date, payment_method, order_status
- customers: customer_id, gender, age, city

예측 대상:
- order_total: 주문별 line_total 합계

입력값 후보:
- item_count
- total_quantity
- avg_unit_price
- payment_method
- order_status
- order_month
- order_dayofweek
- gender
- age
- city

요청:
1. 주문별 모델링 데이터셋을 만드는 pandas 코드를 작성해 주세요.
2. train/test split을 적용해 주세요.
3. LinearRegression과 RandomForestRegressor를 비교해 주세요.
4. MAE, RMSE, R2를 계산해 주세요.
5. 데이터 누수가 발생할 수 있는 부분을 설명해 주세요.

주의:
- order_total을 입력값으로 사용하지 마세요.
- 실제 데이터에 없는 컬럼명을 만들지 마세요.
- 범주형 컬럼은 OneHotEncoder를 사용해 주세요.
- 테스트 데이터 기준으로 평가해 주세요.
```

### 분류 분석 프롬프트 예시

```text
온라인 쇼핑몰 주문 데이터를 사용해 주문 취소 여부를 예측하는 분류 모델을 만들려고 합니다.

데이터 구조:
- orders: order_id, customer_id, order_date, payment_method, order_status
- order_items: order_id, product_id, quantity, unit_price, line_total
- customers: customer_id, gender, age, city

예측 대상:
- is_cancelled: order_status가 cancelled이면 1, 아니면 0

입력값 후보:
- total_quantity
- order_total
- item_count
- payment_method
- order_month
- gender
- age
- city

요청:
1. 주문별 분류 데이터셋을 만드는 pandas 코드를 작성해 주세요.
2. train/test split을 적용해 주세요.
3. LogisticRegression과 RandomForestClassifier를 비교해 주세요.
4. accuracy, precision, recall, confusion matrix를 계산해 주세요.
5. 클래스 불균형이 있는지 확인하는 코드를 포함해 주세요.

주의:
- order_status 원본 컬럼을 입력값으로 사용하지 마세요.
- is_cancelled를 만든 뒤에는 정답 정보가 입력값에 섞이지 않도록 해 주세요.
- 실제 데이터에 없는 컬럼명을 만들지 마세요.
```

머신러닝 프롬프트에서는 “모델을 만들어 달라”보다 “데이터 누수를 확인해 달라”, “평가 지표를 함께 계산해 달라”, “정답 컬럼을 입력값에서 제외해 달라”는 요청이 중요합니다.

## 9. 결과 해석 프롬프트

LLM은 해석 문장을 자연스럽게 만들어 줄 수 있지만, 데이터에 없는 원인을 단정하는 경우가 있습니다. 따라서 프롬프트에 관찰과 가설을 구분하라는 조건을 넣어야 합니다.

```text
다음은 카테고리별 매출 분석 결과입니다.

category,total_quantity,total_sales,sales_ratio
전자기기,320,12500000,42.5
생활용품,510,7800000,26.5
패션,260,6200000,21.1
식품,430,2900000,9.9

요청:
1. 데이터로 확인 가능한 관찰 내용을 작성해 주세요.
2. 가능한 원인 가설을 조심스럽게 작성해 주세요.
3. 추가로 확인해야 할 분석 질문을 제안해 주세요.
4. 보고서에 넣을 수 있는 문장으로 정리해 주세요.

조건:
- 고객 선호, 프로모션 효과 같은 원인을 단정하지 마세요.
- 데이터에 없는 내용을 추측하지 마세요.
- 관찰과 가설을 구분해 주세요.
```

위 조건이 없으면 LLM은 “전자기기 매출이 높은 이유는 고객 선호도가 높기 때문”처럼 그럴듯하지만 검증되지 않은 문장을 만들 수 있습니다.

## 10. LLM 답변 검증 체크리스트

LLM 답변은 반드시 사람이 검증해야 합니다. 특히 코드와 해석에서는 다음 항목을 확인합니다.

| 점검 항목 | 확인 |
| --- | --- |
| 원본 개인정보나 거래 상세를 입력하지 않았는가? | □ |
| 데이터 구조 요약만 입력했는가? | □ |
| 분석 목적을 명확히 작성했는가? | □ |
| 원하는 출력 형식을 지정했는가? | □ |
| 실제 데이터에 없는 컬럼명을 만들지 말라고 요청했는가? | □ |
| LLM이 만든 코드가 실제로 실행되는가? | □ |
| 컬럼명과 데이터 타입이 실제 데이터와 일치하는가? | □ |
| 병합 기준이 올바른가? | □ |
| 날짜 변환과 결측치 확인 코드가 포함되었는가? | □ |
| 머신러닝 코드에서 데이터 누수가 없는가? | □ |
| 평가 지표가 문제 유형에 맞는가? | □ |
| 해석 문장에서 원인을 단정하지 않았는가? | □ |
| 데이터에 없는 내용을 추측하지 않았는가? | □ |
| LLM 답변을 수정한 내용을 기록했는가? | □ |

검증 체크리스트를 DataFrame으로 만들어 저장할 수도 있습니다.

```python
llm_review_checklist = pd.DataFrame({
    "check_item": [
        "원본 개인정보나 거래 상세를 입력하지 않았는가?",
        "데이터 구조 요약만 입력했는가?",
        "분석 목적을 명확히 작성했는가?",
        "원하는 출력 형식을 지정했는가?",
        "실제 데이터에 없는 컬럼명을 만들지 말라고 요청했는가?",
        "LLM이 만든 코드가 실제로 실행되는가?",
        "컬럼명과 데이터 타입이 실제 데이터와 일치하는가?",
        "병합 기준이 올바른가?",
        "날짜 변환과 결측치 확인 코드가 포함되었는가?",
        "머신러닝 코드에서 데이터 누수가 없는가?",
        "평가 지표가 문제 유형에 맞는가?",
        "해석 문장에서 원인을 단정하지 않았는가?",
        "데이터에 없는 내용을 추측하지 않았는가?",
        "LLM 답변을 수정한 내용을 기록했는가?"
    ],
    "result": ["□"] * 14,
    "memo": [""] * 14
})

llm_review_checklist
```

저장합니다.

```python
llm_review_checklist.to_csv(report_dir / "ch11_llm_review_checklist.csv", index=False)
```

## 11. 프롬프트 로그 남기기

LLM을 분석에 사용했다면 어떤 질문을 입력했고, 어떤 답변을 참고했으며, 어떤 부분을 수정했는지 기록하는 것이 좋습니다. 프롬프트 로그는 분석의 재현성과 신뢰성을 높여 줍니다.

| 항목 | 설명 | 예시 |
| --- | --- | --- |
| 사용 목적 | LLM을 사용한 이유 | 카테고리별 매출 코드 초안 작성 |
| 입력 정보 | 제공한 데이터 구조 | order_items, products 컬럼 목록 |
| 프롬프트 요약 | 핵심 요청 내용 | product_id 병합 후 groupby 요청 |
| 답변 요약 | LLM이 제안한 내용 | merge, groupby, sort_values 코드 |
| 검증 결과 | 사람이 확인한 내용 | 컬럼명은 맞지만 결측치 확인 코드 추가 필요 |
| 수정 내용 | 실제 반영한 수정 | 병합 후 행 수 확인 코드 추가 |
| 최종 사용 여부 | 사용/부분 사용/미사용 | 부분 사용 |

프롬프트 로그를 간단한 표로 만들 수 있습니다.

```python
llm_usage_log = pd.DataFrame({
    "step": [
        "데이터 구조 설명",
        "분석 질문 생성",
        "전처리 계획",
        "시각화 코드 초안",
        "회귀 모델링 코드 초안",
        "분류 모델링 코드 초안",
        "결과 해석 문장 작성"
    ],
    "purpose": [
        "데이터셋 구조를 설명하고 분석 전 확인 사항 정리",
        "현재 데이터로 가능한 분석 질문 생성",
        "결측치, 중복, 날짜 처리 계획 수립",
        "분석 질문에 맞는 그래프와 matplotlib 코드 초안 생성",
        "주문별 총금액 예측 모델 코드 초안 생성",
        "주문 취소 여부 예측 모델 코드 초안 생성",
        "집계 결과를 보고서 문장으로 정리"
    ],
    "validation_point": [
        "실제 컬럼명과 데이터 타입 확인",
        "현재 데이터로 답할 수 있는 질문인지 확인",
        "무조건 삭제나 대체를 제안하지 않았는지 확인",
        "그래프 종류가 분석 질문과 맞는지 확인",
        "데이터 누수와 평가 지표 확인",
        "정답 컬럼이 입력값에 섞이지 않았는지 확인",
        "원인 단정과 과장 표현 확인"
    ]
})

llm_usage_log
```

저장합니다.

```python
llm_usage_log.to_csv(report_dir / "ch11_llm_usage_log.csv", index=False)
```

Markdown 형태의 프롬프트 로그도 만들 수 있습니다.

```python
prompt_log_text = """
# Chapter 11 LLM 프롬프트 로그

## 1. 사용 목적

LLM을 활용해 데이터 구조 설명, 분석 질문 생성, 전처리 계획, 시각화 코드, 머신러닝 코드, 결과 해석 문장의 초안을 만들고 검증했습니다.

## 2. 사용 원칙

- 원본 개인정보와 거래 상세 데이터는 입력하지 않았습니다.
- 컬럼명, 데이터 구조, 집계 결과 중심으로 질문했습니다.
- LLM 답변은 실제 코드 실행과 결과 비교를 통해 검증했습니다.
- 데이터에 없는 원인을 단정하는 문장은 수정했습니다.

## 3. 검증 기준

- 실제 컬럼명과 일치하는가?
- 병합 기준이 올바른가?
- 날짜 변환과 결측치 확인이 포함되었는가?
- 머신러닝 코드에서 데이터 누수가 없는가?
- 해석 문장이 데이터에 근거하는가?
"""

prompt_log_path = report_dir / "ch11_llm_prompt_log.md"
prompt_log_path.write_text(prompt_log_text, encoding="utf-8")
```

## 12. LLM과 함께 분석할 때의 태도

LLM은 분석가를 대체하는 도구가 아니라 분석가의 사고를 확장하는 도구입니다. 좋은 질문을 던지면 더 빠르게 분석 방향을 잡을 수 있고, 코드 초안을 만들 수 있으며, 보고서 문장을 다듬을 수 있습니다. 그러나 최종 결론과 책임은 사람에게 있습니다.

직접 더 연습해 보고 싶다면 다음을 해볼 수 있습니다.

- 현재 데이터셋 구조 요약표를 만들고 LLM에게 분석 질문 10개를 요청합니다.
- LLM이 제안한 질문 중 현재 데이터로 답할 수 없는 질문을 찾아 수정합니다.
- 전처리 계획 프롬프트를 작성하고, 무조건 삭제를 제안하는 답변이 있는지 검토합니다.
- 시각화 프롬프트를 작성하고, 그래프 선택이 분석 질문과 맞는지 검토합니다.
- 회귀 또는 분류 분석 프롬프트를 작성하고, 데이터 누수 가능성을 확인합니다.
- LLM이 작성한 해석 문장에서 원인 단정 표현을 찾아 안전한 문장으로 고칩니다.
- 프롬프트 로그를 작성해 어떤 답변을 실제 분석에 반영했는지 기록합니다.

다음 장에서는 LLM이 생성한 분석 코드와 결과를 더 구체적으로 검토합니다. 코드가 실행되는지뿐 아니라, 컬럼명, 데이터 타입, 병합 기준, 평가 지표, 해석 문장이 실제 분석 목적에 맞는지 확인하는 과정으로 이어집니다.
