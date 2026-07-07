# 12장. LLM이 만든 분석 코드를 검증하는 방법

LLM은 데이터 분석 코드를 빠르게 만들어 줍니다. pandas 집계 코드, 시각화 코드, 머신러닝 모델링 코드, 보고서 초안까지 몇 초 만에 제안할 수 있습니다. 그래서 처음에는 LLM이 분석을 대신해 주는 것처럼 느껴질 수 있습니다.

하지만 데이터 분석에서 중요한 것은 코드가 존재하는 것이 아니라, **그 코드가 현재 데이터 구조에 맞고, 논리적으로 올바르며, 결과를 신뢰할 수 있는지 확인하는 것**입니다. LLM이 만든 코드는 그럴듯해 보이지만 실제 데이터에 없는 컬럼을 사용하거나, 병합 기준을 잘못 잡거나, 타깃 컬럼을 입력값에 포함하는 데이터 누수를 만들 수도 있습니다.

이 장에서는 LLM을 활용해 분석 코드 초안을 만들고, 사람이 그 코드를 어떻게 검토하고 수정해야 하는지 살펴봅니다. 핵심은 LLM에게 코드를 맡기는 것이 아니라, LLM을 빠른 초안 작성자와 코드 리뷰 파트너로 활용하는 것입니다.

## 1. LLM 코드는 초안이다

LLM이 만든 코드는 완성본이 아니라 초안입니다. 초안은 빠르게 방향을 잡는 데 유용하지만, 그대로 프로젝트에 넣기 전에 반드시 검토해야 합니다.

예를 들어 “카테고리별 매출을 계산하는 pandas 코드를 작성해 줘”라고 요청하면 LLM은 다음과 같은 코드를 제안할 수 있습니다.

```python
category_sales = (
    order_items
    .merge(products, on="product_id")
    .groupby("category")
    .agg(total_sales=("line_total", "sum"))
    .reset_index()
)
```

겉으로 보면 자연스러운 코드입니다. 하지만 바로 실행하기 전에 확인해야 할 것이 많습니다.

- `order_items`에 `line_total` 컬럼이 있는가?
- `products`에 `category` 컬럼이 있는가?
- `product_id`가 두 데이터셋에 모두 존재하는가?
- 병합 후 행 수가 예상과 같은가?
- 취소 주문이 매출에 포함되어도 되는가?
- `line_total`이 숫자형인가?

코드가 짧고 보기 좋아도, 검증 없이 사용하면 분석 결과가 틀릴 수 있습니다.

## 2. 좋은 코드 생성 요청은 데이터 구조에서 시작한다

LLM에게 좋은 코드를 받으려면 먼저 데이터 구조를 정확히 알려 주어야 합니다. “매출 분석 코드 작성해 줘”처럼 요청하면 LLM은 컬럼명을 추측할 가능성이 높습니다. 반대로 데이터셋 이름, 컬럼 목록, 분석 목적, 검증 조건을 함께 주면 더 안전한 코드를 얻을 수 있습니다.

코드 생성 전에 정리하면 좋은 정보는 다음과 같습니다.

| 정보 | 예시 |
| --- | --- |
| 데이터셋 이름 | `customers`, `products`, `orders`, `order_items` |
| 주요 컬럼 | `order_id`, `product_id`, `quantity`, `unit_price`, `line_total` |
| 키 관계 | `orders.order_id` ↔ `order_items.order_id` |
| 분석 목적 | 카테고리별 매출 계산 |
| 원하는 결과 | `category`, `total_quantity`, `total_sales`, `sales_ratio` |
| 검증 조건 | 병합 전후 행 수 확인, 누락 카테고리 확인 |
| 제약 조건 | 데이터에 없는 컬럼명 추측 금지 |

원본 데이터 전체를 붙여 넣을 필요는 없습니다. 개인정보, 이메일, 전화번호, API Key, 내부 서버 주소 같은 민감정보는 절대 입력하지 않습니다. LLM에게는 컬럼 구조와 요약 정보만 제공하는 것이 안전합니다.

