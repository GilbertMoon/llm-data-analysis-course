# 8장. 작은 데이터 분석 프로젝트 완성하기

지금까지는 데이터 분석의 각 단계를 나누어 살펴보았습니다. 데이터를 불러오고 구조를 확인하고, pandas로 집계하고, 전처리하고, EDA 질문을 만들고, 시각화까지 진행했습니다. 이 장에서는 이 과정을 하나의 재현 가능한 프로젝트로 연결합니다.

온라인 쇼핑몰의 고객, 상품, 주문, 주문 상세 데이터를 사용해 기본 운영 현황을 분석합니다. 복잡한 머신러닝 모델을 만드는 것이 목표는 아닙니다. **질문 설정 → 데이터 점검 → 전처리 → 안전한 병합 → 완료 주문 기준 집계 → 시각화 → 해석 → 보고서 작성 → 검증**의 흐름을 완성하는 것이 핵심입니다.

중간 프로젝트를 마치면 데이터 분석이 코드 조각을 실행하는 일이 아니라, 입력 데이터와 처리 기준, 산출물과 해석을 함께 관리하는 작업이라는 점을 이해할 수 있습니다.

<figure class="figure">
  <img src="../assets/images/ch08/ch08_project_overview_flow.png" alt="중간 프로젝트 전체 흐름도">
  <figcaption>그림 8-1. 중간 프로젝트 전체 흐름도</figcaption>
</figure>

## 1. 프로젝트 목표와 분석 기준

온라인 쇼핑몰 운영자가 최근 주문 데이터를 바탕으로 기본 현황을 파악하려고 한다고 가정합니다. 이번 프로젝트에서는 다음 질문에 답합니다.

| 분석 질문 | 주요 지표 | 결과 형태 |
| --- | --- | --- |
| 카테고리별 완료 주문 매출은 어떻게 다른가? | 판매 수량, 매출, 매출 비중 | 집계표, 막대그래프 |
| 월별 완료 주문 매출과 주문 수는 어떻게 변하는가? | 월별 매출, 주문 수, 평균 주문 금액 | 집계표, 선그래프 |
| 완료 주문 기준 구매 금액 상위 고객은 누구인가? | 총 구매 금액, 주문 횟수, 평균 주문 금액 | 익명화된 집계표, 막대그래프 |
| 주문 상태별 주문 수는 어떻게 분포하는가? | 상태별 주문 수와 비율 | 요약표 |

이 장에서 **매출**은 별도 설명이 없는 한 `order_status == "completed"`인 주문의 금액을 뜻합니다. 취소 또는 환불 주문을 포함한 금액은 확정 매출과 구분해 **전체 주문 상세 금액**으로 표현합니다.

현재 데이터만으로 고객 만족도, 광고 효과, 재고 부족, 이탈 이유를 단정할 수는 없습니다. 분석 질문은 현재 데이터로 계산할 수 있는 지표와 연결되어야 합니다.

## 2. 재현 가능한 분석 파이프라인

프로젝트형 분석은 다음 단계를 하나의 흐름으로 연결합니다.

| 단계 | 수행 내용 | 주요 산출물 |
| --- | --- | --- |
| 질문 정리 | 현재 데이터로 답할 질문을 정함 | 분석 질문 목록 |
| 데이터 확인 | 파일, 컬럼, 타입, 결측치, 중복 확인 | 데이터 구조 요약 |
| 전처리 | 원본을 보존하고 분석 가능한 형태로 정리 | clean CSV |
| 관계 점검 | 기본키 중복과 외래키 미매칭 확인 | 관계 점검표 |
| 안전한 병합 | `validate`, `indicator`로 병합 검증 | 분석용 DataFrame |
| 지표 계산 | 완료 주문 기준 집계 | 결과 CSV |
| 시각화 | 질문에 맞는 그래프 생성 | PNG 이미지 |
| 해석 | 관찰, 한계, 다음 질문 정리 | 해석 메모 |
| 보고서 | 분석 흐름과 결과를 문서화 | Markdown 보고서 |
| 최종 검증 | 산출물 존재와 개인정보 노출 점검 | 제출 체크리스트 |

<figure class="figure">
  <img src="../assets/images/ch08/ch08_analysis_pipeline.png" alt="중간 프로젝트 분석 파이프라인">
  <figcaption>그림 8-2. 중간 프로젝트 분석 파이프라인</figcaption>
