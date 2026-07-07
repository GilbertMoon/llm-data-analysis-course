# 8장. 작은 데이터 분석 프로젝트 완성하기

지금까지는 데이터 분석의 각 단계를 하나씩 나누어 살펴보았습니다. 데이터를 불러오고, 구조를 확인하고, pandas로 집계하고, 전처리하고, EDA 질문을 만들고, 시각화까지 진행했습니다. 각각의 단계는 따로 배울 수 있지만, 실제 분석에서는 이 과정들이 하나의 흐름으로 이어집니다.

이 장에서는 온라인 쇼핑몰 운영 데이터를 사용해 작은 분석 프로젝트를 완성합니다. 복잡한 머신러닝 모델을 만드는 것이 목표는 아닙니다. 원본 데이터를 확인하고, 전처리하고, 분석 질문을 만들고, pandas로 지표를 계산하고, 그래프로 표현하고, 마지막에 짧은 보고서로 정리하는 과정이 핵심입니다.

중간 프로젝트는 지금까지 익힌 기초 분석 흐름을 한 번에 연결해 보는 지점입니다. 이 프로젝트를 마치면 데이터 분석이 단순히 코드 조각을 실행하는 일이 아니라, **질문에서 시작해 결과와 해석으로 이어지는 재현 가능한 작업 흐름**이라는 점을 더 분명하게 이해할 수 있습니다.

<figure class="figure">
  <img src="../assets/images/ch08/ch08_project_overview_flow.png" alt="중간 실습 프로젝트 전체 흐름도">
  <figcaption>그림 8-1. 중간 프로젝트 전체 흐름도</figcaption>
</figure>

## 1. 프로젝트는 분석 흐름을 하나로 묶는 일이다

데이터 분석을 배울 때는 기능을 하나씩 익히는 시간이 필요합니다. `read_csv()`로 데이터를 불러오고, `groupby()`로 집계하고, `to_datetime()`으로 날짜를 변환하고, `matplotlib`으로 그래프를 그리는 식입니다. 하지만 실제 프로젝트에서는 이런 기능들이 독립적으로 존재하지 않습니다.

예를 들어 카테고리별 매출을 알고 싶다면 먼저 주문 상세 데이터와 상품 데이터를 연결해야 합니다. 연결하기 전에 상품 ID가 잘 유지되는지 확인해야 하고, 수량과 단가가 숫자형인지도 점검해야 합니다. 그래프를 그린 뒤에는 매출이 높은 카테고리가 정말 많이 팔린 것인지, 단가가 높아서 매출이 커진 것인지 다시 질문해야 합니다.

프로젝트형 분석은 다음 단계를 하나의 흐름으로 연결합니다.

| 단계 | 하는 일 | 남기는 결과 |
| --- | --- | --- |
| 질문 정리 | 무엇을 알고 싶은지 정함 | 분석 질문 목록 |
| 데이터 확인 | 파일, 컬럼, 타입, 결측치 확인 | 데이터 구조 요약 |
| 전처리 | 분석 가능한 형태로 정리 | clean 데이터 |
| 병합과 집계 | 질문에 맞는 지표 계산 | 집계표 |
| 시각화 | 결과를 그래프로 표현 | 이미지 파일 |
| 해석 | 관찰, 가설, 한계 정리 | 해석 메모 |
| 보고서 | 전체 과정을 문서화 | Markdown 보고서 |
| 검증 | 코드와 해석의 오류 확인 | 체크리스트 또는 검토 메모 |

각 단계를 분리해서 생각하되, 최종적으로는 하나의 분석 이야기로 연결하는 것이 중요합니다.

## 2. 이번 프로젝트의 상황

온라인 쇼핑몰 운영자가 최근 주문 데이터를 바탕으로 기본 현황을 파악하려고 한다고 가정해 보겠습니다. 운영자는 어떤 카테고리가 매출에 많이 기여하는지, 월별 매출 흐름은 어떤지, 구매 금액이 높은 고객은 누구인지, 주문 상태는 어떻게 분포하는지 알고 싶어 합니다.

