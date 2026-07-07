# 15장. 하나의 데이터 분석 프로젝트로 완성하기

지금까지 우리는 데이터를 불러오고, 구조를 이해하고, pandas로 분석하고, 전처리하고, EDA와 시각화를 수행했습니다. 이어서 회귀와 분류 모델을 통해 간단한 예측 분석을 경험했고, LLM을 활용해 분석 질문과 코드, 해석 문장을 검토하는 방법도 살펴보았습니다. 외부 데이터 수집과 자동화 아이디어까지 더하면 하나의 실무형 데이터 분석 프로젝트 흐름이 완성됩니다.

최종 프로젝트는 앞에서 배운 내용을 단순히 다시 실행하는 시간이 아닙니다. 분석 목적을 정하고, 데이터 구조를 확인하고, 필요한 전처리를 수행하고, 분석 질문에 맞는 결과를 만들고, 그래프와 모델 결과를 해석하고, LLM 활용 내역과 검증 과정을 남기며, 마지막에는 보고서와 발표 자료로 정리하는 과정입니다.

이번 장에서는 온라인 쇼핑몰 데이터를 바탕으로 **EDA + 시각화 + 머신러닝 + LLM 활용 + 외부 데이터 확장 아이디어 + 자동화 설계**를 하나의 프로젝트로 묶는 방법을 살펴봅니다. 핵심은 많은 코드를 작성하는 것이 아니라, 분석 질문에서 최종 보고서까지 흐름이 자연스럽게 이어지도록 만드는 것입니다.

## 이 장에서 생각해 볼 질문

최종 프로젝트를 시작하기 전에 다음 질문을 먼저 생각해 봅니다.

- 이 프로젝트는 어떤 의사결정에 도움이 되어야 하는가?
- 현재 데이터로 답할 수 있는 질문과 답하기 어려운 질문은 무엇인가?
- 전처리 기준은 분석 목적에 맞게 설명되어 있는가?
- EDA와 시각화 결과가 같은 질문을 향해 연결되어 있는가?
- 회귀 또는 분류 모델은 왜 필요한가?
- LLM은 어떤 단계에서 사용했고, 답변은 어떻게 검증했는가?
- 외부 데이터가 추가된다면 어떤 분석이 더 가능해질까?
- 반복 분석 업무로 운영하려면 어떤 자동화 구조가 필요할까?
- 최종 보고서는 데이터에 없는 원인을 단정하지 않고 있는가?

## 1. 최종 프로젝트의 전체 흐름

최종 프로젝트는 하나의 분석 스토리를 만드는 과정입니다. 코드, 그래프, 모델, 보고서가 각각 따로 존재하는 것이 아니라 하나의 질문을 향해 연결되어야 합니다.

```text
분석 목적 정의
→ 데이터 구조 점검
→ 전처리 기준 수립
→ EDA와 핵심 지표 계산
→ 시각화
→ 회귀 또는 분류 모델링
→ LLM 활용과 검증 기록
→ 외부 데이터 확장 아이디어
→ 자동화/파이프라인 설계
→ 최종 보고서와 발표 정리
```

아래 그림은 최종 프로젝트의 전체 흐름을 보여줍니다.

<figure class="figure">
  <img src="../assets/images/ch15/ch15_final_project_overview.png" alt="기말 종합 프로젝트 전체 흐름도">
  <figcaption>그림 15-1. 최종 프로젝트 전체 흐름도</figcaption>
</figure>

이번 프로젝트의 기본 주제는 다음과 같습니다.

```text
온라인 쇼핑몰 고객·상품·주문 데이터 기반 매출 분석 및 예측 프로젝트
```

프로젝트의 기본 시나리오는 다음과 같습니다.

> 온라인 쇼핑몰 운영팀은 최근 주문 데이터를 바탕으로 매출 현황과 고객 구매 패턴을 파악하려고 합니다. 데이터 분석가는 원본 CSV 데이터를 점검하고, 전처리하고, 주요 지표를 계산하고, 시각화와 머신러닝 모델을 통해 분석 결과를 정리해야 합니다. 또한 LLM을 분석 보조 도구로 활용하되, 결과를 직접 검증하고, 향후 외부 데이터 확장 및 반복 분석 자동화 방안을 제안해야 합니다.

## 2. 프로젝트 산출물의 의미

최종 프로젝트에서는 다양한 파일이 만들어집니다. 하지만 산출물의 목적은 파일 개수를 늘리는 것이 아닙니다. 각 파일이 분석 흐름의 어느 단계를 설명하는지 명확해야 합니다.

| 구분 | 예시 파일 | 의미 |
| --- | --- | --- |
| Notebook | `notebooks/ch15_final_project.ipynb` | 전체 분석 흐름을 실행 가능한 형태로 정리 |
| 데이터 개요 | `reports/ch15_dataset_summary.csv` | 사용 데이터의 구조 요약 |
| 전처리 결과 | `data/processed/*_clean.csv` | 분석에 사용할 정리된 데이터 |
| EDA 결과 | `reports/ch15_category_sales.csv`, `reports/ch15_monthly_sales.csv` | 주요 분석 질문에 대한 집계 결과 |
| 시각화 | `reports/figures/ch15_*.png` | 분석 결과를 그래프로 전달 |
| 머신러닝 결과 | `reports/ch15_model_comparison.csv` | 회귀 또는 분류 모델의 평가 결과 |
| LLM 기록 | `reports/ch15_llm_usage_log.md` | LLM 활용 목적과 검증 내역 |
| 최종 보고서 | `reports/ch15_final_report.md` | 분석 결과, 해석, 한계, 다음 단계 정리 |
| 자동화 설계 | `reports/ch15_automation_plan.md` | 반복 분석을 운영화하기 위한 설계 |

