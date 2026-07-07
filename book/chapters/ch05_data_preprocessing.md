# 5장. 분석을 믿을 수 있게 만드는 데이터 전처리

데이터 분석은 데이터를 불러오는 순간 바로 시작되는 것처럼 보이지만, 실제 분석의 품질은 그 전에 결정되는 경우가 많습니다. 값이 비어 있거나, 같은 고객이 여러 번 기록되어 있거나, 날짜가 문자열로 저장되어 있거나, 숫자처럼 보이는 가격이 문자로 들어 있으면 분석 결과는 쉽게 왜곡됩니다.

데이터 전처리는 이런 문제를 찾아내고, 분석 목적에 맞게 데이터를 정리하는 과정입니다. 단순히 데이터를 “깨끗하게” 만드는 작업이 아니라, **분석 결과를 신뢰할 수 있도록 데이터의 상태를 확인하고 처리 기준을 남기는 일**에 가깝습니다.

이 장에서는 온라인 쇼핑몰의 고객·상품·주문 데이터를 예로 들어 결측치, 중복값, 데이터 타입, 날짜, 문자열 표기, 이상값, 파생 컬럼을 차례대로 살펴봅니다. 전처리된 데이터는 원본과 분리해 `data/processed` 폴더에 저장하고, 이후 EDA와 시각화에서 사용할 수 있는 형태로 만들어 둡니다.

<figure class="figure">
  <img src="../assets/images/ch05/ch05_preprocessing_flow.png" alt="데이터 전처리 전체 흐름도">
  <figcaption>그림 5-1. 데이터 전처리 전체 흐름도</figcaption>
</figure>

## 1. 왜 전처리가 필요한가

현실의 데이터는 처음부터 분석하기 좋은 형태로 주어지지 않습니다. 같은 도시명이 `Seoul`, ` seoul `, `SEOUL`처럼 다르게 기록될 수 있고, 날짜가 `2024-01-15`라는 문자열로 저장되어 있을 수도 있습니다. 숫자처럼 보이는 `10,000`도 실제로는 쉼표가 들어간 문자열일 수 있습니다.

이 상태에서 바로 집계하거나 그래프를 그리면 분석 결과가 틀어질 수 있습니다. 예를 들어 고객의 평균 나이를 계산하려는데 결측치가 많다면 평균값이 대표성을 갖기 어렵습니다. 주문 수량이 음수로 들어간 데이터가 있다면 매출 합계가 실제보다 작게 계산될 수 있습니다. 주문 상태가 `완료`, `complete`, `COMPLETED`처럼 섞여 있으면 같은 상태를 서로 다른 값으로 집계할 수도 있습니다.

전처리는 이런 문제를 분석 전에 확인하는 과정입니다. 중요한 것은 문제를 무조건 삭제하거나 자동으로 고치는 것이 아니라, **왜 그런 값이 생겼는지, 분석 목적에 어떤 영향을 주는지, 어떤 기준으로 처리할지 판단하는 것**입니다.

전처리에서 자주 만나는 문제는 다음과 같습니다.

| 문제 유형 | 예시 | 확인할 질문 |
| --- | --- | --- |
| 결측치 | 나이가 비어 있는 고객 | 비어 있는 이유가 무엇인가? 삭제해도 되는가? |
| 중복 | 같은 고객 ID가 여러 번 등장 | 자연스러운 중복인가, 데이터 오류인가? |
| 타입 오류 | 가격이 문자열로 저장됨 | 계산 가능한 숫자형으로 바꿀 수 있는가? |
| 날짜 오류 | 주문일이 문자열로 저장됨 | 월별·요일별 분석에 사용할 수 있는가? |
| 문자열 표기 차이 | `Seoul`, ` Seoul`, `SEOUL` | 같은 값을 하나의 표기로 통일해야 하는가? |
| 이상값 | 수량이 음수이거나 가격이 0원 | 실제 의미가 있는 값인가, 입력 오류인가? |
| 파생 컬럼 필요 | 수량과 단가만 있고 주문금액이 없음 | 분석에 필요한 새 컬럼을 만들 수 있는가? |

## 2. 원본 데이터와 전처리 데이터는 분리한다

