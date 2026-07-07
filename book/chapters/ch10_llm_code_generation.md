# 10장. 분류 분석으로 주문 취소 여부 예측하기

회귀 분석이 숫자를 예측하는 문제라면, 분류 분석은 여러 범주 중 하나를 예측하는 문제입니다. 예를 들어 내일 비가 올지 말지, 고객이 이탈할지 유지될지, 이메일이 스팸인지 정상인지, 주문이 취소될지 완료될지와 같은 문제는 모두 분류 문제로 볼 수 있습니다.

이 장에서는 온라인 쇼핑몰 데이터를 사용해 **주문 취소 여부를 예측하는 분류 모델**을 만들어 봅니다. 목표는 복잡한 모델을 완성하는 것이 아니라, 분류 분석의 기본 흐름을 이해하는 것입니다. 무엇을 예측할 것인지 정하고, 입력값으로 사용할 컬럼을 고르고, 학습용 데이터와 테스트용 데이터를 나눈 뒤, 모델의 예측 결과를 평가합니다.

분류 분석에서 중요한 것은 단순히 정확도 하나만 보는 것이 아닙니다. 특히 취소 주문처럼 비율이 낮을 수 있는 대상을 예측할 때는 precision, recall, f1-score 같은 지표를 함께 봐야 합니다. 모델이 “대부분 완료 주문”이라고만 예측해도 정확도는 높아 보일 수 있기 때문입니다.

이 장의 흐름은 다음과 같습니다.

1. 분류 문제가 무엇인지 이해한다.
2. 주문 취소 여부를 예측 대상으로 정의한다.
3. 고객, 주문, 주문 상세 데이터를 연결해 분석용 데이터를 만든다.
4. 범주형 컬럼과 숫자형 컬럼을 나누어 전처리한다.
5. Logistic Regression과 RandomForestClassifier 모델을 학습한다.
6. accuracy, precision, recall, f1-score, confusion matrix로 결과를 해석한다.
7. LLM이 만든 분류 코드를 어떻게 검토해야 하는지 정리한다.

## 1. 분류 분석은 범주를 예측한다

분류 분석은 결과가 몇 개의 범주 중 하나로 나뉘는 문제를 다룹니다. 숫자를 예측하는 회귀와 달리, 분류는 “어느 쪽인가”를 예측합니다.

| 문제 | 예측 대상 | 분류 유형 |
| --- | --- | --- |
| 주문이 취소될 것인가? | 취소 / 완료 | 이진 분류 |
| 고객이 이탈할 것인가? | 이탈 / 유지 | 이진 분류 |
| 이메일은 어떤 유형인가? | 스팸 / 정상 / 프로모션 | 다중 분류 |
| 상품 리뷰 감성은 어떤가? | 긍정 / 중립 / 부정 | 다중 분류 |

이번 장에서는 주문 상태를 바탕으로 `is_cancelled`라는 이진 타깃을 만듭니다. 주문이 취소된 경우는 1, 그렇지 않은 경우는 0으로 표시합니다.

분류 분석에서 먼저 생각해야 할 질문은 다음과 같습니다.

- 무엇을 예측할 것인가?
- 예측 시점에 실제로 알 수 있는 정보는 무엇인가?
- 어떤 컬럼을 입력값으로 사용할 수 있는가?
- 정답 범주의 비율은 균형적인가?
- 모델이 틀렸을 때 어떤 오류가 더 중요한가?

예를 들어 주문 취소를 예측하려는 모델에서 `order_status`를 입력값으로 사용하면 안 됩니다. `order_status`는 예측해야 할 정답 그 자체이기 때문입니다. 이런 식으로 정답을 알려 주는 컬럼을 입력값에 포함하면 모델 성능이 매우 높게 보이지만, 실제 예측 모델로는 사용할 수 없습니다. 이를 데이터 누수(data leakage)라고 합니다.

## 2. 주문 취소 여부 예측 데이터 만들기

먼저 필요한 패키지를 불러옵니다.

```python
from pathlib import Path
import pandas as pd
import numpy as np
```

VS Code에서 Notebook을 실행할 때는 현재 실행 위치에 따라 상대 경로가 달라질 수 있습니다. 다음 코드는 프로젝트 루트와 `notebooks` 폴더 실행을 모두 고려합니다.