아래 그림은 최종 제출 패키지 구성을 보여줍니다.

<figure class="figure">
  <img src="../assets/images/ch15/ch15_project_deliverables.png" alt="기말 프로젝트 제출물 구성">
  <figcaption>그림 15-2. 최종 프로젝트 산출물 구성</figcaption>
</figure>

## 3. 분석 질문 설계하기

좋은 프로젝트는 좋은 질문에서 시작합니다. 온라인 쇼핑몰 데이터에서는 다음과 같은 질문을 만들 수 있습니다.

| 분석 영역 | 핵심 질문 | 주요 지표 |
| --- | --- | --- |
| 매출 현황 | 전체 매출은 어느 정도인가? | `total_sales` |
| 카테고리 분석 | 어떤 카테고리가 매출에 기여하는가? | `sales_ratio`, `total_quantity`, `avg_unit_revenue` |
| 월별 분석 | 매출과 주문 수는 월별로 어떻게 변하는가? | `order_month`, `order_count`, `avg_order_value` |
| 고객 분석 | 구매 금액 상위 고객은 어떤 특성이 있는가? | `order_count`, `total_sales`, `avg_order_value` |
| 상품 분석 | 어떤 상품이 매출과 판매 수량에 기여하는가? | `total_quantity`, `total_sales` |
| 회귀 모델 | 주문별 총금액을 예측할 수 있는가? | MAE, RMSE, R² |
| 분류 모델 | 주문 취소 여부를 예측할 수 있는가? | accuracy, precision, recall |
| 외부 데이터 | 외부 데이터가 있으면 어떤 질문을 확장할 수 있는가? | 날짜, 지역, 키워드 연결 가능성 |
| 자동화 | 반복 분석은 어떻게 운영할 수 있는가? | 실행 주기, 산출물, 알림, 로그 |

모든 질문을 반드시 깊게 다룰 필요는 없습니다. 중요한 것은 선택한 질문에 대해 데이터, 코드, 그래프, 해석이 서로 연결되어 있어야 한다는 점입니다.

## 4. 프로젝트 기본 환경 준비

최종 프로젝트 Notebook에서는 앞 장에서 사용한 기본 패키지들을 함께 사용합니다.

```python
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix
)
```

실행 위치에 따라 기준 폴더를 설정합니다.

```python
current_dir = Path.cwd()

if current_dir.name == "notebooks":
    base_dir = current_dir.parent
else:
    base_dir = current_dir

raw_dir = base_dir / "data" / "raw"
processed_dir = base_dir / "data" / "processed"
external_dir = base_dir / "data" / "external"
report_dir = base_dir / "reports"
figure_dir = report_dir / "figures"

processed_dir.mkdir(parents=True, exist_ok=True)
external_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)
figure_dir.mkdir(parents=True, exist_ok=True)

print("raw_dir:", raw_dir)
print("processed_dir:", processed_dir)
print("report_dir:", report_dir)
print("figure_dir:", figure_dir)
```

한글 그래프 제목을 사용한다면 폰트 설정도 추가합니다.

```python
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
```

## 5. 데이터 불러오기와 구조 점검

먼저 원본 CSV 파일을 불러옵니다.

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

데이터 구조 요약표를 만듭니다.

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

저장합니다.

```python
dataset_summary.to_csv(report_dir / "ch15_dataset_summary.csv", index=False)
```

이 표는 최종 보고서의 데이터 개요 섹션에 그대로 활용할 수 있습니다.

## 6. 전처리 기준 정리하기

전처리는 단순히 데이터를 깨끗하게 만드는 작업이 아닙니다. 분석 목적에 맞게 데이터를 사용할 수 있는 상태로 만드는 과정입니다.

먼저 문자열 공백 제거와 숫자형 변환 함수를 준비합니다.

```python
def strip_string_columns(df):
    df = df.copy()
    string_columns = df.select_dtypes(include="object").columns

    for col in string_columns:
        df[col] = df[col].where(
            df[col].isna(),
            df[col].astype(str).str.strip()
        )

    return df
```

```python
def to_number(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )
```

고객 데이터, 상품 데이터, 주문 데이터, 주문 상세 데이터를 각각 정리합니다.

```python
customers_clean = strip_string_columns(customers)

if "age" in customers_clean.columns:
    customers_clean["age"] = pd.to_numeric(customers_clean["age"], errors="coerce")
    customers_clean["age"] = customers_clean["age"].fillna(customers_clean["age"].median())

if "city" in customers_clean.columns:
    customers_clean["city"] = customers_clean["city"].fillna("Unknown")

if "signup_date" in customers_clean.columns:
    customers_clean["signup_date"] = pd.to_datetime(customers_clean["signup_date"], errors="coerce")

customers_clean = customers_clean.drop_duplicates()
```

```python
products_clean = strip_string_columns(products)

if "price" in products_clean.columns:
    products_clean["price"] = to_number(products_clean["price"])
    products_clean = products_clean[products_clean["price"] > 0]

products_clean = products_clean.drop_duplicates()
```