전처리에서 가장 먼저 지켜야 할 원칙은 원본 데이터를 직접 덮어쓰지 않는 것입니다. 원본 데이터는 `data/raw`에 보관하고, 전처리 결과는 `data/processed`에 따로 저장합니다. 이렇게 해야 전처리 과정에서 실수가 생겨도 원본으로 돌아갈 수 있고, 전처리 전후의 차이를 비교할 수 있습니다.

이 책에서는 다음과 같은 구조를 사용합니다.

```text
data/
├─ raw/
│  ├─ customers.csv
│  ├─ products.csv
│  ├─ orders.csv
│  └─ order_items.csv
└─ processed/
   ├─ customers_clean.csv
   ├─ products_clean.csv
   ├─ orders_clean.csv
   └─ order_items_clean.csv
```

`data/raw`는 처음 받은 데이터의 보관 장소입니다. `data/processed`는 분석에 사용하기 위해 정리한 데이터의 저장 장소입니다.

원본과 전처리 데이터를 분리하면 다음과 같은 장점이 있습니다.

- 원본 데이터를 언제든 다시 확인할 수 있습니다.
- 전처리 기준을 바꾸어 다시 처리할 수 있습니다.
- 전처리 전후 데이터 크기와 결측치 변화를 비교할 수 있습니다.
- 다른 사람이 같은 전처리 과정을 재현하기 쉽습니다.
- 보고서에서 데이터 처리 기준을 명확히 설명할 수 있습니다.

<figure class="figure">
  <img src="../assets/images/ch05/ch05_raw_processed_structure.png" alt="raw 데이터와 processed 데이터 분리 구조">
  <figcaption>그림 5-2. raw 데이터와 processed 데이터 분리 구조</figcaption>
</figure>

## 3. 전처리에서 자주 하는 판단

전처리는 기계적으로 코드를 실행하는 작업이 아닙니다. 같은 결측치라도 컬럼의 의미와 분석 목적에 따라 처리 방식이 달라집니다.

### 결측치: 비어 있는 값은 모두 같은 의미가 아니다

결측치는 값이 비어 있는 상태를 의미합니다. 하지만 결측치가 생긴 이유는 다양합니다. 입력을 빠뜨렸을 수도 있고, 해당 값이 실제로 존재하지 않을 수도 있고, 수집 과정에서 누락되었을 수도 있습니다.

결측치 처리 방법은 크게 세 가지로 나눌 수 있습니다.

| 방법 | 설명 | 예시 |
| --- | --- | --- |
| 삭제 | 결측치가 있는 행 또는 컬럼을 제거 | ID가 없는 주문 행 제외 |
| 대체 | 평균, 중앙값, 최빈값 등으로 채움 | 나이 결측치를 중앙값으로 대체 |
| 별도 범주 | 알 수 없음으로 표시 | 도시 결측치를 `Unknown`으로 처리 |

결측치가 있다고 해서 무조건 삭제하면 안 됩니다. 삭제하면 데이터 수가 줄어들고, 특정 그룹이 분석에서 빠질 수 있습니다. 반대로 무조건 평균으로 채우는 것도 위험합니다. 결측치가 분석 결과에 어떤 영향을 줄지 먼저 생각해야 합니다.

### 중복: 반복된 값이 항상 오류는 아니다

중복 데이터도 맥락을 보고 판단해야 합니다. `customers` 데이터에서 `customer_id`가 중복되면 고객 정보가 잘못 들어갔을 가능성이 큽니다. 하지만 `order_items` 데이터에서 같은 `order_id`가 여러 번 나오는 것은 정상일 수 있습니다. 한 주문 안에 여러 상품이 들어갈 수 있기 때문입니다.

| 구분 | 설명 | 예시 |
| --- | --- | --- |
| 전체 행 중복 | 모든 컬럼 값이 같은 행이 반복됨 | 같은 고객 행이 두 번 저장됨 |
| 기준 ID 중복 | 고유해야 할 ID가 중복됨 | `customer_id` 중복 |
| 자연스러운 반복 | 관계상 같은 값이 여러 번 나올 수 있음 | `order_items`의 `order_id` 반복 |

따라서 중복을 확인할 때는 “어떤 컬럼이 고유해야 하는가”를 먼저 생각해야 합니다.

### 타입 변환: 보이는 것과 저장된 것은 다를 수 있다

데이터 화면에서 숫자처럼 보인다고 해서 실제로 숫자형인 것은 아닙니다. 날짜처럼 보여도 문자열일 수 있습니다. pandas에서 데이터 타입이 맞지 않으면 합계, 평균, 월별 집계 같은 분석이 제대로 동작하지 않습니다.