</figure>

재현 가능성을 높이려면 실행 위치, 전처리 기준, 병합 관계, 매출 정의, 저장 파일명을 명확히 해야 합니다. Notebook 화면에서 결과를 확인하고 끝내지 말고 주요 표와 그래프를 파일로 남깁니다.

## 3. 보고서는 코드의 설명서가 아니다

분석 보고서는 코드를 줄 단위로 설명하는 문서가 아닙니다. 읽는 사람이 분석 목적, 데이터, 처리 기준, 주요 결과, 해석, 한계를 이해할 수 있도록 정리해야 합니다.

| 섹션 | 포함 내용 |
| --- | --- |
| 분석 목적 | 무엇을 확인하려는지 설명 |
| 데이터 개요 | 사용 파일, 행·열 수, 주요 컬럼 |
| 분석 기준 | 완료 주문만 매출에 포함한다는 기준 |
| 전처리 내용 | 결측치, 중복, 타입 변환, 이상값 처리 |
| 관계와 병합 검증 | 키 중복, 미매칭, 병합 전후 행 수 |
| 주요 결과 | 표와 그래프 |
| 결과 해석 | 관찰과 추가 확인 사항 |
| 한계점 | 현재 데이터로 알 수 없는 내용 |
| 다음 단계 | 후속 분석 또는 개선 방향 |

<figure class="figure">
  <img src="../assets/images/ch08/ch08_report_structure.png" alt="중간 프로젝트 보고서 구조">
  <figcaption>그림 8-3. 중간 프로젝트 보고서 구조</figcaption>
</figure>

“전자기기 완료 주문 매출이 가장 높다”는 관찰입니다. “광고 효과 때문에 높다”는 광고 데이터가 있어야 검증할 수 있는 가설입니다. 관찰과 원인을 구분해 작성합니다.

## 4. 프로젝트 작업 공간 준비하기

전체 실습은 `notebooks/ch08_midterm_project.ipynb`에서 진행할 수 있으며, 전체 파이프라인은 `python scripts/run_midterm_project.py`로 다시 실행할 수 있습니다.

현재 작업 폴더가 프로젝트 루트 또는 `notebooks` 폴더일 수 있으므로 상위 폴더를 확인해 프로젝트 루트를 찾습니다.

```python
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def find_project_root(start_path):
    start_path = Path(start_path).resolve()
    for candidate in [start_path, *start_path.parents]:
        if (
            (candidate / "requirements.txt").exists()
            and (candidate / "scripts").exists()
        ):
            return candidate
    raise FileNotFoundError("프로젝트 루트 폴더를 찾을 수 없습니다.")


PROJECT_ROOT = find_project_root(Path.cwd())
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"
FIGURE_DIR = REPORT_DIR / "figures"

for path in [PROCESSED_DIR, REPORT_DIR, FIGURE_DIR]:
    path.mkdir(parents=True, exist_ok=True)
```

`to_markdown()`은 `tabulate` 패키지를 사용합니다. 이 저장소의 `requirements.txt`에 포함되어 있으므로 별도 설치보다 먼저 전체 패키지 설치가 완료되었는지 확인합니다.

```powershell
python -m pip install -r requirements.txt
```

## 5. 원본 데이터와 필수 컬럼 확인

필요한 파일이 모두 존재하는지 확인한 뒤 불러옵니다.

```python
required_files = [
    "customers.csv",
    "products.csv",
    "orders.csv",
    "order_items.csv",
]

missing_files = [
    filename
    for filename in required_files
    if not (RAW_DIR / filename).exists()
]

if missing_files:
    raise FileNotFoundError(
        "필요한 파일이 없습니다: " + ", ".join(missing_files)
        + ". 프로젝트 루트에서 "
        + "python scripts/generate_sample_data.py를 실행하세요."
    )

customers = pd.read_csv(RAW_DIR / "customers.csv")
products = pd.read_csv(RAW_DIR / "products.csv")
orders = pd.read_csv(RAW_DIR / "orders.csv")
order_items = pd.read_csv(RAW_DIR / "order_items.csv")
```

이번 프로젝트에서 필요한 컬럼도 확인합니다.