현재 사용할 수 있는 데이터는 고객, 상품, 주문, 주문 상세 파일입니다. 이 데이터만으로 모든 것을 설명할 수는 없습니다. 예를 들어 고객 만족도, 광고 효과, 재고 부족, 프로모션 여부는 현재 데이터에 들어 있지 않을 수 있습니다. 따라서 이번 프로젝트에서는 현재 데이터로 답할 수 있는 질문에 집중합니다.

| 분석 질문 | 주요 지표 | 결과 형태 |
| --- | --- | --- |
| 카테고리별 매출은 어떻게 다른가? | 총매출, 판매 수량, 매출 비중 | 집계표, 막대그래프 |
| 월별 매출과 주문 수는 어떻게 변하는가? | 월별 매출, 주문 수, 평균 주문 금액 | 집계표, 선그래프 |
| 구매 금액 상위 고객은 누구인가? | 고객별 총 구매 금액, 주문 횟수, 평균 주문 금액 | 집계표, 막대그래프 |
| 주문 상태별 주문 수는 어떻게 분포하는가? | 주문 상태별 주문 수 | 요약표 |

좋은 프로젝트 질문은 현재 데이터로 답할 수 있어야 합니다. 다음과 같은 질문은 중요하지만, 현재 데이터만으로는 바로 답하기 어렵습니다.

- 고객이 왜 이탈했는가?
- 고객 만족도는 어떤가?
- 광고가 매출에 어떤 영향을 주었는가?
- 재구매 의도는 높은가?

이 질문들은 추가 데이터가 있을 때 별도 프로젝트로 확장할 수 있습니다.

## 3. 재현 가능한 분석 파이프라인

분석 파이프라인은 데이터가 들어와 결과 보고서가 나오기까지의 처리 흐름입니다. 재현 가능한 파이프라인을 만들면 같은 코드를 다시 실행했을 때 같은 결과를 얻을 수 있습니다.

이번 프로젝트에서는 다음 흐름을 사용합니다.

1. 원본 데이터 불러오기
2. 데이터 구조 확인
3. 전처리 수행
4. 분석용 데이터 병합
5. 주요 지표 계산
6. 시각화 생성
7. 결과 파일 저장
8. 보고서 작성
9. LLM을 활용한 검토
10. 최종 결과 정리

<figure class="figure">
  <img src="../assets/images/ch08/ch08_analysis_pipeline.png" alt="중간 프로젝트 분석 파이프라인">
  <figcaption>그림 8-2. 중간 프로젝트 분석 파이프라인</figcaption>
</figure>

재현 가능성을 높이려면 파일 경로, 코드 실행 순서, 전처리 기준, 저장 파일명을 명확히 해야 합니다. 특히 Notebook에서만 결과를 확인하고 끝내지 말고, 주요 집계표와 그래프를 파일로 저장해 두는 습관이 필요합니다.

## 4. 보고서는 코드의 설명서가 아니다

분석 보고서는 코드를 그대로 설명하는 문서가 아닙니다. 보고서는 분석 목적, 데이터, 처리 기준, 주요 결과, 해석, 한계를 읽는 사람이 이해할 수 있도록 정리한 문서입니다.

이번 프로젝트 보고서는 다음 구조를 가질 수 있습니다.

| 섹션 | 포함 내용 |
| --- | --- |
| 분석 목적 | 무엇을 알고 싶은지 설명 |
| 데이터 개요 | 사용한 파일과 주요 컬럼 |
| 전처리 내용 | 결측치, 중복, 타입 변환, 이상값 처리 기준 |
| 분석 질문 | 이번 프로젝트에서 답할 질문 |
| 주요 분석 결과 | 표와 그래프 중심의 결과 |
| 결과 해석 | 관찰 내용과 추가 확인 필요 사항 |
| 한계점 | 현재 데이터로 알 수 없는 것 |
| 다음 단계 | 추가 분석 또는 개선 방향 |

<figure class="figure">
  <img src="../assets/images/ch08/ch08_report_structure.png" alt="중간 프로젝트 보고서 구조">
  <figcaption>그림 8-3. 중간 프로젝트 보고서 구조</figcaption>
</figure>

보고서에서 가장 조심해야 할 점은 관찰과 원인을 섞지 않는 것입니다. “전자기기 매출이 가장 높다”는 데이터에서 확인한 관찰입니다. 하지만 “전자기기 매출이 높은 이유는 광고 효과 때문이다”라고 말하려면 광고 데이터가 필요합니다. 현재 데이터에 없는 원인은 가설로만 표현해야 합니다.