| 문제 상황 | 필요한 처리 |
| --- | --- |
| `"10,000"`처럼 저장된 가격 | 쉼표 제거 후 숫자형 변환 |
| `"2024-01-15"`처럼 저장된 날짜 | 날짜형 변환 |
| `"  Seoul "`처럼 앞뒤 공백이 있는 문자열 | 공백 제거 |
| `"seoul"`, `"SEOUL"`처럼 대소문자가 섞인 값 | 표기 통일 |
| `"완료"`, `"completed"`처럼 언어가 섞인 상태값 | 상태값 매핑 |

### 이상값: 삭제보다 확인이 먼저다

이상값은 일반적인 범위를 벗어난 값입니다. 하지만 이상값이 항상 오류는 아닙니다. 0원 상품은 이벤트 상품일 수 있고, 음수 수량은 환불이나 취소를 의미할 수도 있습니다. 따라서 이상값은 먼저 확인하고, 처리 기준을 기록한 뒤 다루어야 합니다.

예를 들어 다음 값들은 확인이 필요합니다.

- 나이가 150세인 고객
- 상품 가격이 0원인 상품
- 주문 수량이 음수인 데이터
- 단가가 비정상적으로 큰 주문
- 주문일이 분석 기간보다 훨씬 오래된 데이터

<figure class="figure">
  <img src="../assets/images/ch05/ch05_missing_duplicate_outlier.png" alt="결측치·중복·이상값 전처리 개념도">
  <figcaption>그림 5-3. 결측치·중복·이상값 전처리 개념도</figcaption>
</figure>

## 4. 온라인 쇼핑몰 데이터 전처리 흐름

이번 장에서는 온라인 쇼핑몰 데이터를 분석하기 전 단계라고 생각하고 전처리를 진행합니다. 원본 CSV 파일을 불러온 뒤 결측치, 중복, 타입, 날짜, 문자열, 이상값을 차례대로 확인하고, 정리된 데이터를 `data/processed` 폴더에 저장합니다.

전처리 과정에서 던질 질문은 다음과 같습니다.

| 전처리 질문 | 사용할 데이터 | pandas 기능 |
| --- | --- | --- |
| 결측치가 있는 컬럼은 무엇인가? | 전체 데이터 | `isna().sum()` |
| 결측치 비율은 얼마나 되는가? | 전체 데이터 | `isna().mean()` |
| 중복 행이 있는가? | 전체 데이터 | `duplicated()` |
| 고객 ID는 고유한가? | `customers` | `duplicated()` |
| 주문일은 날짜형인가? | `orders` | `pd.to_datetime()` |
| 가격과 수량은 숫자형인가? | `products`, `order_items` | `pd.to_numeric()` |
| 지역명과 상태값 표기가 일관적인가? | `customers`, `orders` | `str.strip()`, `replace()` |
| 주문 상세 금액을 계산할 수 있는가? | `order_items` | 파생 컬럼 생성 |
| 전처리 결과를 저장했는가? | 전체 데이터 | `to_csv()` |

<figure class="figure">
  <img src="../assets/images/ch05/ch05_preprocessing_practice_flow.png" alt="데이터 전처리 실습 흐름도">
  <figcaption>그림 5-4. 데이터 전처리 실습 흐름도</figcaption>
</figure>

## 5. 데이터를 불러오고 작업 공간을 준비한다

전체 코드는 `notebooks/ch05_data_preprocessing.ipynb`에서 따라갈 수 있습니다. 본문에서는 흐름을 이해하는 데 필요한 핵심 코드만 다룹니다.

먼저 필요한 패키지를 불러옵니다.

```python
from pathlib import Path
import pandas as pd
import numpy as np
```

데이터 경로를 설정합니다. VS Code에서 프로젝트 루트 폴더를 기준으로 실행한다면 다음 경로를 사용할 수 있습니다.

```python
raw_dir = Path("data/raw")
processed_dir = Path("data/processed")
report_dir = Path("reports")

processed_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(exist_ok=True)
```

Notebook을 `notebooks` 폴더 안에서 실행하는 경우에는 상대 경로가 달라질 수 있습니다. 이때는 다음처럼 한 단계 위 폴더를 기준으로 경로를 조정합니다.