## 3. 코드 생성을 요청하는 프롬프트 구조

좋은 코드 생성 프롬프트는 분석 목적과 검증 조건을 함께 포함합니다. 다음은 카테고리별 매출 분석 코드를 요청하는 예시입니다.

```text
온라인 쇼핑몰 데이터로 카테고리별 매출을 계산하는 pandas 코드를 작성해 주세요.

데이터 구조:
- products: product_id, product_name, category, price
- order_items: order_id, product_id, quantity, unit_price, line_total

목표:
- product_id를 기준으로 products와 order_items를 병합합니다.
- category별 total_quantity와 total_sales를 계산합니다.
- total_sales 기준 내림차순으로 정렬합니다.
- 전체 매출 대비 sales_ratio를 계산합니다.

검증 조건:
- 병합 전후 행 수를 출력해 주세요.
- 병합 후 category 결측치 개수를 출력해 주세요.
- line_total이 없으면 quantity * unit_price로 생성하는 코드를 포함해 주세요.

제약 조건:
- 위에 없는 컬럼명은 사용하지 마세요.
- 코드에는 초보자가 이해할 수 있는 주석을 포함해 주세요.
```

이 프롬프트의 핵심은 “코드를 작성해 달라”에서 끝나지 않는다는 점입니다. 병합 검증, 결측치 확인, 없는 컬럼 처리, 컬럼명 추측 금지까지 함께 요청하고 있습니다.

## 4. LLM 코드의 첫 번째 검증: 실행 전 점검

LLM이 만든 코드를 받으면 바로 실행하지 말고 먼저 읽어야 합니다. 실행 전 점검은 코드가 현재 데이터 구조와 맞는지 확인하는 단계입니다.

실행 전에는 다음 항목을 봅니다.

| 점검 항목 | 확인할 질문 |
| --- | --- |
| 데이터셋 이름 | 실제 Notebook에 존재하는 변수명인가? |
| 컬럼명 | 실제 데이터에 있는 컬럼인가? |
| 병합 기준 | 두 데이터셋에 모두 존재하는 키인가? |
| 타깃 컬럼 | 예측해야 할 정답을 입력값에 넣고 있지 않은가? |
| 날짜 처리 | 문자열 날짜를 날짜형으로 바꾸고 있는가? |
| 숫자형 처리 | 쉼표가 있는 문자열 숫자를 처리하고 있는가? |
| 개인정보 | 고객명, 이메일, 전화번호를 불필요하게 출력하지 않는가? |
| 파일 경로 | 현재 프로젝트 구조와 맞는 경로인가? |

예를 들어 다음 코드는 실행 전에 문제가 보입니다.

```python
sales = orders.merge(products, on="product_id")
```

`orders`에는 보통 `product_id`가 없습니다. 상품은 주문 상세 데이터인 `order_items`에 연결되어 있습니다. 따라서 카테고리별 매출을 계산하려면 `order_items`와 `products`를 먼저 병합해야 합니다.

수정 방향은 다음과 같습니다.

```python
sales_items = order_items.merge(
    products,
    on="product_id",
    how="left"
)
```

LLM 코드에서 가장 흔한 오류는 “그럴듯한 컬럼명과 병합 구조를 추측하는 것”입니다. 그래서 실행 전에는 컬럼명과 키 관계를 먼저 확인합니다.

## 5. LLM 코드의 두 번째 검증: 실행 후 점검

코드가 실행되었다고 해서 분석이 맞는 것은 아닙니다. 실행 후에는 결과가 논리적으로 맞는지 확인해야 합니다.

병합 코드를 실행했다면 행 수와 결측치를 확인합니다.

```python
print("병합 전 order_items:", order_items.shape)
print("병합 후 sales_items:", sales_items.shape)
print("카테고리 누락:", sales_items["category"].isna().sum())
```

