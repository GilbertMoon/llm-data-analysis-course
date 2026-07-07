# 9장. 회귀 분석으로 숫자 예측하기

지금까지는 데이터를 불러오고, 정리하고, 질문을 만들고, 그래프로 확인하는 과정을 살펴보았습니다. 이 과정은 주로 “무슨 일이 있었는가”를 이해하는 데 초점을 둡니다. 이제 한 걸음 더 나아가 “앞으로 어떤 값이 나올 수 있는가”를 예측해 보겠습니다.

회귀 분석은 숫자를 예측하는 머신러닝 문제입니다. 예를 들어 온라인 쇼핑몰 데이터에서는 주문 금액, 상품 매출, 고객별 구매 금액 같은 값을 예측 대상으로 삼을 수 있습니다. 이번 장에서는 복잡한 수학 이론보다, 데이터 분석 프로젝트에서 회귀 모델이 어떤 흐름으로 만들어지는지 이해하는 데 집중합니다.

회귀 모델은 마법처럼 정답을 맞히는 도구가 아닙니다. 과거 데이터의 패턴을 학습해 새로운 데이터의 숫자 값을 추정하는 도구입니다. 따라서 어떤 값을 예측할지, 어떤 컬럼을 입력값으로 사용할지, 모델이 얼마나 잘 맞는지 어떻게 평가할지 사람이 신중하게 결정해야 합니다.

## 이 장에서 생각해 볼 질문

회귀 분석을 시작하기 전에 다음 질문을 먼저 생각해 봅니다.

- 우리는 어떤 숫자를 예측하려고 하는가?
- 예측 대상이 되는 값은 데이터에 실제로 존재하는가?
- 예측에 사용할 수 있는 입력 컬럼은 무엇인가?
- 학습 데이터와 테스트 데이터를 왜 나눠야 하는가?
- 모델의 예측 오차는 어떻게 해석해야 하는가?
- 선형 회귀와 랜덤 포레스트 회귀는 어떤 차이가 있는가?
- LLM이 만든 회귀 분석 코드는 어떻게 검증해야 하는가?

## 1. 회귀 분석이란 무엇인가

회귀 분석은 연속적인 숫자 값을 예측하는 문제입니다. “맞다/아니다”처럼 범주를 예측하는 분류와 달리, 회귀는 금액, 수량, 점수, 온도, 시간처럼 숫자로 표현되는 값을 예측합니다.

온라인 쇼핑몰 데이터에서는 다음과 같은 회귀 문제를 생각해 볼 수 있습니다.

| 예측 질문 | 예측 대상 | 입력값 예시 |
| --- | --- | --- |
| 주문 금액을 예측할 수 있을까? | 주문별 총금액 | 주문 상품 수, 총수량, 평균 단가, 결제수단 |
| 고객별 구매 금액을 예측할 수 있을까? | 고객별 총 구매 금액 | 주문 횟수, 평균 주문 금액, 지역, 연령 |
| 상품별 매출을 예측할 수 있을까? | 상품별 총매출 | 가격, 카테고리, 판매 수량 |
| 다음 달 매출을 예측할 수 있을까? | 월별 매출 | 이전 월 매출, 주문 수, 평균 주문 금액 |

이번 장에서는 가장 이해하기 쉬운 예시로 **주문별 총금액 예측**을 다룹니다. 주문 상세 데이터에서 주문별 총금액을 만들고, 주문 상품 수, 총수량, 평균 단가, 결제수단 같은 정보를 사용해 주문 금액을 예측해 보겠습니다.

## 2. 회귀 모델을 만들 때 필요한 것

회귀 모델을 만들려면 먼저 입력값과 예측 대상을 구분해야 합니다.

| 구분 | 설명 | 예시 |
| --- | --- | --- |
| 입력값(feature) | 예측에 사용할 정보 | 상품 수, 총수량, 평균 단가, 결제수단 |
| 예측 대상(target) | 모델이 예측해야 하는 값 | 주문별 총금액 |
| 학습 데이터(train) | 모델이 패턴을 배우는 데이터 | 전체 데이터의 일부 |
| 테스트 데이터(test) | 모델 성능을 확인하는 데이터 | 학습에 사용하지 않은 데이터 |
| 평가 지표(metric) | 예측이 얼마나 맞는지 확인하는 기준 | MAE, RMSE, R² |