```python
datasets = {
    "customers": customers,
    "products": products,
    "orders": orders,
    "order_items": order_items,
}

required_columns = {
    "customers": ["customer_id", "age", "city"],
    "products": ["product_id", "product_name", "category", "price"],
    "orders": [
        "order_id",
        "customer_id",
        "order_date",
        "order_status",
    ],
    "order_items": [
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    ],
}

for name, columns in required_columns.items():
    missing = [
        column
        for column in columns
        if column not in datasets[name].columns
    ]
    if missing:
        raise KeyError(f"{name}에 필요한 컬럼이 없습니다: {missing}")
```

데이터 구조를 보고서용 표로 저장합니다.

```python
dataset_summary = pd.DataFrame([
    {
        "dataset": name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "missing_values": int(df.isna().sum().sum()),
        "duplicated_rows": int(df.duplicated().sum()),
    }
    for name, df in datasets.items()
])

dataset_summary.to_csv(
    REPORT_DIR / "ch08_dataset_summary.csv",
    index=False,
    encoding="utf-8-sig",
)
```

## 6. 원본을 보존하며 전처리하기

원본 DataFrame은 직접 수정하지 않고 복사본을 사용합니다.

```python
def strip_string_columns(df):
    result = df.copy()
    for column in result.select_dtypes(include="object").columns:
        result[column] = result[column].where(
            result[column].isna(),
            result[column].astype(str).str.strip(),
        )
    return result


def to_number(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )
```

고객 데이터를 정리합니다.

```python
customers_clean = strip_string_columns(customers)
customers_clean["age"] = pd.to_numeric(
    customers_clean["age"],
    errors="coerce",
)

if customers_clean["age"].notna().any():
    customers_clean["age"] = customers_clean["age"].fillna(
        customers_clean["age"].median()
    )

customers_clean["city"] = (
    customers_clean["city"]
    .replace("", pd.NA)
    .fillna("Unknown")
)

customers_clean = customers_clean.drop_duplicates()
```

상품 데이터를 정리합니다.

```python
products_clean = strip_string_columns(products)
products_clean["price"] = to_number(products_clean["price"])
products_clean = products_clean.dropna(
    subset=["product_id", "category", "price"]
)
products_clean = products_clean[products_clean["price"] > 0]
products_clean = products_clean.drop_duplicates()
```

주문 데이터를 정리합니다.

```python
status_map = {
    "complete": "completed",
    "Complete": "completed",
    "COMPLETED": "completed",
    "완료": "completed",
    "cancel": "cancelled",
    "Cancel": "cancelled",
    "CANCELLED": "cancelled",
    "취소": "cancelled",
    "refund": "refunded",
    "Refund": "refunded",
    "REFUNDED": "refunded",
    "환불": "refunded",
}

orders_clean = strip_string_columns(orders)
orders_clean["order_status"] = (
    orders_clean["order_status"].replace(status_map)
)
orders_clean["order_date"] = pd.to_datetime(
    orders_clean["order_date"],
    errors="coerce",
)
orders_clean = orders_clean.dropna(
    subset=["order_id", "customer_id", "order_date", "order_status"]
)
orders_clean["order_month"] = (
    orders_clean["order_date"].dt.to_period("M").astype(str)
)
orders_clean = orders_clean.drop_duplicates()
```

주문 상세 데이터를 정리하고 주문 상세 금액을 만듭니다.

```python
order_items_clean = strip_string_columns(order_items)
order_items_clean["quantity"] = to_number(
    order_items_clean["quantity"]
)
order_items_clean["unit_price"] = to_number(
    order_items_clean["unit_price"]
)
order_items_clean = order_items_clean.dropna(
    subset=[
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    ]
)
order_items_clean = order_items_clean[
    (order_items_clean["quantity"] > 0)
    & (order_items_clean["unit_price"] > 0)
].copy()
order_items_clean["line_total"] = (
    order_items_clean["quantity"]
    * order_items_clean["unit_price"]
)
order_items_clean = order_items_clean.drop_duplicates()
```

전처리된 데이터는 `data/processed`에 저장하고 전후 크기를 비교합니다.

```python
processed_data = {
    "customers": customers_clean,
    "products": products_clean,
    "orders": orders_clean,
    "order_items": order_items_clean,
}

for name, df in processed_data.items():
    df.to_csv(
        PROCESSED_DIR / f"{name}_clean.csv",
        index=False,
        encoding="utf-8-sig",
    )

processed_summary = pd.DataFrame([
    {
        "dataset": name,
        "rows_processed": df.shape[0],
        "columns_processed": df.shape[1],
    }
    for name, df in processed_data.items()
])

preprocessing_comparison = dataset_summary.merge(
    processed_summary,
    on="dataset",
    how="outer",
)
```