```python
orders_clean = strip_string_columns(orders)

if "order_date" in orders_clean.columns:
    orders_clean["order_date"] = pd.to_datetime(orders_clean["order_date"], errors="coerce")
    orders_clean["order_month"] = orders_clean["order_date"].dt.to_period("M").astype(str)
    orders_clean["order_dayofweek"] = orders_clean["order_date"].dt.dayofweek

if "order_status" in orders_clean.columns:
    status_map = {
        "complete": "completed",
        "Complete": "completed",
        "COMPLETED": "completed",
        "완료": "completed",
        "cancel": "cancelled",
        "Cancel": "cancelled",
        "CANCELLED": "cancelled",
        "취소": "cancelled"
    }
    orders_clean["order_status"] = orders_clean["order_status"].replace(status_map)

orders_clean = orders_clean.drop_duplicates()
```

```python
order_items_clean = strip_string_columns(order_items)

if "quantity" in order_items_clean.columns:
    order_items_clean["quantity"] = to_number(order_items_clean["quantity"])
    order_items_clean = order_items_clean[order_items_clean["quantity"] > 0]

if "unit_price" in order_items_clean.columns:
    order_items_clean["unit_price"] = to_number(order_items_clean["unit_price"])
    order_items_clean = order_items_clean[order_items_clean["unit_price"] > 0]

if {"quantity", "unit_price"}.issubset(order_items_clean.columns):
    order_items_clean["line_total"] = order_items_clean["quantity"] * order_items_clean["unit_price"]

order_items_clean = order_items_clean.drop_duplicates()
```

전처리 결과를 저장합니다.

```python
customers_clean.to_csv(processed_dir / "customers_clean.csv", index=False)
products_clean.to_csv(processed_dir / "products_clean.csv", index=False)
orders_clean.to_csv(processed_dir / "orders_clean.csv", index=False)
order_items_clean.to_csv(processed_dir / "order_items_clean.csv", index=False)
```

전처리 전후 비교표도 만듭니다.

```python
processed_summary = pd.DataFrame({
    "dataset": ["customers", "products", "orders", "order_items"],
    "rows_processed": [
        customers_clean.shape[0],
        products_clean.shape[0],
        orders_clean.shape[0],
        order_items_clean.shape[0]
    ],
    "columns_processed": [
        customers_clean.shape[1],
        products_clean.shape[1],
        orders_clean.shape[1],
        order_items_clean.shape[1]
    ]
})

preprocessing_comparison = dataset_summary.merge(processed_summary, on="dataset")
preprocessing_comparison
```

```python
preprocessing_comparison.to_csv(report_dir / "ch15_preprocessing_comparison.csv", index=False)
```

## 7. EDA와 주요 지표 계산

분석용 데이터를 만들기 위해 주문 상세, 상품, 주문, 고객 데이터를 연결합니다.

```python
sales_items = order_items_clean.merge(
    products_clean,
    on="product_id",
    how="left"
)

order_sales = order_items_clean.merge(
    orders_clean,
    on="order_id",
    how="left"
)

customer_sales_base = order_sales.merge(
    customers_clean,
    on="customer_id",
    how="left"
)
```

병합 후에는 행 수와 결측치를 확인합니다.

```python
print("sales_items:", sales_items.shape)
print("order_sales:", order_sales.shape)
print("customer_sales_base:", customer_sales_base.shape)

print("category 누락:", sales_items["category"].isna().sum())
print("order_date 누락:", order_sales["order_date"].isna().sum())
print("customer_id 누락:", customer_sales_base["customer_id"].isna().sum())
```

카테고리별 매출을 계산합니다.

```python
category_sales = (
    sales_items
    .groupby("category", as_index=False)
    .agg(
        total_quantity=("quantity", "sum"),
        total_sales=("line_total", "sum")
    )
    .sort_values("total_sales", ascending=False)
)

category_sales["sales_ratio"] = (
    category_sales["total_sales"] / category_sales["total_sales"].sum() * 100
).round(2)

category_sales["avg_unit_revenue"] = (
    category_sales["total_sales"] / category_sales["total_quantity"]
).round(0)

category_sales.to_csv(report_dir / "ch15_category_sales.csv", index=False)
category_sales
```

월별 매출을 계산합니다.

```python
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

monthly_sales["sales_change_ratio"] = (
    monthly_sales["total_sales"].pct_change() * 100
).round(2)

monthly_sales.to_csv(report_dir / "ch15_monthly_sales.csv", index=False)
monthly_sales
```

고객별 구매 금액을 계산합니다.

```python
customer_sales = (
    customer_sales_base
    .groupby(["customer_id", "city"], as_index=False)
    .agg(
        order_count=("order_id", "nunique"),
        total_sales=("line_total", "sum")
    )
    .sort_values("total_sales", ascending=False)
)

customer_sales["avg_order_value"] = (
    customer_sales["total_sales"] / customer_sales["order_count"]
).round(0)

customer_sales["customer_label"] = "Customer " + customer_sales["customer_id"].astype(str)

customer_sales.to_csv(report_dir / "ch15_customer_sales.csv", index=False)
customer_sales.head(10)
```

상품별 매출도 계산합니다.