중요한 것은 예측 대상과 입력값이 뒤섞이지 않도록 하는 것입니다. 예를 들어 주문별 총금액을 예측하면서 이미 계산된 `order_total`을 입력값으로 사용하면 의미가 없습니다. 모델은 정답을 미리 보고 맞히는 셈이 됩니다. 이런 문제를 데이터 누수(data leakage)라고 합니다.

회귀 분석에서는 다음 흐름을 따릅니다.

```text
데이터 준비
→ 예측 대상 정의
→ 입력 변수 선택
→ 범주형 변수 인코딩
→ 학습/테스트 데이터 분리
→ 모델 학습
→ 예측
→ 평가
→ 결과 해석
```

## 3. 회귀 평가 지표 읽기

모델이 얼마나 잘 예측했는지는 평가 지표로 확인합니다. 회귀 분석에서 자주 사용하는 지표는 MAE, RMSE, R²입니다.

| 지표 | 의미 | 해석 |
| --- | --- | --- |
| MAE | 평균 절대 오차 | 예측값이 실제값과 평균적으로 얼마나 차이 나는지 봅니다. |
| RMSE | 평균 제곱근 오차 | 큰 오차에 더 민감하게 반응합니다. |
| R² | 설명력 | 모델이 실제 값의 변동을 얼마나 설명하는지 봅니다. |

MAE가 12,000이라면 모델의 예측이 실제 주문 금액과 평균적으로 약 12,000원 정도 차이 난다고 해석할 수 있습니다. RMSE는 큰 오차에 더 민감하므로, 일부 주문에서 예측이 크게 빗나가면 값이 커집니다. R²는 보통 1에 가까울수록 좋지만, 데이터와 문제에 따라 해석에 주의해야 합니다.

평가 지표는 숫자 하나로 모델을 판단하기 위한 것이 아니라, 모델의 한계를 이해하기 위한 도구입니다.

## 4. 사용할 모델: 선형 회귀와 랜덤 포레스트 회귀

이번 장에서는 두 가지 회귀 모델을 사용합니다.

첫 번째는 선형 회귀입니다. 선형 회귀는 입력값과 예측 대상 사이의 관계를 직선적인 관계로 설명하려는 모델입니다. 구조가 단순하고 해석이 쉽기 때문에 회귀 분석의 출발점으로 적합합니다.

두 번째는 랜덤 포레스트 회귀입니다. 랜덤 포레스트는 여러 개의 의사결정나무를 사용해 예측하는 모델입니다. 선형 회귀보다 복잡한 패턴을 잡아낼 수 있지만, 그만큼 해석은 조금 어려울 수 있습니다.

| 모델 | 장점 | 주의할 점 |
| --- | --- | --- |
| Linear Regression | 단순하고 빠르며 해석이 쉽습니다. | 비선형 관계를 잘 잡지 못할 수 있습니다. |
| RandomForestRegressor | 복잡한 패턴을 잡는 데 유리합니다. | 해석이 어렵고 과적합을 확인해야 합니다. |

처음부터 복잡한 모델을 사용하는 것보다, 단순한 모델과 비교하면서 모델 성능과 해석 가능성을 함께 보는 것이 좋습니다.

## 5. 데이터 준비하기

이번 장의 코드는 `notebooks/ch09_regression_analysis.ipynb`로 구성하는 것이 좋습니다. 현재 저장소의 파일명은 기존 목차 기준으로 남아 있을 수 있으므로, 노트북 파일명은 이후 새 목차에 맞게 정리할 수 있습니다.

먼저 필요한 패키지를 불러옵니다.

```python
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
```

실행 위치에 따라 데이터 경로가 달라질 수 있으므로 기준 폴더를 설정합니다.

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

전처리된 데이터가 있다면 `data/processed`에서 불러오고, 없다면 `data/raw`를 사용할 수 있습니다. 여기서는 우선 전처리 데이터를 기준으로 설명합니다.