숫자형·날짜형 변환 실패를 조용히 무시하지 말고 건수를 기록합니다. 전처리로 행이 제외되었다면 그 이유도 보고서에 남깁니다.

## 7. 키 관계와 병합 조건 검증하기

관계형 데이터에서는 전체 행 중복뿐 아니라 키 컬럼 중복을 확인해야 합니다.

```python
key_duplicate_checks = pd.DataFrame({
    "dataset": [
        "customers",
        "products",
        "orders",
        "order_items",
    ],
    "key": [
        "customer_id",
        "product_id",
        "order_id",
        "order_item_id",
    ],
    "duplicate_count": [
        int(customers_clean["customer_id"].duplicated().sum()),
        int(products_clean["product_id"].duplicated().sum()),
        int(orders_clean["order_id"].duplicated().sum()),
        int(order_items_clean["order_item_id"].duplicated().sum()),
    ],
})
```

외래키 미매칭도 확인합니다.

```python
relationship_checks = pd.DataFrame({
    "check": [
        "orders.customer_id → customers.customer_id",
        "order_items.order_id → orders.order_id",
        "order_items.product_id → products.product_id",
    ],
    "invalid_count": [
        int((~orders_clean["customer_id"].isin(
            customers_clean["customer_id"]
        )).sum()),
        int((~order_items_clean["order_id"].isin(
            orders_clean["order_id"]
        )).sum()),
        int((~order_items_clean["product_id"].isin(
            products_clean["product_id"]
        )).sum()),
    ],
})
```

`left merge`라고 해서 왼쪽 행 수가 자동으로 유지되는 것은 아닙니다. 오른쪽 키가 중복되면 행이 늘어날 수 있습니다. `validate`와 `indicator`를 사용해 병합 관계를 명시하고 미매칭을 확인합니다.

```python
order_sales = order_items_clean.merge(
    orders_clean[
        [
            "order_id",
            "customer_id",
            "order_date",
            "order_month",
            "order_status",
        ]
    ],
    on="order_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)

print(order_sales["_merge"].value_counts())
order_sales = order_sales.drop(columns="_merge")
```

완료 주문만 분석 대상으로 선택합니다.

```python
completed_order_sales = order_sales[
    order_sales["order_status"] == "completed"
].copy()
```

상품 정보를 붙입니다.

```python
completed_sales_items = completed_order_sales.merge(
    products_clean[
        ["product_id", "product_name", "category", "price"]
    ],
    on="product_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)

print(completed_sales_items["_merge"].value_counts())
completed_sales_items = completed_sales_items.drop(columns="_merge")
```

## 8. 완료 주문 기준 지표 계산하기

카테고리별 매출을 계산합니다.

```python
category_sales = (
    completed_sales_items
    .groupby("category", as_index=False)
    .agg(
        total_quantity=("quantity", "sum"),
        total_sales=("line_total", "sum"),
    )
    .sort_values("total_sales", ascending=False)
)

category_sales["sales_ratio"] = (
    category_sales["total_sales"]
    / category_sales["total_sales"].sum()
    * 100
).round(2)
```

월별 매출과 주문 수를 계산합니다.

```python
monthly_sales = (
    completed_order_sales
    .groupby("order_month", as_index=False)
    .agg(
        total_sales=("line_total", "sum"),
        order_count=("order_id", "nunique"),
    )
    .sort_values("order_month")
)

monthly_sales["avg_order_value"] = (
    monthly_sales["total_sales"]
    / monthly_sales["order_count"]
).round(0)
```

고객별 구매 금액은 `customer_id`로 먼저 집계한 뒤 고객 속성을 붙입니다. 고객 이름은 결과 파일에 포함하지 않습니다.