```python
product_sales = (
    sales_items
    .groupby(["product_id", "product_name", "category", "price"], as_index=False)
    .agg(
        total_quantity=("quantity", "sum"),
        total_sales=("line_total", "sum")
    )
    .sort_values("total_sales", ascending=False)
)

product_sales["avg_unit_revenue"] = (
    product_sales["total_sales"] / product_sales["total_quantity"]
).round(0)

product_sales.to_csv(report_dir / "ch15_product_sales.csv", index=False)
product_sales.head(10)
```

## 8. 시각화로 결과 전달하기

카테고리별 매출 그래프를 저장합니다.

```python
plt.figure(figsize=(10, 5))
plt.bar(category_sales["category"], category_sales["total_sales"])
plt.title("카테고리별 매출")
plt.xlabel("카테고리")
plt.ylabel("총매출")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(figure_dir / "ch15_category_sales.png", dpi=150)
plt.show()
```

월별 매출 추이를 저장합니다.

```python
plt.figure(figsize=(10, 5))
plt.plot(monthly_sales["order_month"], monthly_sales["total_sales"], marker="o")
plt.title("월별 매출 추이")
plt.xlabel("주문 월")
plt.ylabel("총매출")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(figure_dir / "ch15_monthly_sales.png", dpi=150)
plt.show()
```

구매 금액 상위 고객은 개인정보 보호를 위해 익명화 라벨로 표현합니다.

```python
top_customers = customer_sales.head(10).copy().sort_values("total_sales")

plt.figure(figsize=(10, 6))
plt.barh(top_customers["customer_label"], top_customers["total_sales"])
plt.title("구매 금액 상위 10명 고객")
plt.xlabel("총 구매 금액")
plt.ylabel("고객")
plt.tight_layout()
plt.savefig(figure_dir / "ch15_top_customers.png", dpi=150)
plt.show()
```

상품 가격과 판매 수량의 관계도 확인합니다.

```python
plt.figure(figsize=(10, 5))
plt.scatter(product_sales["price"], product_sales["total_quantity"], alpha=0.6)
plt.title("상품 가격과 판매 수량의 관계")
plt.xlabel("상품 가격")
plt.ylabel("총 판매 수량")
plt.tight_layout()
plt.savefig(figure_dir / "ch15_price_quantity_scatter.png", dpi=150)
plt.show()
```

아래 그림은 최종 프로젝트에서 생성할 주요 시각화 결과를 보여줍니다.

<figure class="figure">
  <img src="../assets/images/ch15/ch15_analysis_dashboard.png" alt="기말 프로젝트 주요 분석 대시보드 예시">
  <figcaption>그림 15-3. 최종 프로젝트 주요 분석 대시보드 예시</figcaption>
</figure>

## 9. 머신러닝 모델 추가하기

최종 프로젝트에는 간단한 머신러닝 모델을 하나 이상 포함할 수 있습니다. 회귀와 분류 중 하나를 선택해도 되고, 시간이 충분하다면 둘 다 비교해도 좋습니다.

### 회귀: 주문별 총금액 예측

주문별 총금액을 예측하는 모델링 데이터를 만듭니다.

```python
order_features = (
    order_items_clean
    .groupby("order_id", as_index=False)
    .agg(
        item_count=("product_id", "count"),
        total_quantity=("quantity", "sum"),
        avg_unit_price=("unit_price", "mean"),
        order_total=("line_total", "sum")
    )
)

regression_data = order_features.merge(
    orders_clean[["order_id", "customer_id", "payment_method", "order_status", "order_month", "order_dayofweek"]],
    on="order_id",
    how="left"
).merge(
    customers_clean[["customer_id", "gender", "age", "city"]],
    on="customer_id",
    how="left"
).dropna()
```

입력값과 예측 대상을 나눕니다.

```python
regression_features = [
    "item_count",
    "total_quantity",
    "avg_unit_price",
    "payment_method",
    "order_status",
    "order_dayofweek",
    "gender",
    "age",
    "city"
]

X_reg = regression_data[regression_features]
y_reg = regression_data["order_total"]

categorical_reg = ["payment_method", "order_status", "gender", "city"]

preprocessor_reg = ColumnTransformer(
    transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), categorical_reg)],
    remainder="passthrough"
)

X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
    X_reg,
    y_reg,
    test_size=0.2,
    random_state=42
)
```

두 회귀 모델을 비교합니다.

```python
regression_models = {
    "Linear Regression": LinearRegression(),
    "Random Forest Regressor": RandomForestRegressor(n_estimators=200, random_state=42)
}

regression_results = []

for model_name, model in regression_models.items():
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor_reg),
        ("model", model)
    ])

    pipeline.fit(X_train_reg, y_train_reg)
    y_pred = pipeline.predict(X_test_reg)

    regression_results.append({
        "model": model_name,
        "MAE": mean_absolute_error(y_test_reg, y_pred),
        "RMSE": mean_squared_error(y_test_reg, y_pred, squared=False),
        "R2": r2_score(y_test_reg, y_pred)
    })

regression_comparison = pd.DataFrame(regression_results)
regression_comparison.to_csv(report_dir / "ch15_regression_model_comparison.csv", index=False)
regression_comparison
```

### 분류: 주문 취소 여부 예측

주문 취소 여부를 예측하는 분류 데이터도 만들 수 있습니다. 이때 `order_status` 자체를 입력값으로 사용하면 정답을 미리 보는 데이터 누수가 발생합니다.