```python
raw_dir = Path("../data/raw")
processed_dir = Path("../data/processed")
report_dir = Path("../reports")

processed_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(exist_ok=True)
```

현재 코드가 어느 위치에서 실행되는지 헷갈린다면 먼저 작업 폴더를 확인합니다.

```python
Path.cwd()
```

원본 데이터를 불러옵니다.

```python
customers = pd.read_csv(raw_dir / "customers.csv")
products = pd.read_csv(raw_dir / "products.csv")
orders = pd.read_csv(raw_dir / "orders.csv")
order_items = pd.read_csv(raw_dir / "order_items.csv")
```

전처리 전 데이터 크기를 기록해 두면 나중에 전처리 결과를 비교할 수 있습니다.

```python
raw_shapes = pd.DataFrame({
    "dataset": ["customers", "products", "orders", "order_items"],
    "rows": [customers.shape[0], products.shape[0], orders.shape[0], order_items.shape[0]],
    "columns": [customers.shape[1], products.shape[1], orders.shape[1], order_items.shape[1]]
})

raw_shapes
```

전처리 과정에서는 원본 DataFrame을 직접 수정하지 않고 복사본을 사용합니다.

```python
customers_clean = customers.copy()
products_clean = products.copy()
orders_clean = orders.copy()
order_items_clean = order_items.copy()
```

## 6. 결측치를 확인하고 처리한다

결측치를 처리하기 전에 먼저 어디에 얼마나 비어 있는 값이 있는지 확인합니다.

```python
datasets = {
    "customers": customers_clean,
    "products": products_clean,
    "orders": orders_clean,
    "order_items": order_items_clean
}

for name, df in datasets.items():
    print(f"\n[{name}]")
    print(df.isna().sum())
```

개수만 보면 데이터 크기에 따른 차이를 놓칠 수 있으므로 비율도 함께 확인합니다.

```python
for name, df in datasets.items():
    print(f"\n[{name}] 결측치 비율(%)")
    print((df.isna().mean() * 100).round(2))
```

반복해서 사용할 수 있도록 결측치 요약 함수를 만들어 두면 편리합니다.

```python
def missing_summary(df):
    summary = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_ratio": (df.isna().mean() * 100).round(2)
    })
    return summary.sort_values("missing_count", ascending=False)

missing_summary(customers_clean)
```

고객 나이처럼 숫자형 컬럼에 결측치가 있다면 중앙값으로 대체할 수 있습니다.

```python
customers_clean["age"].isna().sum()
```

```python
age_median = customers_clean["age"].median()
customers_clean["age"] = customers_clean["age"].fillna(age_median)
```

나이처럼 극단값의 영향을 받을 수 있는 컬럼은 평균보다 중앙값이 더 안정적일 수 있습니다. 다만 중앙값 대체 역시 실제 나이를 알 수 없는 고객에게 대표값을 넣는 방식이므로, 연령대별 분석에서는 이 처리 기준을 함께 설명해야 합니다.

도시처럼 범주형 컬럼의 결측치는 `Unknown`으로 남겨 분석에서 구분할 수 있습니다.

```python
if "city" in customers_clean.columns:
    customers_clean["city"] = customers_clean["city"].fillna("Unknown")
```

## 7. 중복을 확인한다

전체 행이 완전히 같은 중복부터 확인합니다.

```python
for name, df in datasets.items():
    print(name, df.duplicated().sum())
```

중복 행을 제거할 수는 있지만, 제거하기 전에는 어떤 행이 중복인지 먼저 보는 것이 좋습니다.

```python
customers[customers.duplicated()]
```

확인 후 완전 중복을 제거하려면 다음처럼 작성할 수 있습니다.

```python
customers_clean = customers_clean.drop_duplicates()
products_clean = products_clean.drop_duplicates()
orders_clean = orders_clean.drop_duplicates()
order_items_clean = order_items_clean.drop_duplicates()
```

고유해야 하는 ID 컬럼은 별도로 확인합니다.

```python
customers_clean["customer_id"].duplicated().sum()
```

```python
products_clean["product_id"].duplicated().sum()
```

```python
orders_clean["order_id"].duplicated().sum()
```

`order_items`에서는 `order_id`가 중복될 수 있습니다. 한 주문에 여러 상품이 포함될 수 있기 때문입니다. 대신 `order_item_id`처럼 주문 상세를 식별하는 컬럼이 있다면 그 컬럼의 중복 여부를 확인합니다.