```python
current_dir = Path.cwd()

if current_dir.name == "notebooks":
    base_dir = current_dir.parent
else:
    base_dir = current_dir

processed_dir = base_dir / "data" / "processed"
report_dir = base_dir / "reports"
report_dir.mkdir(exist_ok=True)
```

Chapter 5와 8에서 저장한 전처리 데이터를 불러옵니다.

```python
customers = pd.read_csv(processed_dir / "customers_clean.csv")
products = pd.read_csv(processed_dir / "products_clean.csv")
orders = pd.read_csv(processed_dir / "orders_clean.csv")
order_items = pd.read_csv(processed_dir / "order_items_clean.csv")
```

날짜 컬럼은 CSV로 저장했다가 다시 불러오면 문자열로 돌아올 수 있습니다. 필요한 컬럼은 다시 날짜형으로 변환합니다.

```python
orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")

if "signup_date" in customers.columns:
    customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="coerce")
```

주문 상태값을 확인합니다.

```python
orders["order_status"].value_counts()
```

주문 취소 여부를 나타내는 타깃 컬럼을 만듭니다.

```python
orders["is_cancelled"] = (orders["order_status"] == "cancelled").astype(int)
orders["is_cancelled"].value_counts(normalize=True).round(3)
```

이 비율은 매우 중요합니다. 취소 주문이 전체 주문의 5%뿐이라면, 모든 주문을 “취소 아님”으로 예측해도 정확도는 95%가 됩니다. 그래서 분류 문제에서는 정답 비율을 먼저 확인해야 합니다.

## 3. 주문 단위 특징 만들기

주문 상세 데이터는 한 주문 안에 여러 상품이 들어 있을 수 있기 때문에 `order_id` 기준으로 집계해야 합니다. 주문별 상품 개수, 총 수량, 주문 금액을 만듭니다.

```python
order_item_features = (
    order_items
    .groupby("order_id", as_index=False)
    .agg(
        item_count=("product_id", "count"),
        total_quantity=("quantity", "sum"),
        order_amount=("line_total", "sum")
    )
)

order_item_features.head()
```

주문 데이터에 주문 상세 특징을 붙입니다.

```python
model_data = orders.merge(
    order_item_features,
    on="order_id",
    how="left"
)
```

고객 정보도 연결합니다.

```python
model_data = model_data.merge(
    customers,
    on="customer_id",
    how="left"
)
```

병합 후에는 항상 행 수와 누락값을 확인합니다.

```python
print("orders:", orders.shape)
print("model_data:", model_data.shape)
print(model_data[["item_count", "total_quantity", "order_amount"]].isna().sum())
```

주문 상세가 없는 주문이 있다면 집계값이 비어 있을 수 있습니다. 실습에서는 0으로 채우겠습니다.

```python
for col in ["item_count", "total_quantity", "order_amount"]:
    if col in model_data.columns:
        model_data[col] = model_data[col].fillna(0)
```

날짜에서 월과 요일을 추출합니다.

```python
model_data["order_month"] = model_data["order_date"].dt.month
model_data["order_dayofweek"] = model_data["order_date"].dt.dayofweek
```

가입일이 있는 경우 주문일과 가입일 사이의 기간을 만들 수 있습니다.

```python
if "signup_date" in model_data.columns:
    model_data["days_since_signup"] = (
        model_data["order_date"] - model_data["signup_date"]
    ).dt.days
```

`days_since_signup`에 결측치가 있으면 중앙값으로 채웁니다.

```python
if "days_since_signup" in model_data.columns:
    model_data["days_since_signup"] = model_data["days_since_signup"].fillna(
        model_data["days_since_signup"].median()
    )
```

## 4. 입력값과 정답을 나눈다

분류 모델을 만들 때는 입력값 `X`와 정답 `y`를 분리합니다. 여기서 가장 주의해야 할 점은 정답을 직접 알려 주는 컬럼을 입력값에 넣지 않는 것입니다.

이번 실습에서는 다음과 같은 컬럼을 후보 입력값으로 사용합니다. 실제 저장소의 데이터 구조에 따라 일부 컬럼은 없을 수 있으므로, 존재하는 컬럼만 선택합니다.