집계 결과를 만들었다면 총합이 맞는지도 확인합니다.

```python
raw_total_sales = order_items["line_total"].sum()
grouped_total_sales = category_sales["total_sales"].sum()

print("원본 총매출:", raw_total_sales)
print("집계 총매출:", grouped_total_sales)
print("차이:", raw_total_sales - grouped_total_sales)
```

월별 결과라면 시간순으로 정렬되어 있는지 확인합니다.

```python
monthly_sales = monthly_sales.sort_values("order_month")
monthly_sales
```

분류 모델이라면 accuracy만 보지 않고 precision, recall, f1-score를 함께 확인합니다. 특히 주문 취소 여부 예측처럼 클래스가 불균형할 수 있는 문제에서는 accuracy만으로는 부족합니다.

## 6. pandas 코드 검증 예시

LLM에게 월별 매출 코드를 요청했다고 가정해 보겠습니다. LLM이 다음 코드를 만들 수 있습니다.

```python
monthly_sales = (
    order_items
    .merge(orders, on="order_id")
    .groupby("order_month")
    .agg(total_sales=("line_total", "sum"))
    .reset_index()
)
```

이 코드는 실행될 수도 있지만 몇 가지를 확인해야 합니다.

- `orders`에 `order_month`가 이미 있는가?
- 없다면 `order_date`에서 만들어야 하는가?
- `order_date`는 날짜형인가?
- 취소 주문을 포함할 것인가?
- 월별 주문 수와 평균 주문 금액도 함께 볼 것인가?

더 안전한 코드는 다음처럼 작성할 수 있습니다.

```python
order_sales = order_items.merge(
    orders,
    on="order_id",
    how="left"
)

print("병합 전 order_items:", order_items.shape)
print("병합 후 order_sales:", order_sales.shape)
print("order_date 누락:", order_sales["order_date"].isna().sum())

order_sales["order_date"] = pd.to_datetime(order_sales["order_date"], errors="coerce")
order_sales["order_month"] = order_sales["order_date"].dt.to_period("M").astype(str)

monthly_sales = (
    order_sales
    .groupby("order_month", as_index=False)
    .agg(
        total_sales=("line_total", "sum"),
        order_count=("order_id", "nunique")
    )
    .sort_values("order_month")
)

monthly_sales["avg_order_value"] = (
    monthly_sales["total_sales"] / monthly_sales["order_count"]
).round(0)

monthly_sales
```

좋은 분석 코드는 계산만 하지 않습니다. 중간 검증을 포함하고, 결과 해석에 필요한 보조 지표도 함께 만듭니다.

## 7. 머신러닝 코드 검증 예시

LLM이 머신러닝 코드를 만들 때는 데이터 누수와 평가 지표를 특히 조심해야 합니다. 주문 취소 여부를 예측하는 분류 모델에서 다음 코드는 위험합니다.

```python
features = ["payment_method", "order_status", "order_amount"]
X = model_data[features]
y = model_data["is_cancelled"]
```

`order_status`는 `is_cancelled`를 만들 때 사용한 정답 정보입니다. 이 컬럼을 입력값에 넣으면 모델은 정답을 미리 보고 학습하는 셈입니다. 이런 모델은 테스트 성능이 높게 나와도 실제 예측에는 사용할 수 없습니다.

수정된 입력값 구성은 다음처럼 정리할 수 있습니다.

```python
features = [
    "payment_method",
    "order_amount",
    "item_count",
    "total_quantity",
    "order_month",
    "order_dayofweek"
]

features = [col for col in features if col in model_data.columns]

X = model_data[features]
y = model_data["is_cancelled"]
```

모델 평가에서도 accuracy만 출력하는 코드는 부족합니다.

```python
from sklearn.metrics import classification_report, confusion_matrix

print(classification_report(y_test, y_pred, zero_division=0))
print(confusion_matrix(y_test, y_pred))
```

LLM이 모델링 코드를 제안하면 다음을 반드시 확인합니다.