```python
classification_data = regression_data.copy()
classification_data["is_cancelled"] = (classification_data["order_status"] == "cancelled").astype(int)

classification_features = [
    "item_count",
    "total_quantity",
    "avg_unit_price",
    "payment_method",
    "order_dayofweek",
    "gender",
    "age",
    "city"
]

X_cls = classification_data[classification_features]
y_cls = classification_data["is_cancelled"]

categorical_cls = ["payment_method", "gender", "city"]

preprocessor_cls = ColumnTransformer(
    transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cls)],
    remainder="passthrough"
)

X_train_cls, X_test_cls, y_train_cls, y_test_cls = train_test_split(
    X_cls,
    y_cls,
    test_size=0.2,
    random_state=42,
    stratify=y_cls
)
```

분류 모델을 비교합니다.

```python
classification_models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Random Forest Classifier": RandomForestClassifier(n_estimators=200, random_state=42)
}

classification_results = []

for model_name, model in classification_models.items():
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor_cls),
        ("model", model)
    ])

    pipeline.fit(X_train_cls, y_train_cls)
    y_pred = pipeline.predict(X_test_cls)

    classification_results.append({
        "model": model_name,
        "accuracy": accuracy_score(y_test_cls, y_pred),
        "precision": precision_score(y_test_cls, y_pred, zero_division=0),
        "recall": recall_score(y_test_cls, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test_cls, y_pred).tolist()
    })

classification_comparison = pd.DataFrame(classification_results)
classification_comparison.to_csv(report_dir / "ch15_classification_model_comparison.csv", index=False)
classification_comparison
```

머신러닝 결과를 해석할 때는 “정확도가 높다”에서 멈추지 말고, 데이터 크기, 클래스 불균형, 입력 변수의 한계, 데이터 누수 가능성을 함께 확인해야 합니다.

## 10. 인사이트 카드 만들기

분석 결과는 보고서에 바로 넣을 수 있는 형태로 정리해 둡니다.

```python
top_category = category_sales.iloc[0]
top_month = monthly_sales.sort_values("total_sales", ascending=False).iloc[0]
top_customer = customer_sales.iloc[0]
top_product = product_sales.iloc[0]
```

```python
insight_cards = pd.DataFrame({
    "insight_title": [
        "매출 기여도 높은 카테고리 확인",
        "월별 매출 집중 구간 확인",
        "구매 금액 상위 고객 특성 확인",
        "상품별 매출 기여도 확인",
        "머신러닝 모델의 예측 가능성 확인"
    ],
    "observation": [
        f"{top_category['category']} 카테고리의 매출 비중이 가장 높게 나타났습니다.",
        f"{top_month['order_month']}의 매출이 가장 높게 나타났습니다.",
        "구매 금액 상위 고객은 전체 매출에 크게 기여하는 고객군입니다.",
        f"{top_product['product_name']} 상품의 매출이 가장 높게 나타났습니다.",
        "회귀 또는 분류 모델을 통해 일부 예측 가능성을 확인했습니다."
    ],
    "caution": [
        "매출이 높은 이유를 고객 선호로 단정할 수 없습니다.",
        "매출 증가 원인을 프로모션이나 계절성으로 단정할 수 없습니다.",
        "총 구매 금액만으로 충성 고객 여부를 판단할 수 없습니다.",
        "상품 매출이 높은 이유는 단가 또는 판매 수량을 함께 확인해야 합니다.",
        "모델 성능은 현재 데이터와 입력 변수 범위에 한정됩니다."
    ],
    "next_step": [
        "판매 수량과 평균 판매 단가를 함께 분석합니다.",
        "주문 수와 평균 주문 금액 변화를 함께 확인합니다.",
        "반복 구매 여부와 최근 구매일을 추가로 확인합니다.",
        "상품별 판매 수량과 가격대를 함께 분석합니다.",
        "외부 데이터와 추가 변수를 결합해 모델 성능을 개선합니다."
    ]
})

insight_cards.to_csv(report_dir / "ch15_insight_cards.csv", index=False)
insight_cards
```

## 11. LLM 활용 및 검증 기록 남기기

LLM은 최종 프로젝트에서 분석 질문 보완, 코드 초안 작성, 오류 해결, 해석 문장 작성, 보고서 검토에 활용할 수 있습니다. 다만 최종 산출물에는 검증된 내용만 반영해야 합니다.

```python
llm_usage_log = pd.DataFrame({
    "step": [
        "분석 질문 검토",
        "pandas 코드 생성",
        "머신러닝 코드 검토",
        "오류 해결",
        "결과 해석",
        "보고서 문장 보완",
        "자동화 설계"
    ],
    "input_summary": [
        "데이터셋 이름과 컬럼명",
        "분석 목적과 데이터 구조",
        "예측 대상, 입력값 후보, 평가 지표",
        "오류 메시지와 코드 일부",
        "집계 결과표와 모델 평가 결과",
        "보고서 초안",
        "보고서 파일과 반복 실행 흐름"
    ],
    "validation_point": [
        "현재 데이터로 답할 수 있는 질문인지 확인",
        "컬럼명과 병합 기준 검증",
        "데이터 누수와 평가 지표 검증",
        "수정 코드 실행 여부 확인",
        "원인 단정 여부 검토",
        "데이터에 없는 표현 수정",
        "실제 도구에서 구현 가능한지 확인"
    ],
    "used_in_final": [
        "수정 후 사용",
        "검증 후 사용",
        "검증 후 사용",
        "검증 후 사용",
        "수정 후 사용",
        "수정 후 사용",
        "설계 참고"
    ]
})

llm_usage_log
```