## 5. 프로젝트 작업 공간 준비하기

전체 코드는 `notebooks/ch08_midterm_project.ipynb`에서 진행할 수 있습니다. 먼저 필요한 패키지를 불러옵니다.

```python
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
```

Notebook이 프로젝트 루트에서 실행되는지, `notebooks` 폴더 안에서 실행되는지에 따라 상대 경로가 달라질 수 있습니다. 다음 코드는 현재 위치를 기준으로 기본 폴더를 자동으로 정합니다.

```python
current_dir = Path.cwd()

if current_dir.name == "notebooks":
    base_dir = current_dir.parent
else:
    base_dir = current_dir
```

작업 경로를 설정합니다.

```python
raw_dir = base_dir / "data" / "raw"
processed_dir = base_dir / "data" / "processed"
report_dir = base_dir / "reports"
figure_dir = report_dir / "figures"

processed_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)
figure_dir.mkdir(parents=True, exist_ok=True)
```

`to_markdown()`을 사용할 때 환경에 따라 `tabulate` 패키지가 필요할 수 있습니다. 오류가 발생하면 터미널이나 Notebook에서 다음 명령을 실행합니다.

```text
pip install tabulate
```

## 6. 원본 데이터를 확인한다

먼저 원본 데이터를 불러옵니다.

```python
customers = pd.read_csv(raw_dir / "customers.csv")
products = pd.read_csv(raw_dir / "products.csv")
orders = pd.read_csv(raw_dir / "orders.csv")
order_items = pd.read_csv(raw_dir / "order_items.csv")
```

데이터 크기를 요약합니다.

```python
dataset_summary = pd.DataFrame({
    "dataset": ["customers", "products", "orders", "order_items"],
    "rows": [customers.shape[0], products.shape[0], orders.shape[0], order_items.shape[0]],
    "columns": [customers.shape[1], products.shape[1], orders.shape[1], order_items.shape[1]]
})

dataset_summary
```

데이터 개요는 보고서에 사용할 수 있도록 저장합니다.

```python
dataset_summary.to_csv(report_dir / "ch08_dataset_summary.csv", index=False)
```

분석을 시작하기 전에 각 데이터셋의 구조를 빠르게 점검합니다.

```python
datasets = {
    "customers": customers,
    "products": products,
    "orders": orders,
    "order_items": order_items
}

for name, df in datasets.items():
    print(f"\n===== {name} =====")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print("missing values:", df.isna().sum().sum())
    print("duplicated rows:", df.duplicated().sum())
```

이 단계는 단순한 확인처럼 보이지만 중요합니다. 데이터 크기, 컬럼명, 결측치, 중복 상태를 모른 채 전처리나 집계를 시작하면 뒤에서 오류를 찾기 어려워집니다.

## 7. 전처리는 원본을 보존하면서 진행한다

전처리는 원본 DataFrame을 직접 수정하지 않고 복사본을 만들어 진행합니다. 먼저 문자열 공백 제거와 숫자 변환에 사용할 함수를 준비합니다.

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

고객 데이터를 정리합니다.

```python
customers_clean = customers.copy()
customers_clean = strip_string_columns(customers_clean)

if "age" in customers_clean.columns:
    customers_clean["age"] = pd.to_numeric(customers_clean["age"], errors="coerce")
    customers_clean["age"] = customers_clean["age"].fillna(customers_clean["age"].median())

if "city" in customers_clean.columns:
    customers_clean["city"] = customers_clean["city"].fillna("Unknown")

if "signup_date" in customers_clean.columns:
    customers_clean["signup_date"] = pd.to_datetime(
        customers_clean["signup_date"],
        errors="coerce"
    )

customers_clean = customers_clean.drop_duplicates()
```

상품 데이터를 정리합니다.

```python
products_clean = products.copy()
products_clean = strip_string_columns(products_clean)

if "price" in products_clean.columns:
    products_clean["price"] = to_number(products_clean["price"])
    products_clean = products_clean[products_clean["price"] > 0]

products_clean = products_clean.drop_duplicates()
```