| 검증 항목 | 확인할 내용 |
| --- | --- |
| 타깃 정의 | 무엇을 예측하는지 명확한가? |
| 데이터 누수 | 정답 또는 정답에서 파생된 컬럼이 입력값에 들어가지 않았는가? |
| 학습/테스트 분리 | `train_test_split`을 사용했는가? |
| 전처리 위치 | 테스트 데이터를 미리 학습에 사용하지 않았는가? |
| 범주형 처리 | OneHotEncoder 등 적절한 처리가 있는가? |
| 결측치 처리 | 학습 파이프라인 안에서 처리하는가? |
| 평가 지표 | 문제 유형에 맞는 지표를 사용하는가? |
| 해석 | 상관관계나 예측 결과를 원인으로 단정하지 않는가? |

## 8. 오류 메시지는 수정 프롬프트의 재료다

LLM 코드가 한 번에 잘 실행되지 않는 것은 자연스러운 일입니다. 오류가 발생하면 오류 메시지를 그대로 붙여 넣기보다, 현재 상황을 함께 정리해 질문하는 것이 좋습니다.

```text
다음 pandas 코드에서 오류가 발생했습니다.

목표:
- products와 order_items를 product_id 기준으로 병합해 카테고리별 매출을 계산하려고 합니다.

현재 데이터 컬럼:
- products: product_id, product_name, category, price
- order_items: order_id, product_id, quantity, unit_price, line_total

실행한 코드:
[여기에 코드 붙여넣기]

오류 메시지:
[여기에 오류 메시지 붙여넣기]

요청:
1. 오류 원인을 초보자도 이해할 수 있게 설명해 주세요.
2. 실제 컬럼명만 사용해 수정 코드를 제안해 주세요.
3. 병합 후 행 수와 category 결측치 확인 코드도 포함해 주세요.
4. 데이터에 없는 컬럼명은 새로 만들지 마세요.
```

오류 수정 프롬프트는 “고쳐 줘”보다 “무엇을 하려 했는지, 어떤 데이터 구조인지, 어떤 오류가 났는지”를 함께 설명해야 합니다.

## 9. 코드 리뷰 체크리스트 만들기

LLM을 분석 과정에 자주 사용하려면 매번 감으로 검토하기보다 체크리스트를 만들어 두는 것이 좋습니다.

```python
code_review_checklist = pd.DataFrame({
    "category": [
        "데이터 구조",
        "데이터 구조",
        "병합",
        "병합",
        "전처리",
        "전처리",
        "머신러닝",
        "머신러닝",
        "해석",
        "보안"
    ],
    "check_item": [
        "실제 데이터셋 이름을 사용했는가?",
        "실제 컬럼명만 사용했는가?",
        "병합 기준 컬럼이 양쪽 데이터에 모두 존재하는가?",
        "병합 전후 행 수를 확인했는가?",
        "날짜와 숫자형 변환 실패를 확인했는가?",
        "결측치와 중복을 무시하지 않았는가?",
        "타깃 컬럼이 명확하게 정의되었는가?",
        "데이터 누수가 없는가?",
        "결과를 원인으로 단정하지 않았는가?",
        "개인정보나 API Key가 코드와 프롬프트에 포함되지 않았는가?"
    ],
    "status": ["미확인"] * 10
})

code_review_checklist
```

체크리스트는 CSV로 저장해 둘 수 있습니다.

```python
report_dir = Path("reports")
report_dir.mkdir(exist_ok=True)

code_review_checklist.to_csv(
    report_dir / "ch12_llm_code_review_checklist.csv",
    index=False
)
```

## 10. 검증 결과를 짧은 보고서로 남긴다

LLM이 만든 코드를 사용했다면 어떤 프롬프트를 사용했고, 어떤 부분을 수정했으며, 최종적으로 어떻게 검증했는지 기록해 두는 것이 좋습니다. 이는 프로젝트의 신뢰도를 높입니다.