```python
if "order_item_id" in order_items_clean.columns:
    print(order_items_clean["order_item_id"].duplicated().sum())
```

## 8. 문자열 표기를 정리한다

문자열 데이터에는 앞뒤 공백이 숨어 있을 수 있습니다. `"Seoul"`과 `" Seoul "`은 눈으로는 비슷해 보이지만 pandas에서는 서로 다른 값입니다.

문자열 컬럼의 앞뒤 공백을 제거하는 함수를 만들어 둡니다.

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

`where()`를 함께 사용하면 결측치는 그대로 유지하면서 실제 문자열 값에 대해서만 공백을 제거할 수 있습니다. 단순히 `astype(str)`만 사용하면 결측치가 `"nan"`이라는 문자열로 바뀔 수 있으므로 주의해야 합니다.

각 데이터셋에 적용합니다.

```python
customers_clean = strip_string_columns(customers_clean)
products_clean = strip_string_columns(products_clean)
orders_clean = strip_string_columns(orders_clean)
order_items_clean = strip_string_columns(order_items_clean)
```

상태값이나 도시명처럼 범주형 값은 실제 값의 분포를 먼저 확인합니다.

```python
customers_clean["city"].value_counts()
```

```python
orders_clean["order_status"].value_counts()
```

주문 상태값이 여러 표기로 섞여 있다면 하나의 기준으로 통일합니다.

```python
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
```

처리 후 다시 분포를 확인합니다.

```python
orders_clean["order_status"].value_counts()
```

## 9. 날짜와 숫자형 컬럼을 변환한다

날짜처럼 보이는 값도 실제로는 문자열일 수 있습니다. 월별 주문 분석이나 요일별 분석을 하려면 날짜형으로 변환해야 합니다.

```python
orders_clean["order_date"] = pd.to_datetime(
    orders_clean["order_date"],
    errors="coerce"
)
```

가입일 컬럼도 같은 방식으로 변환할 수 있습니다.

```python
if "signup_date" in customers_clean.columns:
    customers_clean["signup_date"] = pd.to_datetime(
        customers_clean["signup_date"],
        errors="coerce"
    )
```

`errors="coerce"`는 변환할 수 없는 값을 `NaT`로 바꿉니다. 그래서 변환 후 실패 건수를 반드시 확인해야 합니다.

```python
print("order_date 변환 실패:", orders_clean["order_date"].isna().sum())

if "signup_date" in customers_clean.columns:
    print("signup_date 변환 실패:", customers_clean["signup_date"].isna().sum())
```

날짜 범위도 함께 살펴봅니다.

```python
print("주문 시작일:", orders_clean["order_date"].min())
print("주문 종료일:", orders_clean["order_date"].max())
```

날짜형으로 변환하면 주문 월과 요일 같은 파생 컬럼을 만들 수 있습니다.

```python
orders_clean["order_month"] = orders_clean["order_date"].dt.to_period("M").astype(str)
orders_clean["order_dayofweek"] = orders_clean["order_date"].dt.day_name()

orders_clean[["order_date", "order_month", "order_dayofweek"]].head()
```

가격, 수량, 단가 컬럼은 숫자형인지 확인합니다.

```python
products_clean.dtypes
```

```python
order_items_clean.dtypes
```

쉼표가 들어간 문자열 숫자를 처리할 수 있도록 함수를 만듭니다.

```python
def to_number(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )
```

상품 가격, 주문 수량, 단가를 숫자형으로 변환합니다.

```python
if "price" in products_clean.columns:
    products_clean["price"] = to_number(products_clean["price"])

if "quantity" in order_items_clean.columns:
    order_items_clean["quantity"] = to_number(order_items_clean["quantity"])

if "unit_price" in order_items_clean.columns:
    order_items_clean["unit_price"] = to_number(order_items_clean["unit_price"])
```

변환 후에는 실패값이 생겼는지 확인합니다.

```python
print(products_clean["price"].isna().sum())
print(order_items_clean["quantity"].isna().sum())
print(order_items_clean["unit_price"].isna().sum())
```

## 10. 이상값과 파생 컬럼을 다룬다

숫자형 컬럼은 기본 통계를 통해 이상값 후보를 확인할 수 있습니다.

```python
products_clean["price"].describe()
```

```python
order_items_clean[["quantity", "unit_price"]].describe()
```