```python
candidate_numeric_features = [
    "age",
    "item_count",
    "total_quantity",
    "order_amount",
    "order_month",
    "order_dayofweek",
    "days_since_signup"
]

candidate_categorical_features = [
    "gender",
    "city",
    "payment_method"
]

numeric_features = [col for col in candidate_numeric_features if col in model_data.columns]
categorical_features = [col for col in candidate_categorical_features if col in model_data.columns]

features = numeric_features + categorical_features
features
```

정답 컬럼은 `is_cancelled`입니다. `order_status`는 정답을 만드는 데 사용했기 때문에 입력값에서 제외합니다.

```python
X = model_data[features].copy()
y = model_data["is_cancelled"].copy()
```

입력값의 결측치를 간단히 확인합니다.

```python
X.isna().sum()
```

## 5. 학습 데이터와 테스트 데이터를 나눈다

모델은 학습에 사용한 데이터에서 잘 맞는 것만으로는 충분하지 않습니다. 처음 보는 데이터에서도 어느 정도 맞아야 합니다. 그래서 데이터를 학습용과 테스트용으로 나눕니다.

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)
```

`stratify=y`는 학습 데이터와 테스트 데이터에서 취소 주문 비율이 비슷하게 유지되도록 도와줍니다. 분류 문제에서는 타깃 비율이 중요한 경우가 많기 때문에 자주 사용합니다.

```python
print("train target ratio")
print(y_train.value_counts(normalize=True).round(3))

print("test target ratio")
print(y_test.value_counts(normalize=True).round(3))
```

## 6. 범주형 컬럼과 숫자형 컬럼을 함께 처리한다

머신러닝 모델은 대부분 숫자형 입력을 사용합니다. 나이, 주문 금액, 상품 수량 같은 숫자형 컬럼은 그대로 사용할 수 있지만, 도시나 결제수단 같은 범주형 컬럼은 숫자 형태로 바꿔야 합니다.

scikit-learn의 `ColumnTransformer`와 `Pipeline`을 사용하면 숫자형 처리, 범주형 처리, 모델 학습을 하나의 흐름으로 묶을 수 있습니다.

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ]
)
```

숫자형 컬럼에는 중앙값 대체와 표준화를 적용하고, 범주형 컬럼에는 최빈값 대체와 원-핫 인코딩을 적용합니다. `handle_unknown="ignore"`는 테스트 데이터에 학습 데이터에서 보지 못한 범주가 등장해도 오류가 나지 않도록 합니다.

## 7. Logistic Regression으로 기준 모델 만들기

먼저 Logistic Regression을 사용해 기준 모델을 만듭니다. 이름에 Regression이 들어가지만, Logistic Regression은 분류 모델입니다.

```python
from sklearn.linear_model import LogisticRegression

logistic_model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", LogisticRegression(max_iter=1000, class_weight="balanced"))
])

logistic_model.fit(X_train, y_train)
```

`class_weight="balanced"`는 취소 주문처럼 소수 클래스가 있을 때 어느 정도 균형을 맞춰 주는 옵션입니다. 항상 좋은 결과를 보장하지는 않지만, 불균형 분류 문제에서 시도해 볼 수 있습니다.

예측을 수행합니다.

```python
y_pred_logistic = logistic_model.predict(X_test)
```

## 8. 분류 모델은 여러 지표로 평가한다

분류 모델 평가는 정확도 하나로 끝내면 위험합니다. 특히 취소 주문처럼 비율이 낮은 대상을 예측할 때는 precision, recall, f1-score를 함께 봐야 합니다.

```python
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

logistic_metrics = {
    "accuracy": accuracy_score(y_test, y_pred_logistic),
    "precision": precision_score(y_test, y_pred_logistic, zero_division=0),
    "recall": recall_score(y_test, y_pred_logistic, zero_division=0),
    "f1": f1_score(y_test, y_pred_logistic, zero_division=0)
}

logistic_metrics
```

각 지표의 의미는 다음과 같습니다.

| 지표 | 의미 | 해석할 때 주의할 점 |
| --- | --- | --- |
| accuracy | 전체 예측 중 맞춘 비율 | 클래스 불균형이 있으면 높게 보일 수 있음 |
| precision | 취소라고 예측한 것 중 실제 취소 비율 | 잘못된 취소 예측을 줄이고 싶을 때 중요 |
| recall | 실제 취소 중 모델이 찾아낸 비율 | 취소 주문을 놓치지 않는 것이 중요할 때 사용 |
| f1-score | precision과 recall의 균형 | 두 지표를 함께 보고 싶을 때 사용 |