```python
customers = pd.read_csv(processed_dir / "customers_clean.csv")
products = pd.read_csv(processed_dir / "products_clean.csv")
orders = pd.read_csv(processed_dir / "orders_clean.csv")
order_items = pd.read_csv(processed_dir / "order_items_clean.csv")
```

만약 위 파일이 없다면 다음처럼 원본 데이터를 불러올 수 있습니다.

```python
customers = pd.read_csv(raw_dir / "customers.csv")
products = pd.read_csv(raw_dir / "products.csv")
orders = pd.read_csv(raw_dir / "orders.csv")
order_items = pd.read_csv(raw_dir / "order_items.csv")
```

분석에 필요한 기본 컬럼을 확인합니다.

```python
print("customers:", customers.shape, list(customers.columns))
print("products:", products.shape, list(products.columns))
print("orders:", orders.shape, list(orders.columns))
print("order_items:", order_items.shape, list(order_items.columns))
```

`line_total`이 없다면 수량과 단가를 곱해 만듭니다.

```python
if "line_total" not in order_items.columns:
    order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]
```

## 6. 주문별 예측 데이터 만들기

주문 금액을 예측하려면 주문 상세 데이터를 주문 단위로 요약해야 합니다. 하나의 주문에는 여러 상품이 포함될 수 있기 때문입니다.

```python
order_features = (
    order_items
    .groupby("order_id", as_index=False)
    .agg(
        item_count=("product_id", "count"),
        total_quantity=("quantity", "sum"),
        avg_unit_price=("unit_price", "mean"),
        order_total=("line_total", "sum")
    )
)

order_features.head()
```

여기서 `order_total`이 예측 대상입니다. 나머지 `item_count`, `total_quantity`, `avg_unit_price`는 입력값 후보입니다.

주문 정보와 고객 정보를 연결해 더 많은 입력값을 사용할 수 있습니다.

```python
orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
orders["order_month"] = orders["order_date"].dt.month
orders["order_dayofweek"] = orders["order_date"].dt.dayofweek

model_data = order_features.merge(
    orders[["order_id", "customer_id", "payment_method", "order_status", "order_month", "order_dayofweek"]],
    on="order_id",
    how="left"
)

model_data = model_data.merge(
    customers[["customer_id", "gender", "age", "city"]],
    on="customer_id",
    how="left"
)

model_data.head()
```

모델 데이터의 결측치를 확인합니다.

```python
model_data.isna().sum()
```

이번 장에서는 흐름을 단순하게 보기 위해 결측치가 있는 행을 제외합니다. 실제 프로젝트에서는 결측치의 원인을 먼저 확인하고, 평균 대체, 별도 범주 처리, 제거 여부를 신중히 결정해야 합니다.

```python
model_data = model_data.dropna().copy()
model_data.shape
```

예측 대상의 기본 통계를 확인합니다.

```python
model_data["order_total"].describe()
```

## 7. 입력값과 예측 대상 나누기

이제 입력값과 예측 대상을 나눕니다. 예측 대상은 `order_total`입니다.

```python
target = "order_total"

feature_cols = [
    "item_count",
    "total_quantity",
    "avg_unit_price",
    "payment_method",
    "order_status",
    "order_month",
    "order_dayofweek",
    "gender",
    "age",
    "city"
]

X = model_data[feature_cols]
y = model_data[target]
```

숫자형 컬럼과 범주형 컬럼을 구분합니다.

```python
numeric_features = [
    "item_count",
    "total_quantity",
    "avg_unit_price",
    "order_month",
    "order_dayofweek",
    "age"
]

categorical_features = [
    "payment_method",
    "order_status",
    "gender",
    "city"
]
```

범주형 컬럼은 모델이 바로 이해하기 어렵기 때문에 숫자 형태로 변환해야 합니다. 여기서는 `OneHotEncoder`를 사용합니다.

```python
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ],
    remainder="passthrough"
)
```

`handle_unknown="ignore"`는 테스트 데이터에 학습 데이터에서 보지 못한 범주가 나와도 오류가 나지 않도록 해 줍니다.

학습 데이터와 테스트 데이터를 나눕니다.