주문 데이터를 정리합니다.

```python
orders_clean = orders.copy()
orders_clean = strip_string_columns(orders_clean)

if "order_date" in orders_clean.columns:
    orders_clean["order_date"] = pd.to_datetime(
        orders_clean["order_date"],
        errors="coerce"
    )
    orders_clean["order_month"] = orders_clean["order_date"].dt.to_period("M").astype(str)

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

주문 상세 데이터를 정리하고 `line_total`을 만듭니다.

```python
order_items_clean = order_items.copy()
order_items_clean = strip_string_columns(order_items_clean)

if "quantity" in order_items_clean.columns:
    order_items_clean["quantity"] = to_number(order_items_clean["quantity"])

if "unit_price" in order_items_clean.columns:
    order_items_clean["unit_price"] = to_number(order_items_clean["unit_price"])

if "quantity" in order_items_clean.columns:
    order_items_clean = order_items_clean[order_items_clean["quantity"] > 0]

if "unit_price" in order_items_clean.columns:
    order_items_clean = order_items_clean[order_items_clean["unit_price"] > 0]

if {"quantity", "unit_price"}.issubset(order_items_clean.columns):
    order_items_clean["line_total"] = (
        order_items_clean["quantity"] * order_items_clean["unit_price"]
    )

order_items_clean = order_items_clean.drop_duplicates()
```

전처리된 데이터는 `data/processed`에 저장합니다.

```python
customers_clean.to_csv(processed_dir / "customers_clean.csv", index=False)
products_clean.to_csv(processed_dir / "products_clean.csv", index=False)
orders_clean.to_csv(processed_dir / "orders_clean.csv", index=False)
order_items_clean.to_csv(processed_dir / "order_items_clean.csv", index=False)
```

전처리 전후 크기를 비교합니다.

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

preprocessing_comparison = dataset_summary.merge(
    processed_summary,
    on="dataset"
)

preprocessing_comparison
```

전처리 과정에서 일부 행을 제외했다면 파일 간 키 관계가 깨지지 않았는지도 확인합니다.

```python
invalid_customers = orders_clean[
    ~orders_clean["customer_id"].isin(customers_clean["customer_id"])
]

invalid_orders = order_items_clean[
    ~order_items_clean["order_id"].isin(orders_clean["order_id"])
]

invalid_products = order_items_clean[
    ~order_items_clean["product_id"].isin(products_clean["product_id"])
]

print("customers에 없는 customer_id 수:", len(invalid_customers))
print("orders에 없는 order_id 수:", len(invalid_orders))
print("products에 없는 product_id 수:", len(invalid_products))
```

키 관계 확인은 병합 분석 전의 안전장치입니다. 관계가 깨져 있으면 이후 매출 집계에서 누락값이 생길 수 있습니다.

## 8. 분석용 데이터를 연결한다

카테고리별 매출을 계산하려면 주문 상세와 상품 정보를 연결해야 합니다.

```python
sales_items = order_items_clean.merge(
    products_clean,
    on="product_id",
    how="left"
)
```

병합 후에는 행 수와 누락 여부를 확인합니다.

```python
print("병합 전 order_items_clean:", order_items_clean.shape)
print("병합 후 sales_items:", sales_items.shape)
print("상품명 누락:", sales_items["product_name"].isna().sum())
print("카테고리 누락:", sales_items["category"].isna().sum())
```

월별 매출과 고객별 구매 금액을 계산하려면 주문 상세와 주문 데이터, 고객 데이터를 차례대로 연결합니다.

```python
order_sales = order_items_clean.merge(
    orders_clean,
    on="order_id",
    how="left"
)
```

```python
customer_sales_base = order_sales.merge(
    customers_clean,
    on="customer_id",
    how="left"
)
```

병합은 프로젝트에서 자주 쓰이지만 위험한 지점이기도 합니다. 병합 기준 컬럼이 중복되어 있거나 누락되어 있으면 결과 행 수가 예상과 달라질 수 있습니다. 병합 후에는 항상 행 수와 누락값을 확인합니다.

## 9. 주요 지표를 계산한다

먼저 카테고리별 매출을 계산합니다.

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

category_sales
```

```python
category_sales.to_csv(report_dir / "ch08_category_sales.csv", index=False)
```

월별 매출과 주문 수를 계산합니다.

```python
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