혼동행렬도 확인합니다.

```python
confusion_matrix(y_test, y_pred_logistic)
```

더 자세한 보고서는 다음 코드로 볼 수 있습니다.

```python
print(classification_report(y_test, y_pred_logistic, zero_division=0))
```

혼동행렬은 보통 다음처럼 읽습니다.

| 구분 | 의미 |
| --- | --- |
| True Negative | 실제 완료 주문을 완료로 예측 |
| False Positive | 실제 완료 주문을 취소로 잘못 예측 |
| False Negative | 실제 취소 주문을 완료로 잘못 예측 |
| True Positive | 실제 취소 주문을 취소로 예측 |

분류 모델에서는 어떤 오류가 더 중요한지 생각해야 합니다. 취소 주문을 놓치는 것이 더 문제인지, 정상 주문을 취소 위험으로 잘못 분류하는 것이 더 문제인지에 따라 모델 선택 기준이 달라집니다.

## 9. Random Forest로 비교 모델 만들기

이번에는 RandomForestClassifier를 사용해 비교 모델을 만들어 보겠습니다. Random Forest는 여러 개의 의사결정나무를 사용해 예측하는 모델입니다. 범주형 변수는 앞에서 OneHotEncoder로 숫자형으로 바꿔 사용합니다.

```python
from sklearn.ensemble import RandomForestClassifier

rf_model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    ))
])

rf_model.fit(X_train, y_train)
```

```python
y_pred_rf = rf_model.predict(X_test)
```

평가 지표를 계산합니다.

```python
rf_metrics = {
    "accuracy": accuracy_score(y_test, y_pred_rf),
    "precision": precision_score(y_test, y_pred_rf, zero_division=0),
    "recall": recall_score(y_test, y_pred_rf, zero_division=0),
    "f1": f1_score(y_test, y_pred_rf, zero_division=0)
}

rf_metrics
```

두 모델의 결과를 비교합니다.

```python
model_comparison = pd.DataFrame([
    {"model": "Logistic Regression", **logistic_metrics},
    {"model": "Random Forest", **rf_metrics}
])

model_comparison
```

결과를 저장합니다.

```python
model_comparison.to_csv(report_dir / "ch10_classification_model_comparison.csv", index=False)
```

모델 비교에서는 단순히 수치가 높은 모델을 고르는 것이 아니라, 어떤 지표가 중요한지 먼저 정해야 합니다. 취소 주문을 최대한 많이 찾아야 한다면 recall이 중요할 수 있고, 취소 위험 알림의 정확도를 높이고 싶다면 precision이 더 중요할 수 있습니다.

## 10. 예측 확률과 임계값

분류 모델은 보통 범주 예측뿐 아니라 예측 확률도 제공합니다. 예를 들어 어떤 주문이 취소될 확률이 0.72라고 계산될 수 있습니다.

```python
y_proba_rf = rf_model.predict_proba(X_test)[:, 1]
```

기본적으로는 확률이 0.5 이상이면 1, 즉 취소로 예측합니다. 하지만 상황에 따라 임계값을 조정할 수 있습니다.

```python
threshold = 0.3
y_pred_rf_03 = (y_proba_rf >= threshold).astype(int)

threshold_metrics = {
    "threshold": threshold,
    "accuracy": accuracy_score(y_test, y_pred_rf_03),
    "precision": precision_score(y_test, y_pred_rf_03, zero_division=0),
    "recall": recall_score(y_test, y_pred_rf_03, zero_division=0),
    "f1": f1_score(y_test, y_pred_rf_03, zero_division=0)
}

threshold_metrics
```

임계값을 낮추면 더 많은 주문을 취소 위험으로 잡아낼 수 있어 recall이 올라갈 수 있습니다. 대신 실제로는 취소되지 않을 주문까지 취소 위험으로 예측해 precision이 낮아질 수 있습니다. 이 균형을 이해하는 것이 분류 모델 해석의 핵심입니다.

## 11. 결과를 보고서 문장으로 바꾸기

모델 평가 결과는 숫자로만 남기지 않고 해석 문장으로 정리해야 합니다. 예를 들어 다음과 같이 쓸 수 있습니다.