```python
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

print("X_train:", X_train.shape)
print("X_test:", X_test.shape)
```

학습 데이터는 모델이 패턴을 배우는 데 사용하고, 테스트 데이터는 학습에 사용하지 않은 데이터에서 성능을 확인하는 데 사용합니다.

## 8. 선형 회귀 모델 만들기

먼저 선형 회귀 모델을 만들어 봅니다. 전처리와 모델을 하나의 파이프라인으로 묶으면 코드가 더 안전하고 깔끔해집니다.

```python
linear_model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", LinearRegression())
])

linear_model.fit(X_train, y_train)
```

테스트 데이터에 대해 예측합니다.

```python
y_pred_linear = linear_model.predict(X_test)
```

평가 지표를 계산합니다.

```python
linear_mae = mean_absolute_error(y_test, y_pred_linear)
linear_rmse = mean_squared_error(y_test, y_pred_linear, squared=False)
linear_r2 = r2_score(y_test, y_pred_linear)

print("Linear Regression MAE:", linear_mae)
print("Linear Regression RMSE:", linear_rmse)
print("Linear Regression R2:", linear_r2)
```

MAE는 예측값이 실제값과 평균적으로 얼마나 차이 나는지를 보여줍니다. 주문 금액의 단위가 원이라면 MAE도 원 단위로 해석할 수 있습니다.

## 9. 랜덤 포레스트 회귀 모델 만들기

이번에는 랜덤 포레스트 회귀 모델을 사용해 봅니다.

```python
rf_model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", RandomForestRegressor(
        n_estimators=200,
        random_state=42
    ))
])

rf_model.fit(X_train, y_train)
```

예측하고 평가합니다.

```python
y_pred_rf = rf_model.predict(X_test)

rf_mae = mean_absolute_error(y_test, y_pred_rf)
rf_rmse = mean_squared_error(y_test, y_pred_rf, squared=False)
rf_r2 = r2_score(y_test, y_pred_rf)

print("Random Forest MAE:", rf_mae)
print("Random Forest RMSE:", rf_rmse)
print("Random Forest R2:", rf_r2)
```

두 모델의 결과를 비교합니다.

```python
model_comparison = pd.DataFrame({
    "model": ["Linear Regression", "Random Forest"],
    "MAE": [linear_mae, rf_mae],
    "RMSE": [linear_rmse, rf_rmse],
    "R2": [linear_r2, rf_r2]
})

model_comparison
```

결과를 저장합니다.

```python
model_comparison.to_csv(report_dir / "ch09_regression_model_comparison.csv", index=False)
```

성능이 더 좋아 보이는 모델이 항상 좋은 모델은 아닙니다. 모델이 너무 복잡하면 새로운 데이터에서 성능이 떨어질 수 있습니다. 따라서 모델 비교에서는 평가 지표와 함께 해석 가능성, 데이터 크기, 문제 목적을 함께 고려해야 합니다.

## 10. 실제값과 예측값 비교하기

모델 성능을 숫자로만 보는 것보다 실제값과 예측값을 함께 보는 것이 좋습니다.

```python
prediction_result = X_test.copy()
prediction_result["actual_order_total"] = y_test.values
prediction_result["predicted_order_total"] = y_pred_rf
prediction_result["error"] = prediction_result["actual_order_total"] - prediction_result["predicted_order_total"]
prediction_result["abs_error"] = prediction_result["error"].abs()

prediction_result.sort_values("abs_error", ascending=False).head(10)
```

오차가 큰 주문을 보면 모델이 어떤 상황에서 잘 맞지 않는지 확인할 수 있습니다. 예를 들어 특정 결제수단, 특정 지역, 높은 주문 금액에서 오차가 크다면 추가 분석이 필요합니다.

오차 요약도 확인합니다.

```python
prediction_result["abs_error"].describe()
```

결과를 저장합니다.

```python
prediction_result.to_csv(report_dir / "ch09_regression_predictions.csv", index=False)
```

## 11. 회귀 결과를 해석하는 방법