```python
customer_sales = (
    completed_order_sales
    .groupby("customer_id", as_index=False)
    .agg(
        order_count=("order_id", "nunique"),
        total_sales=("line_total", "sum"),
    )
    .sort_values("total_sales", ascending=False)
)

customer_sales["avg_order_value"] = (
    customer_sales["total_sales"]
    / customer_sales["order_count"]
).round(0)

customer_sales = customer_sales.merge(
    customers_clean[["customer_id", "city"]],
    on="customer_id",
    how="left",
    validate="one_to_one",
)

customer_sales["customer_label"] = (
    "Customer "
    + customer_sales["customer_id"].astype(str)
)
```

주문 상태별 주문 수도 계산합니다.

```python
order_status_summary = (
    orders_clean["order_status"]
    .value_counts(dropna=False)
    .rename_axis("order_status")
    .reset_index(name="order_count")
)

order_status_summary["order_ratio"] = (
    order_status_summary["order_count"]
    / order_status_summary["order_count"].sum()
    * 100
).round(2)
```

결과 CSV는 Excel 호환성을 고려해 `utf-8-sig`로 저장합니다.

```python
outputs = {
    "ch08_category_sales.csv": category_sales,
    "ch08_monthly_sales.csv": monthly_sales,
    "ch08_customer_sales.csv": customer_sales,
    "ch08_order_status_summary.csv": order_status_summary,
    "ch08_key_duplicate_checks.csv": key_duplicate_checks,
    "ch08_relationship_checks.csv": relationship_checks,
}

for filename, df in outputs.items():
    df.to_csv(
        REPORT_DIR / filename,
        index=False,
        encoding="utf-8-sig",
    )
```

## 9. 결과를 시각화하기

그래프 제목에도 완료 주문 기준임을 표시합니다.

```python
plt.figure(figsize=(10, 5))
plt.bar(
    category_sales["category"],
    category_sales["total_sales"],
)
plt.title("카테고리별 완료 주문 매출")
plt.xlabel("카테고리")
plt.ylabel("매출")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(
    FIGURE_DIR / "ch08_category_sales.png",
    dpi=150,
    bbox_inches="tight",
)
plt.show()
```

```python
plt.figure(figsize=(10, 5))
plt.plot(
    monthly_sales["order_month"],
    monthly_sales["total_sales"],
    marker="o",
)
plt.title("월별 완료 주문 매출 추이")
plt.xlabel("주문 월")
plt.ylabel("매출")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(
    FIGURE_DIR / "ch08_monthly_sales.png",
    dpi=150,
    bbox_inches="tight",
)
plt.show()
```

```python
top_customers = customer_sales.head(10).sort_values(
    "total_sales"
)

plt.figure(figsize=(10, 6))
plt.barh(
    top_customers["customer_label"],
    top_customers["total_sales"],
)
plt.title("완료 주문 구매 금액 상위 10명")
plt.xlabel("총 구매 금액")
plt.ylabel("익명화 고객")
plt.tight_layout()
plt.savefig(
    FIGURE_DIR / "ch08_top_customers.png",
    dpi=150,
    bbox_inches="tight",
)
plt.show()
```

## 10. 결과를 해석하고 보고서로 정리하기

해석은 관찰, 주의점, 다음 질문을 분리해 작성합니다.

| 분석 | 관찰 | 주의점 | 다음 질문 |
| --- | --- | --- | --- |
| 카테고리별 매출 | 완료 주문 매출 비중이 높은 카테고리를 확인 | 수량과 단가의 영향을 구분해야 함 | 카테고리별 평균 판매 단가는? |
| 월별 매출 | 월별 증가·감소 구간 확인 | 프로모션이나 계절성 원인을 단정할 수 없음 | 주문 수와 평균 주문 금액 중 무엇이 변했는가? |
| 고객별 구매 금액 | 구매 금액 상위 고객군 확인 | 일회성 고액 구매와 반복 구매 구분 필요 | 최근 구매일과 구매 빈도는? |
| 주문 상태 | 완료·취소·환불 비율 확인 | 상태 정의와 처리 기준 확인 필요 | 취소율은 월별로 달라지는가? |

보고서에 들어가는 고객 결과는 실제 이름을 제외하고 `customer_label`, `city`, `order_count`, `total_sales`, `avg_order_value`만 사용합니다.

```python
customer_report = customer_sales[
    [
        "customer_label",
        "city",
        "order_count",
        "total_sales",
        "avg_order_value",
    ]
].head(10)
```

보고서에는 다음 내용을 포함합니다.