```text
Logistic Regression과 Random Forest를 사용해 주문 취소 여부를 예측했습니다.
모델 평가는 accuracy, precision, recall, f1-score를 함께 비교했습니다.
취소 주문 비율이 낮은 경우 accuracy만으로는 모델 성능을 판단하기 어렵기 때문에, 실제 취소 주문을 얼마나 잘 찾아내는지를 나타내는 recall을 함께 확인했습니다.
```

모델 결과를 해석할 때는 다음 표현을 피하는 것이 좋습니다.

```text
이 모델은 주문 취소 원인을 설명한다.
이 모델은 고객이 왜 취소하는지 알려 준다.
이 모델은 앞으로 모든 주문 취소를 정확히 예측한다.
```

현재 모델은 주어진 입력값과 취소 여부 사이의 패턴을 학습한 것입니다. 취소의 원인을 증명하거나 미래의 모든 상황을 정확히 설명하는 것은 아닙니다.

## 12. LLM과 함께 분류 코드를 검토한다

LLM은 분류 모델 코드 초안을 만들거나 오류를 설명하는 데 도움이 됩니다. 하지만 모델링 코드는 실행만 된다고 안전한 것이 아닙니다. 데이터 누수, 잘못된 타깃, 부적절한 평가 지표, 불균형 데이터 문제를 놓칠 수 있습니다.

LLM에게 분류 코드를 요청할 때는 다음처럼 질문할 수 있습니다.

```text
온라인 쇼핑몰 주문 데이터로 주문 취소 여부를 예측하는 이진 분류 모델을 만들고 싶습니다.

데이터 구조:
- orders: order_id, customer_id, order_date, payment_method, order_status
- customers: customer_id, gender, age, city, signup_date
- order_items: order_id, product_id, quantity, unit_price, line_total

목표:
- order_status가 cancelled이면 1, 그렇지 않으면 0인 is_cancelled를 만듭니다.
- order_status는 입력 feature로 사용하지 않습니다.
- Logistic Regression과 RandomForestClassifier를 비교합니다.
- train/test split에는 stratify=y를 사용합니다.
- accuracy, precision, recall, f1-score, confusion matrix를 출력합니다.

주의:
- 데이터에 없는 컬럼명을 만들지 마세요.
- 데이터 누수가 생기지 않도록 설명해 주세요.
- 각 단계에 초보자용 주석을 포함해 주세요.
```

LLM이 만든 코드는 다음 기준으로 검토합니다.

| 검토 기준 | 확인할 질문 |
| --- | --- |
| 타깃 정의 | `is_cancelled`가 올바르게 만들어졌는가? |
| 데이터 누수 | `order_status`를 입력값으로 사용하지 않았는가? |
| 데이터 분할 | `train_test_split`을 먼저 수행했는가? |
| 클래스 비율 | `stratify=y` 또는 클래스 비율 확인이 있는가? |
| 범주형 처리 | `OneHotEncoder` 등으로 범주형 컬럼을 처리했는가? |
| 결측치 처리 | 학습 파이프라인 안에서 결측치를 처리했는가? |
| 평가 지표 | accuracy 외 precision, recall, f1-score를 함께 보았는가? |
| 해석 | 모델 결과를 원인으로 단정하지 않았는가? |

분류 모델은 숫자가 그럴듯하게 나오기 쉽습니다. 그래서 LLM이 만든 코드일수록 더 꼼꼼히 검토해야 합니다.

## 13. 다음 장으로 이어지는 흐름

이번 장에서는 주문 취소 여부를 예측하는 분류 분석의 기본 흐름을 살펴보았습니다. 회귀 분석과 마찬가지로 분류 분석도 좋은 데이터와 명확한 질문에서 시작합니다. 차이는 예측 대상이 숫자가 아니라 범주라는 점입니다.

이제 데이터 분석의 기본 체력, 회귀, 분류 모델링까지 경험했습니다. 다음 장부터는 LLM을 데이터 분석 과정에 더 본격적으로 연결합니다. LLM은 분석 질문을 정리하고, 전처리와 시각화 코드 초안을 만들고, 모델 결과 해석을 도와줄 수 있습니다. 다만 지금까지 배운 것처럼 최종 판단과 검증은 사람이 해야 합니다.