Markdown 기록으로 저장합니다.

```python
llm_usage_text = f"""
# Chapter 15 LLM 활용 및 검증 기록

## 1. LLM 활용 목적

기말 종합 프로젝트에서 LLM은 분석 질문 보완, pandas 코드 초안 작성, 머신러닝 코드 검토, 오류 해결, 해석 문장 작성, 자동화 설계 보조 도구로 사용했습니다.

## 2. LLM 활용 기록

{llm_usage_log.to_markdown(index=False)}

## 3. 검증 원칙

- 원본 개인정보나 개별 주문 데이터를 LLM에 입력하지 않았습니다.
- 컬럼명, 데이터 구조, 집계 결과 중심으로 질문했습니다.
- LLM이 생성한 코드는 실제 데이터로 실행해 검증했습니다.
- 머신러닝 코드에서는 데이터 누수 여부를 확인했습니다.
- LLM이 작성한 해석 문장은 원인 단정 여부를 검토했습니다.
- 최종 보고서에는 검증된 코드와 문장만 반영했습니다.
"""

llm_usage_path = report_dir / "ch15_llm_usage_log.md"
llm_usage_path.write_text(llm_usage_text, encoding="utf-8")
```

## 12. 외부 데이터 확장 아이디어 정리하기

최종 프로젝트에서 외부 데이터를 실제로 수집하지 못하더라도, 어떤 외부 데이터가 분석을 확장할 수 있는지 제안할 수 있습니다.

```python
external_data_ideas = pd.DataFrame({
    "external_data": [
        "공휴일/캘린더 데이터",
        "날씨 데이터",
        "지역 통계 데이터",
        "네이버 검색 API 데이터",
        "공공 관광/상권 데이터"
    ],
    "connection_key": [
        "order_date 또는 order_month",
        "order_date, city",
        "city",
        "keyword, collection_date",
        "city 또는 location"
    ],
    "possible_question": [
        "공휴일 전후 매출이 달라지는가?",
        "날씨가 특정 카테고리 매출과 관련이 있는가?",
        "지역별 고객 구매 패턴을 인구 특성과 함께 볼 수 있는가?",
        "검색 관심도와 카테고리 매출은 함께 움직이는가?",
        "관광/상권 정보와 지역별 구매 패턴을 연결할 수 있는가?"
    ],
    "caution": [
        "공휴일 효과를 단정하려면 비교 기간이 필요합니다.",
        "날씨와 매출의 관계는 상관일 뿐 원인으로 단정할 수 없습니다.",
        "지역명 표기와 통계 단위를 맞춰야 합니다.",
        "검색 결과가 실제 수요를 대표한다고 단정하면 안 됩니다.",
        "공공데이터의 갱신 주기와 사용 조건을 확인해야 합니다."
    ]
})

external_data_ideas.to_csv(report_dir / "ch15_external_data_ideas.csv", index=False)
external_data_ideas
```

이 표는 프로젝트의 한계와 다음 단계 섹션에 활용할 수 있습니다.

## 13. 자동화와 파이프라인 설계

최종 프로젝트의 마지막 단계는 반복 가능한 분석 흐름을 설계하는 것입니다. 실제 운영 환경에서는 매번 Notebook을 수동으로 실행하기보다, 정해진 주기에 따라 데이터를 불러오고, 전처리하고, 분석하고, 보고서를 생성하고, 알림을 보내는 구조가 필요합니다.

| 단계 | 도구 | 역할 |
| --- | --- | --- |
| 1 | Python | 전처리, 분석, 시각화, 보고서 생성 |
| 2 | Airflow | 정해진 순서로 분석 파이프라인 실행 |
| 3 | Google Drive | 생성된 보고서 저장 |
| 4 | Make 또는 n8n | 새 보고서 감지, 이메일/Slack 발송 |
| 5 | Google Sheets | 실행 로그 기록 |

자동화 설계 문서를 작성합니다.

```python
automation_plan = """
# Chapter 15 자동화 설계서

## 1. 자동화 목적

최종 프로젝트의 분석 과정을 반복 실행할 수 있도록 전처리, 분석, 시각화, 보고서 생성, 전달 과정을 자동화합니다.

## 2. 권장 구조

Airflow는 분석 파이프라인 실행을 담당하고, Make 또는 n8n은 생성된 보고서 발송과 로그 기록을 담당합니다.

## 3. Airflow 역할

- 원본 데이터 확인
- 전처리 실행
- 분석 결과 생성
- 머신러닝 모델 평가
- 시각화 이미지 생성
- Markdown 보고서 생성
- 결과 파일 검증

## 4. Make 또는 n8n 역할

- Google Drive 보고서 파일 감지
- Gmail 또는 Slack 보고서 발송
- Google Sheets 실행 로그 기록
- 실패 시 관리자 알림

## 5. 운영 시 주의사항

- 원본 데이터 경로와 보고서 저장 경로를 고정합니다.
- 보고서 파일명 규칙을 정합니다.
- 자동 발송 전 테스트 수신자에게 먼저 발송합니다.
- 개인정보가 포함된 표나 그래프는 익명화합니다.
- 실행 로그를 반드시 남깁니다.
"""

automation_plan_path = report_dir / "ch15_automation_plan.md"
automation_plan_path.write_text(automation_plan, encoding="utf-8")
```