```python
monthly_sales.to_csv(report_dir / "ch08_monthly_sales.csv", index=False)
```

고객별 구매 금액과 주문 횟수를 계산합니다.

```python
customer_sales = (
    customer_sales_base
    .groupby(["customer_id", "name", "city"], as_index=False)
    .agg(
        order_count=("order_id", "nunique"),
        total_sales=("line_total", "sum")
    )
    .sort_values("total_sales", ascending=False)
)

customer_sales["avg_order_value"] = (
    customer_sales["total_sales"] / customer_sales["order_count"]
).round(0)

customer_sales.head(10)
```

```python
customer_sales.to_csv(report_dir / "ch08_customer_sales.csv", index=False)
```

주문 상태별 주문 수도 확인합니다.

```python
order_status_summary = (
    orders_clean["order_status"]
    .value_counts()
    .reset_index()
)

order_status_summary.columns = ["order_status", "order_count"]
order_status_summary
```

## 10. 결과를 시각화한다

시각화는 분석 질문을 더 직관적으로 보여 주는 도구입니다. 그래프를 그릴 때는 “어떤 질문에 답하기 위한 그래프인가”를 먼저 생각해야 합니다.

카테고리별 매출은 막대그래프로 표현할 수 있습니다.

```python
plt.figure(figsize=(10, 5))

plt.bar(
    category_sales["category"],
    category_sales["total_sales"]
)

plt.title("카테고리별 매출")
plt.xlabel("카테고리")
plt.ylabel("총매출")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(figure_dir / "ch08_category_sales.png", dpi=150)
plt.show()
```

월별 매출 흐름은 선그래프로 표현할 수 있습니다.

```python
plt.figure(figsize=(10, 5))

plt.plot(
    monthly_sales["order_month"],
    monthly_sales["total_sales"],
    marker="o"
)

plt.title("월별 매출 추이")
plt.xlabel("주문 월")
plt.ylabel("총매출")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(figure_dir / "ch08_monthly_sales.png", dpi=150)
plt.show()
```

구매 금액 상위 고객은 가로 막대그래프로 표현할 수 있습니다. 보고서에 고객명을 직접 노출하지 않기 위해 고객 ID 기반 라벨을 사용할 수 있습니다.

```python
top_customers = customer_sales.head(10).copy()
top_customers["customer_label"] = "Customer " + top_customers["customer_id"].astype(str)
top_customers = top_customers.sort_values("total_sales")
```

```python
plt.figure(figsize=(10, 6))

plt.barh(
    top_customers["customer_label"],
    top_customers["total_sales"]
)

plt.title("구매 금액 상위 10명 고객")
plt.xlabel("총 구매 금액")
plt.ylabel("고객")
plt.tight_layout()

plt.savefig(figure_dir / "ch08_top_customers.png", dpi=150)
plt.show()
```

그래프는 저장된 이미지 파일로 남겨 두면 보고서나 발표 자료에서 재사용하기 쉽습니다.

## 11. 해석 메모를 남긴다

분석 결과는 숫자와 그래프만으로 끝나지 않습니다. 어떤 관찰을 했고, 무엇을 조심해서 해석해야 하는지 함께 기록해야 합니다.

```python
interpretation_notes = pd.DataFrame({
    "analysis": [
        "카테고리별 매출",
        "월별 매출",
        "고객별 구매 금액",
        "주문 상태별 주문 수"
    ],
    "observation": [
        "매출이 높은 카테고리를 확인할 수 있습니다.",
        "시간에 따른 매출 증가와 감소 흐름을 확인할 수 있습니다.",
        "구매 금액이 높은 고객 후보를 확인할 수 있습니다.",
        "주문 상태의 분포를 확인할 수 있습니다."
    ],
    "caution": [
        "매출이 높은 이유가 판매 수량 때문인지 단가 때문인지 추가 확인이 필요합니다.",
        "매출 변화의 원인을 설명하려면 프로모션, 계절성, 주문 수 변화 확인이 필요합니다.",
        "일회성 고액 구매 고객과 반복 구매 고객을 구분해야 합니다.",
        "취소 주문이 매출 계산에 포함되었는지 확인해야 합니다."
    ]
})

interpretation_notes
```