가격이나 수량이 0 이하인 데이터가 있는지 확인합니다.

```python
products_clean[products_clean["price"] <= 0]
```

```python
order_items_clean[order_items_clean["quantity"] <= 0]
```

```python
order_items_clean[order_items_clean["unit_price"] <= 0]
```

실습 데이터에서 가격이나 수량이 0 이하인 데이터는 정상 주문 분석에서 제외한다고 가정해 보겠습니다.

```python
products_clean = products_clean[products_clean["price"] > 0]
order_items_clean = order_items_clean[order_items_clean["quantity"] > 0]
order_items_clean = order_items_clean[order_items_clean["unit_price"] > 0]
```

이 코드는 단순한 예시입니다. 실제 업무에서는 0원 상품이 이벤트 상품인지, 음수 수량이 반품이나 취소를 의미하는지 먼저 확인해야 합니다. 처리 기준은 보고서에 남겨야 합니다.

```text
전처리 기준:
- price가 0 이하인 상품은 분석 대상에서 제외
- quantity가 0 이하인 주문 상세는 분석 대상에서 제외
- unit_price가 0 이하인 주문 상세는 분석 대상에서 제외
```

전처리된 수량과 단가를 사용하면 주문 상세 금액을 계산할 수 있습니다.

```python
order_items_clean["line_total"] = (
    order_items_clean["quantity"] * order_items_clean["unit_price"]
)
```

```python
order_items_clean[["quantity", "unit_price", "line_total"]].head()
```

전체 매출 합계도 확인할 수 있습니다.

```python
order_items_clean["line_total"].sum()
```

## 11. 파일 간 관계를 다시 확인한다

전처리 과정에서 일부 행을 삭제하면 파일 간 관계가 깨질 수 있습니다. 예를 들어 `products`에서 일부 상품을 제외했는데 `order_items`에는 그 상품 ID가 남아 있을 수 있습니다. 그래서 전처리 후에는 키 관계를 다시 확인해야 합니다.

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

키 관계 확인은 전처리의 마지막 안전장치입니다. 한 파일만 깨끗하게 보인다고 해서 전체 데이터 구조가 안전한 것은 아닙니다.

## 12. 전처리 전후를 비교하고 저장한다

전처리를 마친 뒤에는 원본 데이터와 전처리 데이터의 크기를 비교합니다.

```python
processed_shapes = pd.DataFrame({
    "dataset": ["customers", "products", "orders", "order_items"],
    "rows": [
        customers_clean.shape[0],
        products_clean.shape[0],
        orders_clean.shape[0],
        order_items_clean.shape[0]
    ],
    "columns": [
        customers_clean.shape[1],
        products_clean.shape[1],
        orders_clean.shape[1],
        order_items_clean.shape[1]
    ]
})

comparison = raw_shapes.merge(
    processed_shapes,
    on="dataset",
    suffixes=("_raw", "_processed")
)

comparison
```

행 수가 줄었다면 어떤 기준으로 줄었는지 설명할 수 있어야 합니다. 열 수가 늘었다면 어떤 파생 컬럼이 추가되었는지도 함께 기록합니다.

전처리된 데이터는 `data/processed` 폴더에 저장합니다.

```python
customers_clean.to_csv(processed_dir / "customers_clean.csv", index=False)
products_clean.to_csv(processed_dir / "products_clean.csv", index=False)
orders_clean.to_csv(processed_dir / "orders_clean.csv", index=False)
order_items_clean.to_csv(processed_dir / "order_items_clean.csv", index=False)
```

저장된 파일을 확인합니다.

```python
list(processed_dir.glob("*_clean.csv"))
```

전처리 요약을 Markdown 파일로 남겨 두면 이후 보고서 작성이 쉬워집니다.

```python
summary_text = f"""
# Chapter 5 데이터 전처리 요약

## 전처리 결과 파일

- customers_clean.csv
- products_clean.csv
- orders_clean.csv
- order_items_clean.csv

## 전처리 전후 데이터 크기

{comparison.to_markdown(index=False)}

## 주요 처리 내용

- 문자열 컬럼 앞뒤 공백 제거
- 주문 상태값 표기 통일
- 날짜 컬럼 변환
- 숫자형 컬럼 변환
- 0 이하 가격, 수량, 단가 확인 및 처리
- line_total 파생 컬럼 생성
- 파일 간 키 관계 재확인

## 다음 단계

전처리된 데이터를 사용해 EDA와 시각화를 수행합니다.
"""

report_path = report_dir / "ch05_preprocessing_summary.md"
report_path.write_text(summary_text, encoding="utf-8")
```