회귀 모델의 결과를 해석할 때는 “모델이 완벽하게 예측했다”는 식으로 표현하면 안 됩니다. 테스트 데이터에서 어느 정도의 오차가 있었는지, 그 오차가 업무적으로 받아들일 수 있는 수준인지 판단해야 합니다.

예를 들어 다음과 같이 표현할 수 있습니다.

```text
주문별 총금액을 예측하기 위해 선형 회귀와 랜덤 포레스트 회귀 모델을 비교했습니다.
테스트 데이터 기준으로 MAE와 RMSE를 확인하여 평균적인 예측 오차를 비교했습니다.
랜덤 포레스트 모델의 오차가 더 낮게 나타났다면, 현재 데이터에서는 비선형 패턴을 일부 반영한 모델이 더 적합할 가능성이 있습니다.
다만 데이터 규모와 입력 변수 구성이 제한적이므로, 실제 운영 예측에 사용하기 전에는 추가 검증이 필요합니다.
```

이 문장에서 중요한 점은 “가능성이 있다”, “추가 검증이 필요하다”는 표현입니다. 모델 결과는 의사결정의 참고 자료이지, 그 자체로 확정적인 결론은 아닙니다.

## 12. LLM에게 회귀 분석 코드를 요청할 때

LLM은 회귀 분석 코드 초안을 만드는 데 도움을 줄 수 있습니다. 하지만 모델링 코드는 오류가 나지 않는 것만으로 충분하지 않습니다. 예측 대상과 입력값이 적절히 분리되었는지, 데이터 누수가 없는지, 평가 방식이 맞는지 반드시 확인해야 합니다.

예를 들어 다음처럼 질문할 수 있습니다.

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
- 실제 데이터에 없는 컬럼명을 만들지 마세요.
- order_total을 입력값으로 사용하지 마세요.
- 범주형 컬럼은 OneHotEncoder를 사용해 주세요.
- 초보자도 이해할 수 있도록 단계별 설명을 포함해 주세요.
```

LLM이 만든 답변은 다음 기준으로 검토합니다.

| 검토 항목 | 확인 |
| --- | --- |
| 예측 대상이 명확히 분리되었는가? | □ |
| 정답 컬럼을 입력값으로 사용하지 않았는가? | □ |
| 실제 데이터에 없는 컬럼명을 만들지 않았는가? | □ |
| 범주형 컬럼을 적절히 인코딩했는가? | □ |
| train/test split을 적용했는가? | □ |
| 테스트 데이터 기준으로 평가했는가? | □ |
| MAE, RMSE, R²를 함께 확인했는가? | □ |
| 성능 결과를 과장해서 해석하지 않았는가? | □ |

LLM은 모델링 흐름을 빠르게 정리해 줄 수 있지만, 최종 판단은 사람이 해야 합니다.

## 13. 회귀 분석에서 다음 단계로

이번 장에서는 온라인 쇼핑몰 데이터를 사용해 주문별 총금액을 예측하는 회귀 분석 흐름을 살펴보았습니다. 중요한 것은 모델 이름을 외우는 것이 아니라, 예측 대상을 정의하고, 입력값을 선택하고, 학습 데이터와 테스트 데이터를 나누고, 평가 지표를 해석하는 흐름을 이해하는 것입니다.

직접 더 연습해 보고 싶다면 다음을 해볼 수 있습니다.

- 고객별 총 구매 금액을 예측하는 데이터셋을 만들어 봅니다.
- 상품별 총매출을 예측하는 회귀 모델을 만들어 봅니다.
- 입력값에서 `avg_unit_price`를 제외했을 때 성능이 어떻게 바뀌는지 비교합니다.
- RandomForestRegressor의 `n_estimators` 값을 바꿔 성능을 비교합니다.
- 예측 오차가 큰 주문 10건을 살펴보고 공통점을 찾아봅니다.
- LLM에게 회귀 분석 코드를 작성하게 한 뒤 데이터 누수 여부를 검토합니다.

다음 장에서는 숫자를 예측하는 회귀와 달리, 특정 상태나 범주를 예측하는 분류 분석을 다룹니다. 예를 들어 주문이 완료될지 취소될지, 고객이 구매할 가능성이 높은지 같은 문제를 생각해 볼 수 있습니다.