아래 그림은 최종 프로젝트의 분석·보고서·자동화 통합 구조를 보여줍니다.

<figure class="figure">
  <img src="../assets/images/ch15/ch15_end_to_end_automation_architecture.png" alt="기말 프로젝트 End-to-End 자동화 아키텍처">
  <figcaption>그림 15-4. 최종 프로젝트 End-to-End 자동화 아키텍처</figcaption>
</figure>

## 14. 최종 보고서 작성하기

최종 보고서는 분석 과정을 나열하는 문서가 아니라, 분석 목적과 결과, 해석, 한계, 다음 단계를 연결하는 문서입니다.

```python
today = datetime.now().strftime("%Y-%m-%d")

final_report = f"""
# Chapter 15 최종 프로젝트 보고서

작성일: {today}

## 1. 프로젝트 개요

본 프로젝트는 온라인 쇼핑몰 고객, 상품, 주문, 주문 상세 데이터를 바탕으로 매출 현황과 고객 구매 패턴을 분석하고, 간단한 예측 모델과 자동화 설계까지 확장하는 것을 목표로 합니다.

## 2. 데이터 개요

{dataset_summary.to_markdown(index=False)}

## 3. 전처리 전후 비교

{preprocessing_comparison.to_markdown(index=False)}

## 4. 주요 분석 결과

### 카테고리별 매출

{category_sales.to_markdown(index=False)}

![카테고리별 매출](figures/ch15_category_sales.png)

### 월별 매출

{monthly_sales.to_markdown(index=False)}

![월별 매출](figures/ch15_monthly_sales.png)

### 고객별 구매 금액 상위

{customer_sales.head(10).to_markdown(index=False)}

![구매 금액 상위 고객](figures/ch15_top_customers.png)

## 5. 머신러닝 결과

### 회귀 모델 비교

{regression_comparison.to_markdown(index=False)}

### 분류 모델 비교

{classification_comparison.to_markdown(index=False)}

## 6. 인사이트 카드

{insight_cards.to_markdown(index=False)}

## 7. LLM 활용 및 검증

{llm_usage_log.to_markdown(index=False)}

## 8. 외부 데이터 확장 아이디어

{external_data_ideas.to_markdown(index=False)}

## 9. 한계점

- 현재 데이터만으로 고객 선호도나 만족도를 직접 판단할 수 없습니다.
- 매출 증가 원인을 설명하려면 프로모션, 광고, 재고, 계절성 데이터가 필요합니다.
- 고객별 구매 금액만으로 충성 고객 여부를 판단하기 어렵습니다.
- 머신러닝 결과는 현재 데이터와 입력 변수 범위에 한정됩니다.
- 주문 상태 처리 기준에 따라 매출 결과가 달라질 수 있습니다.

## 10. 다음 단계

- 카테고리별 매출을 판매 수량과 평균 판매 단가로 더 세분화합니다.
- 월별 매출 변화를 주문 수와 평균 주문 금액으로 분해합니다.
- 고객별 구매 금액을 반복 구매 여부와 최근 구매일 기준으로 분석합니다.
- 외부 데이터를 결합해 매출 변화 원인을 더 깊게 검토합니다.
- 자동화 파이프라인을 실제 운영 환경에 맞게 개선합니다.
"""

final_report_path = report_dir / "ch15_final_report.md"
final_report_path.write_text(final_report, encoding="utf-8")
```

보고서 문장에서는 다음 표현을 조심해야 합니다.

| 피해야 할 표현 | 더 안전한 표현 |
| --- | --- |
| 고객이 전자기기를 선호해서 매출이 높다 | 전자기기 카테고리의 매출 비중이 높게 나타났다 |
| 프로모션 때문에 매출이 증가했다 | 매출 증가 원인을 확인하려면 프로모션 데이터가 필요하다 |
| 상위 고객은 충성 고객이다 | 구매 금액 상위 고객이며 반복 구매 여부는 추가 확인이 필요하다 |
| 모델이 정확하게 예측한다 | 현재 테스트 데이터 기준으로 일정 수준의 예측 성능을 보였다 |

## 15. 최종 점검 체크리스트

프로젝트를 마무리할 때는 다음 항목을 확인합니다.

| 점검 항목 | 확인 |
| --- | --- |
| 분석 목적과 질문이 명확한가? | □ |
| 원본 데이터 4개를 불러왔는가? | □ |
| 데이터 구조 요약표를 저장했는가? | □ |
| 전처리 기준을 설명할 수 있는가? | □ |
| 전처리 결과 CSV를 저장했는가? | □ |
| 병합 후 행 수와 결측치를 확인했는가? | □ |
| 카테고리별 매출 분석을 수행했는가? | □ |
| 월별 매출 분석을 수행했는가? | □ |
| 고객별 구매 금액 분석을 수행했는가? | □ |
| 상품별 매출 분석을 수행했는가? | □ |
| 그래프 3개 이상을 저장했는가? | □ |
| 회귀 또는 분류 모델을 1개 이상 포함했는가? | □ |
| 모델 평가 지표를 해석했는가? | □ |
| 데이터 누수 가능성을 확인했는가? | □ |
| 인사이트 카드를 작성했는가? | □ |
| LLM 활용 및 검증 기록을 작성했는가? | □ |
| 외부 데이터 확장 아이디어를 정리했는가? | □ |
| 자동화 설계서를 작성했는가? | □ |
| 최종 보고서 Markdown 파일을 작성했는가? | □ |
| 데이터에 없는 원인을 단정하지 않았는가? | □ |
| 개인정보 노출 위험을 확인했는가? | □ |