## 13. 전처리 과정을 함수로 정리한다

전처리 코드를 한 번만 실행하고 끝내면 재사용하기 어렵습니다. 같은 데이터를 다시 받거나 처리 기준을 조금 바꿔야 할 때는 함수로 정리된 코드가 훨씬 유용합니다.

고객 데이터 전처리 함수는 다음처럼 만들 수 있습니다.

```python
def preprocess_customers(df):
    df = df.copy()
    
    df = strip_string_columns(df)
    
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        df["age"] = df["age"].fillna(df["age"].median())
    
    if "city" in df.columns:
        df["city"] = df["city"].fillna("Unknown")
    
    if "signup_date" in df.columns:
        df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    
    df = df.drop_duplicates()
    
    return df
```

상품 데이터 전처리 함수입니다.

```python
def preprocess_products(df):
    df = df.copy()
    df = strip_string_columns(df)
    
    if "price" in df.columns:
        df["price"] = to_number(df["price"])
        df = df[df["price"] > 0]
    
    df = df.drop_duplicates()
    
    return df
```

주문 데이터 전처리 함수입니다.

```python
def preprocess_orders(df):
    df = df.copy()
    df = strip_string_columns(df)
    
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    
    if "order_status" in df.columns:
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
        df["order_status"] = df["order_status"].replace(status_map)
    
    df = df.drop_duplicates()
    
    return df
```

주문 상세 데이터 전처리 함수입니다.

```python
def preprocess_order_items(df):
    df = df.copy()
    df = strip_string_columns(df)
    
    if "quantity" in df.columns:
        df["quantity"] = to_number(df["quantity"])
    
    if "unit_price" in df.columns:
        df["unit_price"] = to_number(df["unit_price"])
    
    if "quantity" in df.columns:
        df = df[df["quantity"] > 0]
    
    if "unit_price" in df.columns:
        df = df[df["unit_price"] > 0]
    
    if {"quantity", "unit_price"}.issubset(df.columns):
        df["line_total"] = df["quantity"] * df["unit_price"]
    
    df = df.drop_duplicates()
    
    return df
```

함수를 적용하면 전처리 흐름이 더 명확해집니다.

```python
customers_clean = preprocess_customers(customers)
products_clean = preprocess_products(products)
orders_clean = preprocess_orders(orders)
order_items_clean = preprocess_order_items(order_items)
```

함수로 정리할 때도 실제 컬럼이 항상 존재한다고 가정하지 않는 편이 안전합니다. 위 코드처럼 컬럼 존재 여부를 확인하면 데이터 구조가 조금 달라져도 오류를 줄일 수 있습니다.

<figure class="figure">
  <img src="../assets/images/ch05/ch05_preprocessing_function_save_flow.png" alt="전처리 함수화와 저장 흐름도">
  <figcaption>그림 5-5. 전처리 함수화와 저장 흐름도</figcaption>
</figure>

## 14. LLM과 함께 전처리 코드를 검토한다

LLM은 전처리 코드 초안을 만들거나 오류 원인을 정리하는 데 도움이 됩니다. 하지만 전처리는 분석 결과에 직접 영향을 주기 때문에 LLM이 제안한 코드를 그대로 적용하면 위험할 수 있습니다. 최종 판단은 항상 사람이 해야 합니다.

LLM에게 질문할 때는 실제 고객명, 이메일, 주문 내역을 그대로 넣지 않습니다. 컬럼명, 데이터 타입, 결측치 개수, 중복 여부, 처리 목적처럼 구조화된 정보만 제공하는 것이 안전합니다.

결측치 처리 방향을 물어볼 때는 다음처럼 질문할 수 있습니다.

```text
온라인 쇼핑몰 customers 데이터에 다음과 같은 결측치가 있습니다.

컬럼별 결측치:
- customer_id: 0
- name: 0
- gender: 0
- age: 3
- city: 2
- signup_date: 0

분석 목적:
- 고객 연령대별 구매 패턴 분석
- 지역별 고객 분포 확인

질문:
1. age 결측치는 어떻게 처리하는 것이 적절한가요?
2. city 결측치는 어떻게 처리하는 것이 적절한가요?
3. 삭제, 평균/중앙값 대체, Unknown 처리의 장단점을 비교해 주세요.
4. 실제 값을 임의로 만들어내지 말고, 처리 기준 중심으로 설명해 주세요.
```