```python
validation_summary = """
# Chapter 12 LLM 코드 생성과 검증 요약

## 1. 코드 생성 목적

LLM을 활용해 온라인 쇼핑몰 데이터의 카테고리별 매출, 월별 매출, 주문 취소 여부 예측 코드를 생성하고 검토했습니다.

## 2. 검토 기준

- 실제 데이터셋 이름과 컬럼명을 사용했는지 확인했습니다.
- 병합 기준과 병합 전후 행 수를 확인했습니다.
- 날짜형과 숫자형 변환 여부를 확인했습니다.
- 머신러닝 코드에서는 데이터 누수가 없는지 확인했습니다.
- 분류 모델에서는 accuracy 외 precision, recall, f1-score를 함께 확인했습니다.
- 보고서 해석에서는 데이터에 없는 원인을 단정하지 않도록 수정했습니다.

## 3. 수정한 주요 내용

- 존재하지 않는 컬럼명을 실제 컬럼명으로 수정했습니다.
- 병합 후 결측치 확인 코드를 추가했습니다.
- order_status가 feature에 포함되지 않도록 제거했습니다.
- 모델 평가 지표에 classification_report와 confusion_matrix를 추가했습니다.

## 4. 주의할 점

LLM이 만든 코드는 초안으로만 사용해야 하며, 최종 코드는 실제 데이터 구조와 실행 결과를 기준으로 사람이 검증해야 합니다.
"""

(report_dir / "ch12_code_validation_summary.md").write_text(
    validation_summary,
    encoding="utf-8"
)
```

이런 검증 기록은 단순한 부록이 아닙니다. LLM을 활용한 분석에서 어떤 부분을 사람이 확인했는지 보여 주는 중요한 근거가 됩니다.

## 11. LLM 코드 활용의 안전한 원칙

LLM을 데이터 분석에 활용할 때는 다음 원칙을 기억하는 것이 좋습니다.

| 원칙 | 설명 |
| --- | --- |
| 구조를 먼저 제공한다 | 데이터셋과 컬럼명을 정확히 알려 준다 |
| 민감정보는 제거한다 | 원본 개인정보, API Key, 내부 정보는 입력하지 않는다 |
| 코드는 바로 실행하지 않는다 | 실행 전 컬럼명, 병합 기준, 타깃 정의를 읽는다 |
| 결과를 다시 계산해 본다 | 총합, 행 수, 결측치, 클래스 비율을 확인한다 |
| 모델 평가는 문제에 맞게 한다 | 회귀와 분류의 지표를 구분한다 |
| 해석은 사람이 책임진다 | LLM의 원인 단정과 과장 표현을 수정한다 |
| 검증 과정을 기록한다 | 사용한 프롬프트와 수정 내용을 남긴다 |

LLM은 분석 속도를 높여 줄 수 있지만, 분석의 책임을 대신 지지는 않습니다. 좋은 분석자는 LLM이 만든 초안을 빠르게 받아들이는 사람이 아니라, 그 초안을 현재 데이터와 분석 목적에 맞게 검증하고 고칠 수 있는 사람입니다.

## 12. 다음 장으로 이어지는 흐름

이번 장에서는 LLM이 만든 분석 코드를 어떻게 생성하고 검증할지 살펴보았습니다. 이제 LLM은 단순한 질문 응답 도구가 아니라, 전처리 코드, 집계 코드, 시각화 코드, 모델링 코드의 초안을 만드는 협업 도구가 되었습니다.

다음 장에서는 분석 프로젝트를 더 넓은 데이터로 확장합니다. 공공데이터, 네이버 API, 간단한 크롤링을 통해 외부 데이터를 수집하고, 기존 분석 데이터와 연결하는 방법을 살펴봅니다. 외부 데이터를 사용할 때도 원칙은 같습니다. 데이터를 가져오는 것보다 중요한 것은 데이터의 출처, 구조, 품질, 사용 가능 범위를 확인하는 것입니다.