해석 메모를 작성할 때는 관찰과 원인을 구분합니다. “월별 매출이 증가했다”는 관찰이지만, “프로모션 때문에 증가했다”는 현재 데이터만으로는 단정하기 어렵습니다.

## 12. 보고서로 정리한다

마지막으로 프로젝트 결과를 Markdown 보고서로 저장합니다.

```python
report_text = f"""
# Chapter 8 중간 프로젝트 보고서

## 1. 분석 목적

온라인 쇼핑몰 고객, 상품, 주문, 주문 상세 데이터를 사용해 기본 매출 현황과 고객 구매 패턴을 분석했습니다.

## 2. 데이터 개요

{dataset_summary.to_markdown(index=False)}

## 3. 전처리 전후 비교

{preprocessing_comparison.to_markdown(index=False)}

## 4. 주요 분석 질문

1. 카테고리별 매출은 어떻게 다른가?
2. 월별 매출과 주문 수는 어떻게 변하는가?
3. 구매 금액 상위 고객은 누구인가?
4. 주문 상태별 주문 수는 어떻게 분포하는가?

## 5. 카테고리별 매출

{category_sales.to_markdown(index=False)}

## 6. 월별 매출

{monthly_sales.to_markdown(index=False)}

## 7. 구매 금액 상위 고객

{customer_sales.head(10).to_markdown(index=False)}

## 8. 해석 메모

{interpretation_notes.to_markdown(index=False)}

## 9. 한계점

- 현재 데이터만으로 고객 만족도나 이탈 이유는 분석할 수 없습니다.
- 매출 변화의 원인을 설명하려면 프로모션, 광고, 재고, 계절성 데이터가 추가로 필요합니다.
- 구매 금액 상위 고객은 주문 횟수와 평균 주문 금액을 함께 해석해야 합니다.
- 취소 주문과 환불 주문 처리 기준에 따라 매출 결과가 달라질 수 있습니다.

## 10. 다음 단계

- 카테고리별 판매 수량과 평균 단가를 함께 비교합니다.
- 월별 매출 변동 원인을 추가 데이터와 함께 분석합니다.
- 고객별 구매 금액을 기준으로 고객 세분화를 시도합니다.
- LLM을 활용해 보고서 문장을 보완하되, 데이터에 없는 원인은 단정하지 않습니다.
"""

report_path = report_dir / "ch08_midterm_report.md"
report_path.write_text(report_text, encoding="utf-8")
```

최종적으로 다음 파일들이 정리되어 있으면 프로젝트 흐름을 재현하기 쉽습니다.

- `notebooks/ch08_midterm_project.ipynb`
- `reports/ch08_midterm_report.md`
- `reports/ch08_dataset_summary.csv`
- `reports/ch08_category_sales.csv`
- `reports/ch08_monthly_sales.csv`
- `reports/ch08_customer_sales.csv`
- `reports/figures/ch08_category_sales.png`
- `reports/figures/ch08_monthly_sales.png`
- `reports/figures/ch08_top_customers.png`

<figure class="figure">
  <img src="../assets/images/ch08/ch08_project_deliverables.png" alt="중간 프로젝트 산출물 구성">
  <figcaption>그림 8-5. 중간 프로젝트 산출물 구성</figcaption>
</figure>

## 13. LLM은 검토 파트너로 활용한다

LLM은 프로젝트 과정에서 분석 질문을 다듬고, 전처리 코드의 위험 요소를 찾고, 보고서 문장을 정리하는 데 도움을 줄 수 있습니다. 하지만 LLM이 만든 내용은 반드시 실제 데이터와 비교해 검증해야 합니다.

분석 질문을 검토할 때는 다음처럼 요청할 수 있습니다.

```text
온라인 쇼핑몰 데이터로 데이터 분석 프로젝트를 진행하고 있습니다.

사용 데이터:
- customers: 고객 정보
- products: 상품 정보
- orders: 주문 정보
- order_items: 주문 상세 정보

초안 분석 질문:
1. 카테고리별 매출은 어떻게 다른가?
2. 월별 매출과 주문 수는 어떻게 변하는가?
3. 구매 금액 상위 고객은 누구인가?
4. 주문 상태별 주문 수는 어떻게 분포하는가?
5. 상품 가격과 판매 수량은 관계가 있는가?

각 질문이 현재 데이터로 분석 가능한지 검토해 주세요.
각 질문에 필요한 데이터, 지표, pandas 기능을 표로 정리해 주세요.
데이터에 없는 원인은 추측하지 말아 주세요.
```