1. 분석 목적과 질문
2. 사용 데이터와 데이터 구조
3. 완료 주문 기준을 포함한 분석 기준
4. 전처리 전후 비교
5. 키 중복과 관계 점검
6. 카테고리·월별·고객별 결과
7. 주문 상태 분포
8. 관찰, 한계, 다음 질문
9. LLM 활용 및 검증 기록

## 11. LLM은 검토 파트너로 활용하기

LLM에는 실제 고객명이나 원본 행을 전달하지 않고 구조와 요약 결과만 제공합니다.

```text
온라인 쇼핑몰 중간 프로젝트 결과를 검토해 주세요.

분석 기준:
- 매출은 order_status가 completed인 주문만 포함
- 고객 이름은 제외하고 익명화 라벨 사용
- 병합은 validate와 indicator로 검증

검토 항목:
1. 분석 질문과 지표가 연결되어 있는가?
2. 취소·환불 주문이 매출에 포함되지 않았는가?
3. 병합 후 행 증가 또는 미매칭을 확인했는가?
4. 관찰과 원인 가설을 구분했는가?
5. 개인정보가 불필요하게 노출되지 않았는가?
6. 결과를 재현할 수 있는 파일과 실행 순서가 있는가?

데이터에 없는 원인은 단정하지 말고,
수정이 필요한 부분과 추가 확인 질문을 구분해 주세요.
```

LLM의 제안을 바로 반영하지 말고 실제 컬럼, 값의 종류, 집계 기준, 코드 실행 결과와 비교해 검증합니다.

## 12. 제출물과 최종 검증

최종 산출물은 다음과 같습니다.

- `notebooks/ch08_midterm_project.ipynb`
- `data/processed/customers_clean.csv`
- `data/processed/products_clean.csv`
- `data/processed/orders_clean.csv`
- `data/processed/order_items_clean.csv`
- `reports/ch08_midterm_report.md`
- `reports/ch08_dataset_summary.csv`
- `reports/ch08_preprocessing_comparison.csv`
- `reports/ch08_key_duplicate_checks.csv`
- `reports/ch08_relationship_checks.csv`
- `reports/ch08_category_sales.csv`
- `reports/ch08_monthly_sales.csv`
- `reports/ch08_customer_sales.csv`
- `reports/ch08_order_status_summary.csv`
- `reports/figures/ch08_category_sales.png`
- `reports/figures/ch08_monthly_sales.png`
- `reports/figures/ch08_top_customers.png`

<figure class="figure">
  <img src="../assets/images/ch08/ch08_project_deliverables.png" alt="중간 프로젝트 산출물 구성">
  <figcaption>그림 8-5. 중간 프로젝트 산출물 구성</figcaption>
</figure>

제출 전에는 다음을 확인합니다.

| 검증 항목 | 확인 기준 |
| --- | --- |
| 실행 가능성 | 위에서부터 다시 실행해 오류 없이 완료됨 |
| 매출 기준 | 완료 주문만 카테고리·월별·고객별 매출에 포함 |
| 병합 검증 | 키 중복, 미매칭, 병합 전후 행 수 확인 |
| 개인정보 | 고객 이름·이메일 등 불필요한 정보가 결과에 없음 |
| 결과 일치 | Notebook, CSV, 그래프, 보고서의 수치가 일치 |
| 해석 품질 | 관찰과 원인 가설이 구분됨 |
| 재현성 | 샘플 데이터 생성부터 전체 실행 순서가 기록됨 |
| 산출물 | 필수 파일이 모두 존재하고 비어 있지 않음 |

전체 파이프라인은 프로젝트 루트에서 다음 명령으로 확인할 수 있습니다.

```powershell
python scripts/generate_sample_data.py
python scripts/run_midterm_project.py
```

## 13. 다음 장으로 이어지는 흐름

중간 프로젝트까지는 데이터를 불러오고, 전처리하고, 안전하게 병합하고, 질문에 맞는 지표를 계산하고, 시각화와 보고서로 정리하는 기본 흐름을 다루었습니다.

다음 장부터는 머신러닝으로 확장합니다. 그러나 머신러닝도 좋은 데이터, 명확한 목표 변수, 적절한 평가 기준에서 출발합니다. 이번 프로젝트에서 익힌 원본 보존, 데이터 품질 점검, 완료 주문 기준, 병합 검증, 결과 해석 습관은 이후 모델링에서도 그대로 이어집니다.