LLM이 만든 전처리 코드는 다음 기준으로 검토합니다.

| 검토 기준 | 확인할 질문 |
| --- | --- |
| 원본 보존 | 원본 DataFrame을 직접 수정하지 않았는가? |
| 결측치 처리 | 컬럼 의미에 맞는 방식인가? |
| 타입 변환 | 변환 실패 건수를 확인하는가? |
| 중복 제거 | 중복 기준이 충분히 명확한가? |
| 이상값 처리 | 삭제 전에 의미를 확인했는가? |
| 파생 컬럼 | 계산 전에 필요한 컬럼이 숫자형인가? |
| 보안 | 실제 개인정보나 API Key를 입력하지 않았는가? |

전처리 코드 검토를 요청할 때는 다음 프롬프트를 사용할 수 있습니다.

```text
다음 전처리 코드가 안전한지 검토해 주세요.

customers["age"] = customers["age"].fillna(customers["age"].mean())
customers = customers.drop_duplicates()
orders["order_date"] = pd.to_datetime(orders["order_date"])
order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]

검토 기준:
- 원본 데이터를 직접 수정하는 문제가 있는지
- 결측치 처리 방식이 적절한지
- 날짜 변환 실패를 확인하는지
- 중복 제거 기준이 충분한지
- line_total 계산 전에 숫자형 변환이 필요한지
- 더 안전한 코드로 어떻게 수정할 수 있는지
```

LLM은 좋은 검토 파트너가 될 수 있지만, 데이터의 의미를 아는 사람의 판단을 대체하지는 못합니다. 특히 결측치 대체, 중복 제거, 이상값 삭제는 분석 결과를 바꿀 수 있으므로 처리 기준을 반드시 남겨야 합니다.

## 15. 전처리 결과를 어떻게 읽을 것인가

전처리 후에는 “코드가 실행되었다”에서 멈추면 안 됩니다. 어떤 문제가 발견되었고, 어떤 기준으로 처리했으며, 그 결과 데이터가 어떻게 바뀌었는지를 설명할 수 있어야 합니다.

예를 들어 결측치 처리는 다음처럼 해석할 수 있습니다.

```text
age 컬럼의 결측치를 중앙값으로 대체했습니다.
city 컬럼의 결측치는 Unknown으로 처리했습니다.
```

이 문장만으로는 충분하지 않습니다. 나이 결측치를 중앙값으로 대체하면 전체 고객 수는 유지할 수 있지만, 실제 나이를 알 수 없는 고객에게 대표값을 부여한 것이므로 연령대별 분석에서는 주의가 필요하다는 점까지 함께 설명해야 합니다.

날짜 변환 결과도 마찬가지입니다.

```text
order_date 컬럼을 날짜형으로 변환했으며, 변환 실패 건수는 0건입니다.
따라서 월별 주문 분석에 사용할 수 있는 상태입니다.
```

이상값을 제외했다면 기준을 더 명확히 남겨야 합니다.

```text
quantity와 unit_price가 0 이하인 데이터는 정상 주문 상세로 보기 어렵기 때문에 분석 대상에서 제외했습니다.
다만 실제 업무에서는 원본 시스템이나 담당자 확인이 필요합니다.
```

전처리 결과는 최종 분석 결과가 아닙니다. 하지만 이후 EDA, 시각화, 머신러닝의 신뢰도를 결정하는 중요한 중간 산출물입니다.

## 16. 다음 장으로 이어지는 흐름

전처리된 데이터가 준비되면 이제 데이터를 더 깊이 들여다볼 수 있습니다. 다음 장에서는 전처리된 데이터를 바탕으로 탐색적 데이터 분석, 즉 EDA를 수행합니다. EDA에서는 단순히 그래프를 그리는 것보다 “어떤 질문을 던질 것인가”가 중요합니다.

전처리는 분석 가능한 데이터를 만드는 과정이고, EDA는 그 데이터에 질문을 던지는 과정입니다. 결측치, 중복, 타입, 이상값을 정리해 두면 다음 단계에서 고객 행동, 주문 패턴, 상품 매출, 취소율 같은 질문을 훨씬 안정적으로 탐색할 수 있습니다.