체크리스트도 파일로 저장할 수 있습니다.

```python
submission_checklist = pd.DataFrame({
    "check_item": [
        "분석 목적과 질문이 명확한가?",
        "원본 데이터 4개를 불러왔는가?",
        "데이터 구조 요약표를 저장했는가?",
        "전처리 기준을 설명할 수 있는가?",
        "전처리 결과 CSV를 저장했는가?",
        "병합 후 행 수와 결측치를 확인했는가?",
        "카테고리별 매출 분석을 수행했는가?",
        "월별 매출 분석을 수행했는가?",
        "고객별 구매 금액 분석을 수행했는가?",
        "상품별 매출 분석을 수행했는가?",
        "그래프 3개 이상을 저장했는가?",
        "회귀 또는 분류 모델을 1개 이상 포함했는가?",
        "모델 평가 지표를 해석했는가?",
        "데이터 누수 가능성을 확인했는가?",
        "인사이트 카드를 작성했는가?",
        "LLM 활용 및 검증 기록을 작성했는가?",
        "외부 데이터 확장 아이디어를 정리했는가?",
        "자동화 설계서를 작성했는가?",
        "최종 보고서 Markdown 파일을 작성했는가?",
        "데이터에 없는 원인을 단정하지 않았는가?",
        "개인정보 노출 위험을 확인했는가?"
    ],
    "result": ["□"] * 21,
    "memo": [""] * 21
})

submission_checklist.to_csv(report_dir / "ch15_submission_checklist.csv", index=False)
submission_checklist
```

## 16. LLM에게 최종 프로젝트를 검토시키기

최종 제출 전에는 LLM을 검토 도구로 사용할 수 있습니다. 단, 원본 데이터나 개인정보를 넣지 말고 보고서 구조, 요약표, 해석 문장 중심으로 검토를 요청합니다.

```text
다음 기준으로 데이터 분석 최종 프로젝트 보고서를 검토해 주세요.

검토 기준:
1. 분석 목적이 명확한가?
2. 데이터 개요가 충분한가?
3. 전처리 기준이 설명되어 있는가?
4. 분석 질문과 결과가 연결되어 있는가?
5. 그래프가 질문에 맞게 선택되었는가?
6. 회귀 또는 분류 모델의 평가 지표가 적절히 해석되었는가?
7. 데이터 누수 가능성을 언급했는가?
8. 해석에서 원인을 단정하지 않았는가?
9. 한계점과 다음 단계가 포함되어 있는가?
10. LLM 활용 및 검증 기록이 있는가?
11. 외부 데이터 확장 아이디어가 현실적인가?
12. 자동화 설계가 현실적인가?

출력 형식:
- 항목
- 현재 상태
- 보완 필요 여부
- 수정 제안
```

발표용 요약을 요청할 수도 있습니다.

```text
온라인 쇼핑몰 데이터 분석 최종 프로젝트 결과를 3분 발표용으로 요약해 주세요.

포함할 내용:
1. 프로젝트 목적
2. 사용 데이터
3. 주요 분석 결과 3개
4. 머신러닝 모델 결과 요약
5. LLM 활용 및 검증 방식
6. 한계점
7. 외부 데이터 확장 아이디어
8. 자동화 제안
9. 다음 단계

조건:
- 데이터에 없는 원인을 단정하지 말 것
- 발표자가 그대로 읽을 수 있는 자연스러운 문장으로 작성할 것
```

## 17. 마무리

최종 프로젝트는 이 책에서 다룬 전체 흐름을 하나로 연결하는 작업입니다. 좋은 프로젝트는 코드가 많은 프로젝트가 아니라, 질문과 데이터, 분석, 시각화, 모델, 해석, 보고서가 자연스럽게 이어지는 프로젝트입니다.

데이터 분석에서 중요한 것은 도구를 많이 사용하는 것이 아닙니다. pandas, 시각화, 머신러닝, LLM, 외부 데이터, 자동화는 모두 분석 목적을 더 잘 달성하기 위한 수단입니다. 최종 보고서에는 내가 어떤 질문을 던졌고, 어떤 데이터로 확인했으며, 무엇을 알 수 있었고, 무엇은 아직 알 수 없는지 분명하게 남아 있어야 합니다.

이 프로젝트를 완성했다면 하나의 데이터 분석 업무 흐름을 처음부터 끝까지 경험한 것입니다. 다음 단계는 같은 구조를 다른 데이터와 다른 문제에 적용해 보는 것입니다. 데이터가 달라져도 기본 흐름은 크게 달라지지 않습니다. 질문을 정의하고, 데이터를 확인하고, 결과를 검증하고, 조심스럽게 해석하는 태도가 가장 중요한 분석 역량입니다.