전처리 코드를 검토할 때는 기준을 명확히 제시합니다.

```text
다음 전처리 코드가 안전한지 검토해 주세요.

검토 기준:
- 원본 데이터를 직접 수정하는지
- 결측치를 "nan" 문자열로 바꾸는 문제가 있는지
- 날짜 변환 실패 건수를 확인하는지
- 숫자형 변환 실패를 확인하는지
- 이상값을 무조건 삭제하고 있지 않은지
- 전처리 전후 데이터 크기를 비교하는지
- 파일 간 키 관계를 확인하는지

문제점과 개선 방향을 표로 정리해 주세요.
```

보고서 해석을 요청할 때는 원인 단정을 막아야 합니다.

```text
다음은 데이터 분석 프로젝트의 주요 결과입니다.

카테고리별 매출표:
- category
- total_quantity
- total_sales
- sales_ratio

월별 매출표:
- order_month
- total_sales
- order_count
- avg_order_value

고객별 구매 금액표:
- customer_id
- city
- order_count
- total_sales
- avg_order_value

이 결과를 바탕으로 보고서 해석 문장을 작성해 주세요.

조건:
- 데이터에 없는 원인은 단정하지 말 것
- 관찰 결과와 원인 가설을 구분할 것
- 추가로 확인해야 할 분석 질문을 포함할 것
- 실무 보고서 문체로 작성할 것
```

LLM은 초안을 빠르게 만드는 데 도움이 되지만, 데이터의 의미를 이해하고 최종 판단을 내리는 책임은 분석자에게 있습니다.

## 14. 프로젝트 결과를 읽는 방법

이번 프로젝트의 결과는 최종 정답이 아니라 현재 데이터로 확인한 1차 분석 결과입니다. 카테고리별 매출이 높다고 해서 바로 “그 카테고리가 가장 인기 있다”고 말할 수는 없습니다. 매출은 판매 수량과 단가의 영향을 함께 받기 때문입니다.

월별 매출도 마찬가지입니다. 특정 월에 매출이 증가했다면 주문 수가 늘었는지, 평균 주문 금액이 늘었는지, 특정 카테고리 매출이 늘었는지를 추가로 확인해야 합니다. 고객별 구매 금액을 볼 때도 한 번의 고액 구매와 반복 구매를 구분해야 합니다.

프로젝트 보고서에서는 다음처럼 표현하는 것이 안전합니다.

```text
관찰: 카테고리별 매출 결과에서 특정 카테고리의 매출 비중이 높게 나타났습니다.
주의: 매출이 높은 이유가 판매 수량 때문인지 평균 단가 때문인지는 추가 분석이 필요합니다.
다음 질문: 카테고리별 판매 수량과 평균 단가를 함께 비교해 볼 필요가 있습니다.
```

이렇게 쓰면 데이터에서 확인한 사실과 추가로 검증해야 할 내용을 구분할 수 있습니다.

## 15. 다음 장으로 이어지는 흐름

중간 프로젝트까지는 데이터 분석의 기본 흐름을 다루었습니다. 데이터를 불러오고, 전처리하고, 질문을 만들고, pandas로 집계하고, 시각화와 보고서로 정리했습니다.

다음 장부터는 머신러닝으로 확장합니다. 지금까지의 분석이 “현재 데이터를 이해하는 과정”이었다면, 이후에는 데이터를 사용해 값을 예측하거나 분류하는 방법을 살펴봅니다. 회귀 분석에서는 매출이나 가격처럼 연속적인 값을 예측하고, 분류 분석에서는 주문 취소 여부나 구매 여부처럼 범주를 예측합니다.

머신러닝도 결국 좋은 데이터와 좋은 질문에서 출발합니다. 이번 프로젝트에서 정리한 전처리, 지표 설계, 결과 해석 습관은 이후 모델링 실습에서도 그대로 이어집니다.
