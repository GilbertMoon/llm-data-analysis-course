# 7장. 그래프로 데이터의 이야기를 보여주기

표는 정확한 값을 전달하는 데 유용합니다. 하지만 숫자가 많아지면 변화와 차이를 빠르게 파악하기 어렵습니다. 카테고리별 금액을 표로 보면 값을 하나씩 비교해야 하지만, 막대그래프로 표현하면 어떤 카테고리가 큰지 한눈에 확인할 수 있습니다. 월별 금액도 선 그래프로 그리면 시간에 따른 증가와 감소가 더 분명하게 드러납니다.

데이터 시각화는 분석 결과를 예쁘게 꾸미는 작업이 아닙니다. **분석 질문에 맞는 형태로 데이터를 표현해 패턴, 차이, 추세, 분포, 관계를 이해하고 전달하는 과정**입니다. 좋은 그래프는 무엇을 보여 주는지 분명하고, 무엇까지는 설명할 수 없는지도 함께 드러냅니다.

이 장에서는 5장에서 전처리한 온라인 쇼핑몰 데이터를 바탕으로 다음 내용을 시각화합니다.

- 완료 주문 기준 카테고리별 금액
- 완료 주문 기준 월별 금액
- 상품 가격 분포
- 상품 가격과 완료 주문 판매 수량의 관계
- 완료 주문 구매 금액 상위 고객
- 전체 주문 상태별 주문 수

여기서 사용하는 `line_total`은 수량과 단가를 곱한 **주문 상세 금액**입니다. 이 값을 모두 합한 결과를 곧바로 회계상의 순매출이라고 부르면 안 됩니다. 취소·환불 주문, 할인, 배송비, 세금, 부분 환불 정보가 별도로 반영되지 않을 수 있기 때문입니다. 이 장에서는 5장과 같은 기준을 유지해 `order_status == "completed"`인 주문만 완료 주문 기준 금액에 포함합니다.

## 이 장에서 생각해 볼 질문

- 지금 확인하려는 것은 비교, 추세, 분포, 관계 중 무엇인가?
- 분석 질문에 가장 잘 맞는 그래프는 무엇인가?
- 그래프에 사용한 데이터의 포함·제외 기준은 무엇인가?
- x축과 y축은 무엇을 의미하며 단위는 무엇인가?
- 범주와 시간 순서가 올바르게 정렬되어 있는가?
- 그래프가 관찰된 패턴만 보여 주는가, 원인까지 증명하는가?
- 축 범위나 생략된 데이터가 결과를 과장하지 않는가?
- 개인정보 또는 식별 가능한 값이 노출되지 않았는가?
- LLM이 작성한 해석이 실제 집계 결과와 일치하는가?

<figure class="figure">
  <img src="../assets/images/ch07/ch07_visualization_overview_flow.png" alt="데이터 시각화 전체 흐름도">
  <figcaption>그림 7-1. 데이터 시각화 전체 흐름도</figcaption>
</figure>

## 1. 시각화는 분석 질문에서 시작된다

좋은 시각화는 그래프 종류를 많이 아는 데서 시작하지 않습니다. 먼저 어떤 질문에 답하려는지 정해야 합니다.

“카테고리별 완료 주문 금액은 어떻게 다른가?”는 범주별 크기를 비교하는 질문이므로 막대그래프가 적합합니다. “월별 완료 주문 금액은 어떻게 변하는가?”는 시간 흐름을 확인하는 질문이므로 선 그래프가 적합합니다. “상품 가격은 어느 구간에 몰려 있는가?”는 분포를 확인하는 질문이므로 히스토그램이 적합합니다.

| 분석 목적 | 적합한 그래프 | 예시 질문 |
| --- | --- | --- |
| 범주별 크기 비교 | 막대그래프 | 카테고리별 완료 주문 금액은 어떻게 다른가? |
| 시간 흐름 확인 | 선 그래프 | 월별 완료 주문 금액은 어떻게 변하는가? |
| 값의 분포 확인 | 히스토그램 | 상품 가격은 어떤 구간에 몰려 있는가? |
| 두 숫자형 변수의 관계 확인 | 산점도 | 가격과 완료 주문 판매 수량은 관계가 있는가? |
| 상위 항목 비교 | 가로 막대그래프 | 구매 금액 상위 고객군은 어떻게 구성되는가? |
| 비율 또는 빈도 비교 | 막대그래프 | 주문 상태별 주문 수는 어떻게 다른가? |

파이 차트는 전체에서 각 항목이 차지하는 비율을 보여 줄 수 있습니다. 그러나 항목이 많거나 값 차이가 작으면 비교하기 어렵습니다. 실무에서는 비율도 막대그래프로 표현하는 경우가 많습니다.

<figure class="figure">
  <img src="../assets/images/ch07/ch07_chart_selection_guide.png" alt="분석 질문별 그래프 선택 가이드">
  <figcaption>그림 7-2. 분석 질문별 그래프 선택 가이드</figcaption>
</figure>

## 2. matplotlib 그래프의 기본 구조

matplotlib은 Python에서 널리 사용하는 시각화 라이브러리입니다. 이 장에서는 `Figure`와 `Axes` 객체를 명시적으로 사용하는 방식을 중심으로 설명합니다.

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 5))

ax.bar(x_data, y_data)
ax.set_title("그래프 제목")
ax.set_xlabel("x축 이름")
ax.set_ylabel("y축 이름")
ax.tick_params(axis="x", rotation=45)

fig.tight_layout()
fig.savefig("graph.png", dpi=150, bbox_inches="tight")
plt.show()
```

각 요소의 의미는 다음과 같습니다.

| 요소 | 의미 |
| --- | --- |
| `figsize=(10, 5)` | 그래프의 가로·세로 크기입니다. 단위는 인치입니다. |
| `fig`, `ax` | 전체 그림과 실제 그래프 영역을 나타냅니다. |
| `set_title()` | 그래프 제목을 설정합니다. |
| `set_xlabel()`, `set_ylabel()` | 축 이름과 의미를 표시합니다. |
| `tight_layout()` | 제목과 레이블이 잘리는 문제를 줄입니다. |
| `dpi=150` | 저장 이미지의 해상도를 설정합니다. |
| `bbox_inches="tight"` | 저장할 때 바깥쪽 레이블이 잘리는 문제를 줄입니다. |

그래프를 파일로 저장할 때는 일반적으로 `savefig()`를 `show()`보다 먼저 실행합니다. 실행 환경에 따라 `show()` 이후 그래프 상태가 초기화될 수 있으므로, 먼저 저장한 뒤 화면에 표시하는 편이 안전합니다.

스크립트에서 그래프를 여러 개 반복 생성한다면 `plt.close(fig)`로 사용이 끝난 Figure를 닫아 메모리 사용량을 줄일 수 있습니다. Jupyter Notebook에서 몇 개의 그래프만 만드는 실습에서는 반드시 필요한 것은 아닙니다.

<figure class="figure">
  <img src="../assets/images/ch07/ch07_matplotlib_basic_structure.png" alt="matplotlib 기본 그래프 구조">
  <figcaption>그림 7-3. matplotlib 기본 그래프 구조</figcaption>
</figure>

## 3. 한글 폰트와 숫자 표시 설정

matplotlib에서 한글 제목이나 축 이름을 사용하면 실행 환경에 따라 글자가 깨질 수 있습니다. 설치된 폰트 중 사용할 수 있는 한글 폰트를 선택합니다.

```python
from matplotlib import font_manager
import matplotlib.pyplot as plt

installed_fonts = {
    font.name
    for font in font_manager.fontManager.ttflist
}

font_candidates = [
    "Malgun Gothic",       # Windows
    "AppleGothic",         # macOS
    "NanumGothic",         # Linux에서 별도 설치 가능
    "Noto Sans CJK KR",
]

selected_font = next(
    (
        font_name
        for font_name in font_candidates
        if font_name in installed_fonts
    ),
    None,
)

if selected_font is not None:
    plt.rcParams["font.family"] = selected_font
    print("사용 폰트:", selected_font)
else:
    print(
        "사용 가능한 한글 폰트를 찾지 못했습니다. "
        "한글 폰트를 설치하거나 영문 레이블을 사용하세요."
    )

plt.rcParams["axes.unicode_minus"] = False
```

`axes.unicode_minus`를 `False`로 설정하면 음수 기호가 네모 모양으로 보이는 문제를 줄일 수 있습니다.

금액 축에는 천 단위 구분 기호를 표시하면 읽기 쉽습니다.

```python
from matplotlib.ticker import FuncFormatter

money_formatter = FuncFormatter(
    lambda value, position: f"{value:,.0f}"
)
```

이후 `ax.yaxis.set_major_formatter(money_formatter)`처럼 적용할 수 있습니다.

## 4. 그래프 종류별로 읽는 법

### 막대그래프

막대그래프는 범주별 크기를 비교할 때 사용합니다. 카테고리별 금액, 주문 상태별 주문 수, 고객별 구매 금액 상위 목록 등에 적합합니다.

막대그래프의 길이는 값의 크기를 나타내므로 특별한 이유가 없다면 값 축을 0에서 시작하는 것이 좋습니다. 항목 이름이 길거나 항목 수가 많다면 가로 막대그래프가 더 읽기 좋을 수 있습니다.

### 선 그래프

선 그래프는 시간에 따른 변화를 확인할 때 사용합니다. 월별 금액이나 월별 주문 수처럼 순서가 중요한 데이터에 적합합니다.

선 그래프를 만들기 전에 날짜가 올바른 타입인지, 누락된 기간이 있는지, 월이 시간 순서대로 정렬되어 있는지 확인해야 합니다. 데이터가 없는 월을 0으로 볼 것인지 결측으로 볼 것인지도 분석 목적에 따라 판단해야 합니다.

### 히스토그램

히스토그램은 숫자형 데이터의 분포를 확인할 때 사용합니다. 상품 가격이나 고객 나이가 어느 구간에 많이 몰려 있는지 살펴볼 수 있습니다.

`bins`는 값을 나누는 구간 수입니다. 구간 수가 너무 적으면 분포가 단순하게 보이고, 너무 많으면 작은 변동이 과도하게 강조될 수 있습니다. 한 가지 구간 수만 보고 결론을 내리기보다 몇 가지 값을 비교해 보는 것이 좋습니다.

### 산점도

산점도는 두 숫자형 변수의 관계를 탐색할 때 사용합니다. 상품 가격과 판매 수량, 고객별 주문 횟수와 구매 금액 등의 관계를 확인할 수 있습니다.

`alpha`는 점의 투명도입니다. 점이 많이 겹칠 때 0과 1 사이의 값을 사용하면 밀집된 구간을 더 쉽게 확인할 수 있습니다.

산점도에서 관계가 보이더라도 인과관계가 증명되는 것은 아닙니다. 카테고리, 할인, 노출량, 재고, 계절성 같은 다른 요인이 영향을 줄 수 있습니다.

## 5. 시각화를 위한 데이터 준비

이번 장의 실습 노트북 파일은 `notebooks/ch07_visualization.ipynb`입니다.

먼저 필요한 패키지를 불러오고 프로젝트 경로를 설정합니다.

```python
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
```

현재 작업 폴더가 프로젝트 루트이거나 `notebooks` 폴더인 경우를 모두 처리합니다.

```python
project_root = Path.cwd()

if project_root.name == "notebooks":
    project_root = project_root.parent

processed_dir = project_root / "data" / "processed"
report_dir = project_root / "reports"
figure_dir = report_dir / "figures"

figure_dir.mkdir(parents=True, exist_ok=True)

print("프로젝트 루트:", project_root.resolve())
print("전처리 데이터 폴더:", processed_dir.resolve())
print("그래프 저장 폴더:", figure_dir.resolve())
```

다른 위치에서 노트북을 실행하고 있다면 `project_root`를 실제 프로젝트 폴더로 직접 지정해야 합니다.

필요한 파일이 모두 존재하는지 확인합니다.

```python
required_files = [
    "customers_clean.csv",
    "products_clean.csv",
    "orders_clean.csv",
    "order_items_clean.csv",
]

missing_files = [
    file_name
    for file_name in required_files
    if not (processed_dir / file_name).exists()
]

if missing_files:
    raise FileNotFoundError(
        "전처리 결과 파일을 찾을 수 없습니다: "
        + ", ".join(missing_files)
        + "\n5장의 전처리 실습을 먼저 실행하세요."
    )
```

전처리 데이터를 불러옵니다.

```python
customers = pd.read_csv(
    processed_dir / "customers_clean.csv"
)
products = pd.read_csv(
    processed_dir / "products_clean.csv"
)
orders = pd.read_csv(
    processed_dir / "orders_clean.csv"
)
order_items = pd.read_csv(
    processed_dir / "order_items_clean.csv"
)
```

필수 컬럼도 확인합니다.

```python
required_columns = {
    "customers": {
        "customer_id",
    },
    "products": {
        "product_id",
        "product_name",
        "category",
        "price",
    },
    "orders": {
        "order_id",
        "customer_id",
        "order_date",
        "order_status",
    },
    "order_items": {
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    },
}

dataframes = {
    "customers": customers,
    "products": products,
    "orders": orders,
    "order_items": order_items,
}

for name, required in required_columns.items():
    missing = required - set(dataframes[name].columns)

    if missing:
        raise KeyError(
            f"{name}에 필요한 컬럼이 없습니다: "
            f"{sorted(missing)}"
        )
```

날짜와 숫자형 컬럼을 다시 확인합니다. CSV로 저장했다가 다시 불러오면 날짜 타입 정보가 유지되지 않기 때문에 재변환이 필요합니다.

```python
orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    errors="coerce",
)

numeric_columns = [
    (products, "price"),
    (order_items, "quantity"),
    (order_items, "unit_price"),
]

for dataframe, column in numeric_columns:
    dataframe[column] = pd.to_numeric(
        dataframe[column],
        errors="coerce",
    )
```

변환 실패와 고유 키 품질을 확인합니다.

```python
print(
    "order_date 변환 실패:",
    int(orders["order_date"].isna().sum()),
)
print(
    "price 변환 실패:",
    int(products["price"].isna().sum()),
)
print(
    "quantity 변환 실패:",
    int(order_items["quantity"].isna().sum()),
)
print(
    "unit_price 변환 실패:",
    int(order_items["unit_price"].isna().sum()),
)

print(
    "orders.order_id 중복:",
    int(orders["order_id"].duplicated().sum()),
)
print(
    "products.product_id 중복:",
    int(products["product_id"].duplicated().sum()),
)
```

시각화 전에 변환 실패나 고유 키 중복이 남아 있다면 원인을 먼저 해결해야 합니다.

`line_total`이 없으면 수량과 단가로 다시 계산합니다.

```python
if "line_total" not in order_items.columns:
    order_items["line_total"] = (
        order_items["quantity"]
        * order_items["unit_price"]
    )
else:
    order_items["line_total"] = pd.to_numeric(
        order_items["line_total"],
        errors="coerce",
    )
```

주문 상세와 주문 정보를 연결합니다.

```python
order_sales = order_items.merge(
    orders[
        [
            "order_id",
            "customer_id",
            "order_date",
            "order_status",
        ]
    ],
    on="order_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)
```

연결되지 않은 주문 상세가 있는지 확인합니다.

```python
unmatched_order_items = order_sales.loc[
    order_sales["_merge"].ne("both")
].copy()

print(
    "주문 정보와 연결되지 않은 주문 상세:",
    len(unmatched_order_items),
)
```

미연결 행이 있다면 그래프를 만들기 전에 원인을 확인합니다. 정상 연결된 행만 남기고, 완료 주문을 별도로 분리합니다.

```python
order_sales = order_sales.loc[
    order_sales["_merge"].eq("both")
].drop(columns="_merge")

completed_order_sales = order_sales.loc[
    order_sales["order_status"].eq("completed")
].copy()
```

완료 주문 상세에 상품 정보를 연결합니다.

```python
completed_sales_items = completed_order_sales.merge(
    products[
        [
            "product_id",
            "product_name",
            "category",
            "price",
        ]
    ],
    on="product_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)
```

상품 정보와 연결되지 않은 주문 상세도 확인합니다.

```python
unmatched_products = completed_sales_items.loc[
    completed_sales_items["_merge"].ne("both")
].copy()

print(
    "상품 정보와 연결되지 않은 완료 주문 상세:",
    len(unmatched_products),
)

completed_sales_items = completed_sales_items.loc[
    completed_sales_items["_merge"].eq("both")
].drop(columns="_merge")
```

## 6. 시각화용 집계 데이터 만들기

### 카테고리별 완료 주문 금액

```python
category_sales = (
    completed_sales_items
    .groupby(
        "category",
        as_index=False,
        dropna=False,
    )
    .agg(
        total_quantity=("quantity", "sum"),
        completed_amount=("line_total", "sum"),
    )
    .sort_values(
        "completed_amount",
        ascending=False,
    )
)

completed_amount_sum = (
    category_sales["completed_amount"].sum()
)

category_sales["amount_ratio_pct"] = (
    category_sales["completed_amount"]
    .div(completed_amount_sum)
    .mul(100)
    .round(2)
)

category_sales
```

### 월별 완료 주문 금액

날짜 변환에 실패한 행은 월별 분석에 사용할 수 없으므로 별도로 확인합니다.

```python
invalid_date_sales = completed_order_sales.loc[
    completed_order_sales["order_date"].isna()
].copy()

print(
    "월별 집계에서 제외되는 날짜 결측 행:",
    len(invalid_date_sales),
)
```

월을 `Period` 타입으로 만들면 시간 순서대로 안정적으로 정렬할 수 있습니다.

```python
monthly_sales = (
    completed_order_sales
    .dropna(subset=["order_date"])
    .assign(
        order_month=lambda df: (
            df["order_date"].dt.to_period("M")
        )
    )
    .groupby(
        "order_month",
        as_index=False,
    )
    .agg(
        completed_amount=("line_total", "sum"),
        completed_order_count=(
            "order_id",
            "nunique",
        ),
    )
    .sort_values("order_month")
)

monthly_sales["month_start"] = (
    monthly_sales["order_month"].dt.to_timestamp()
)

monthly_sales
```

데이터가 없는 월도 그래프에 0으로 표시해야 한다면 전체 월 범위를 만들어 재색인할 수 있습니다. 그러나 “거래가 없어서 0인 월”과 “데이터가 누락된 월”은 의미가 다르므로 원본 수집 상태를 먼저 확인해야 합니다.

### 상품별 완료 주문 판매 수량과 금액

```python
product_sales = (
    completed_sales_items
    .groupby(
        [
            "product_id",
            "product_name",
            "category",
            "price",
        ],
        as_index=False,
    )
    .agg(
        completed_quantity=("quantity", "sum"),
        completed_amount=("line_total", "sum"),
    )
    .sort_values(
        "completed_amount",
        ascending=False,
    )
)

product_sales.head()
```

### 고객별 완료 주문 구매 금액

고객명을 그래프에 표시하지 않고 고객 ID를 기준으로 집계합니다.

```python
customer_sales = (
    completed_order_sales
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        completed_order_count=(
            "order_id",
            "nunique",
        ),
        completed_amount=("line_total", "sum"),
    )
    .sort_values(
        "completed_amount",
        ascending=False,
    )
)

customer_sales["average_completed_order_amount"] = (
    customer_sales["completed_amount"]
    .div(customer_sales["completed_order_count"])
    .round(0)
)

customer_sales.head()
```

## 7. 그래프 저장을 위한 공통 함수

같은 저장 코드를 반복하지 않도록 간단한 함수를 만듭니다.

```python
def save_and_show(
    fig,
    file_name,
    *,
    dpi=150,
):
    output_path = figure_dir / file_name

    fig.tight_layout()
    fig.savefig(
        output_path,
        dpi=dpi,
        bbox_inches="tight",
    )
    plt.show()

    return output_path
```

`*` 뒤에 있는 `dpi`는 키워드 이름을 명시해 전달하도록 만든 선택 인자입니다. 예를 들어 `save_and_show(fig, "chart.png", dpi=200)`처럼 사용할 수 있습니다.

금액 축 형식도 준비합니다.

```python
money_formatter = FuncFormatter(
    lambda value, position: f"{value:,.0f}"
)
```

## 8. 주요 그래프 만들기

### 8.1 카테고리별 완료 주문 금액 막대그래프

```python
fig, ax = plt.subplots(figsize=(10, 5))

ax.bar(
    category_sales["category"],
    category_sales["completed_amount"],
)

ax.set_title("카테고리별 완료 주문 금액")
ax.set_xlabel("카테고리")
ax.set_ylabel("완료 주문 금액")
ax.set_ylim(bottom=0)
ax.yaxis.set_major_formatter(money_formatter)
ax.tick_params(
    axis="x",
    rotation=45,
)

for label in ax.get_xticklabels():
    label.set_horizontalalignment("right")

category_chart_path = save_and_show(
    fig,
    "ch07_category_completed_amount_bar.png",
)
```

이 그래프는 완료 주문 기준으로 어떤 카테고리의 금액이 큰지 보여 줍니다. 금액이 높은 이유가 판매 수량, 평균 단가, 상품 수 중 무엇 때문인지는 추가 분석이 필요합니다.

### 8.2 월별 완료 주문 금액 선 그래프

```python
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(
    monthly_sales["month_start"],
    monthly_sales["completed_amount"],
    marker="o",
)

ax.set_title("월별 완료 주문 금액 추이")
ax.set_xlabel("주문 월")
ax.set_ylabel("완료 주문 금액")
ax.set_ylim(bottom=0)
ax.yaxis.set_major_formatter(money_formatter)
ax.grid(
    axis="y",
    alpha=0.3,
)

fig.autofmt_xdate()

monthly_chart_path = save_and_show(
    fig,
    "ch07_monthly_completed_amount_line.png",
)
```

특정 월의 금액이 증가하거나 감소했다는 사실은 관찰 결과입니다. 원인을 설명하려면 완료 주문 수, 평균 주문 금액, 카테고리 구성, 프로모션 여부 등을 추가로 확인해야 합니다.

### 8.3 상품 가격 분포 히스토그램

상품 가격은 상품 마스터의 분포이므로 주문 상태와 무관합니다.

```python
fig, ax = plt.subplots(figsize=(10, 5))

ax.hist(
    products["price"].dropna(),
    bins=20,
    edgecolor="black",
)

ax.set_title("상품 가격 분포")
ax.set_xlabel("상품 가격")
ax.set_ylabel("상품 수")
ax.set_xlim(left=0)
ax.xaxis.set_major_formatter(money_formatter)

price_histogram_path = save_and_show(
    fig,
    "ch07_product_price_hist.png",
)
```

`bins=20`은 가격 범위를 20개 구간으로 나눈다는 뜻입니다. 구간 수를 10, 20, 30 등으로 바꾸어 분포가 어떻게 달라 보이는지 비교해 볼 수 있습니다.

### 8.4 상품 가격과 완료 주문 판매 수량 산점도

```python
fig, ax = plt.subplots(figsize=(10, 5))

ax.scatter(
    product_sales["price"],
    product_sales["completed_quantity"],
    alpha=0.6,
)

ax.set_title(
    "상품 가격과 완료 주문 판매 수량의 관계"
)
ax.set_xlabel("상품 가격")
ax.set_ylabel("완료 주문 판매 수량")
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)
ax.xaxis.set_major_formatter(money_formatter)
ax.grid(
    alpha=0.2,
)

scatter_chart_path = save_and_show(
    fig,
    "ch07_price_completed_quantity_scatter.png",
)
```

산점도는 두 변수 사이의 패턴을 탐색하는 데 사용합니다. 가격이 높을수록 판매 수량이 줄어드는 것처럼 보여도 가격이 원인이라고 단정할 수 없습니다. 카테고리, 할인, 노출량, 재고, 계절성 등 다른 요인을 함께 확인해야 합니다.

### 8.5 완료 주문 구매 금액 상위 고객 가로 막대그래프

실제 고객 이름이나 고객 ID를 그래프에 노출하지 않고 순위 기반 익명 라벨을 만듭니다.

```python
top_customers = (
    customer_sales
    .head(10)
    .sort_values("completed_amount")
    .copy()
)

top_customers["customer_label"] = [
    f"고객 {rank:02d}"
    for rank in range(
        len(top_customers),
        0,
        -1,
    )
]
```

익명 라벨은 그래프 표시용입니다. 실제 고객과의 대응이 필요한 내부 분석이라면 접근 권한이 제한된 별도 매핑표로 관리해야 합니다.

```python
fig, ax = plt.subplots(figsize=(10, 6))

ax.barh(
    top_customers["customer_label"],
    top_customers["completed_amount"],
)

ax.set_title(
    "완료 주문 구매 금액 상위 고객"
)
ax.set_xlabel("완료 주문 구매 금액")
ax.set_ylabel("익명 고객")
ax.set_xlim(left=0)
ax.xaxis.set_major_formatter(money_formatter)

top_customer_chart_path = save_and_show(
    fig,
    "ch07_top_customers_anonymized_barh.png",
)
```

이 그래프는 구매 금액이 큰 고객군을 보여 주지만, 충성 고객을 자동으로 의미하지는 않습니다. 한 번에 크게 구매한 고객과 여러 번 반복 구매한 고객을 구분하려면 주문 횟수와 평균 주문 금액을 함께 확인해야 합니다.

### 8.6 주문 상태별 주문 수 막대그래프

주문 상태 분포는 완료·취소·환불을 모두 포함한 전체 주문을 기준으로 확인합니다.

```python
order_status = (
    orders["order_status"]
    .fillna("missing")
    .value_counts()
    .rename_axis("order_status")
    .reset_index(name="order_count")
)
```

```python
fig, ax = plt.subplots(figsize=(8, 5))

ax.bar(
    order_status["order_status"],
    order_status["order_count"],
)

ax.set_title("주문 상태별 주문 수")
ax.set_xlabel("주문 상태")
ax.set_ylabel("주문 수")
ax.set_ylim(bottom=0)
ax.tick_params(
    axis="x",
    rotation=30,
)

for label in ax.get_xticklabels():
    label.set_horizontalalignment("right")

order_status_chart_path = save_and_show(
    fig,
    "ch07_order_status_bar.png",
)
```

상태별 건수만으로 취소나 환불의 원인을 알 수는 없습니다. 기간, 결제 수단, 상품 카테고리, 고객군과의 관계를 추가로 확인해야 합니다.

<figure class="figure">
  <img src="../assets/images/ch07/ch07_sales_visualization_dashboard.png" alt="온라인 쇼핑몰 주요 시각화 예시 대시보드">
  <figcaption>그림 7-4. 온라인 쇼핑몰 주요 시각화 예시 대시보드</figcaption>
</figure>

## 9. 그래프를 보고서로 연결하기

저장된 그래프 파일을 확인합니다.

```python
sorted(
    path.name
    for path in figure_dir.glob("ch07_*.png")
)
```

이번 장에서 저장한 주요 파일은 다음과 같습니다.

```text
ch07_category_completed_amount_bar.png
ch07_monthly_completed_amount_line.png
ch07_product_price_hist.png
ch07_price_completed_quantity_scatter.png
ch07_top_customers_anonymized_barh.png
ch07_order_status_bar.png
```

그래프의 목적과 해석 범위를 표로 정리합니다.

```python
visualization_summary = pd.DataFrame(
    {
        "chart": [
            "카테고리별 완료 주문 금액",
            "월별 완료 주문 금액",
            "상품 가격 분포",
            "가격과 완료 주문 판매 수량",
            "완료 주문 구매 금액 상위 고객",
            "주문 상태별 주문 수",
        ],
        "question": [
            "카테고리별 완료 주문 금액은 어떻게 다른가?",
            "월별 완료 주문 금액은 어떻게 변하는가?",
            "상품 가격은 어떤 구간에 몰려 있는가?",
            "가격과 완료 주문 판매 수량은 관계가 있는가?",
            "구매 금액이 큰 고객군은 어떻게 구성되는가?",
            "주문 상태별 주문 수는 어떻게 다른가?",
        ],
        "scope": [
            "completed 주문만 포함",
            "completed 주문과 유효한 날짜만 포함",
            "전체 상품 마스터",
            "completed 주문만 포함",
            "completed 주문만 포함, 고객 익명화",
            "전체 주문 상태",
        ],
        "file_name": [
            category_chart_path.name,
            monthly_chart_path.name,
            price_histogram_path.name,
            scatter_chart_path.name,
            top_customer_chart_path.name,
            order_status_chart_path.name,
        ],
    }
)

visualization_summary
```

`DataFrame.to_markdown()`은 `tabulate` 패키지를 사용합니다. 이 저장소의 `requirements.txt`에는 `tabulate`가 포함되어 있습니다. 다른 환경에서 오류가 발생하면 패키지를 설치하거나 `to_string(index=False)`로 대체할 수 있습니다.

```python
try:
    summary_table = (
        visualization_summary.to_markdown(
            index=False
        )
    )
except ImportError:
    summary_table = (
        "```text\n"
        + visualization_summary.to_string(
            index=False
        )
        + "\n```"
    )
```

보고서를 저장합니다.

```python
summary_text = f"""# Chapter 7 데이터 시각화 요약 보고서

## 1. 시각화 목적

전처리된 온라인 쇼핑몰 데이터를 사용해 비교, 추세, 분포, 관계를 그래프로 확인했습니다.

## 2. 집계 기준

- 완료 주문 금액 관련 그래프는 `order_status == "completed"`인 주문만 포함했습니다.
- `line_total`은 수량과 단가를 곱한 주문 상세 금액입니다.
- 할인, 배송비, 세금, 부분 환불 정보가 없으므로 회계상 순매출과 같다고 단정하지 않습니다.
- 고객 그래프에는 실제 이름과 고객 ID를 표시하지 않았습니다.

## 3. 생성한 그래프 목록

{summary_table}

## 4. 해석 시 주의사항

- 그래프는 관찰된 패턴을 보여 주지만 원인을 자동으로 설명하지 않습니다.
- 범주별 금액 차이는 판매 수량, 단가, 상품 수를 함께 확인해야 합니다.
- 월별 변화는 완료 주문 수와 평균 주문 금액을 함께 확인해야 합니다.
- 산점도에서 관계가 보여도 인과관계라고 단정하지 않습니다.
- 축, 단위, 포함·제외 기준, 익명화 여부를 보고서에 함께 기록합니다.

## 5. 다음 단계

다음 장에서는 데이터 불러오기, 전처리, EDA, 시각화를 종합한 중간 프로젝트를 수행합니다.
"""

summary_path = (
    report_dir
    / "ch07_visualization_summary.md"
)

summary_path.write_text(
    summary_text,
    encoding="utf-8",
)

summary_path
```

<figure class="figure">
  <img src="../assets/images/ch07/ch07_visualization_to_report_flow.png" alt="시각화 결과를 보고서와 발표 자료로 연결하는 흐름">
  <figcaption>그림 7-5. 시각화 결과를 보고서와 발표 자료로 연결하는 흐름</figcaption>
</figure>

## 10. LLM에게 그래프 선택과 해석을 요청하기

LLM은 그래프 종류 선택, matplotlib 코드 초안 작성, 해석 문장 정리에 도움을 줄 수 있습니다. 그러나 집계 기준과 실제 수치를 검증하는 책임은 사람에게 있습니다.

원본 고객명, 고객 ID, 주문 상세 행을 승인되지 않은 외부 LLM 서비스에 입력하지 않습니다. 다음과 같은 집계 정보만 제공하는 것이 좋습니다.

- 그래프가 답하려는 질문
- 사용한 집계 기준
- 익명화된 범주명
- 집계된 값과 단위
- 제외된 데이터와 결측치
- 그래프 종류
- 추가로 확인하고 싶은 내용

### 그래프 선택 요청 예시

```text
다음 분석 질문에 적합한 그래프를 추천해 주세요.

질문:
- 월별 완료 주문 금액은 어떻게 변하는가?
- 카테고리별 완료 주문 금액은 어떻게 다른가?
- 상품 가격은 어느 구간에 많이 분포하는가?
- 상품 가격과 완료 주문 판매 수량은 관계가 있는가?

각 질문마다 다음 내용을 설명해 주세요.
1. 추천 그래프
2. x축과 y축
3. 정렬 방법
4. 포함·제외 기준
5. 해석할 때 주의할 점
```

### 그래프 해석 요청 예시

```text
다음은 완료 주문만 포함해 계산한 카테고리별 주문 상세 금액입니다.

category,completed_amount,amount_ratio_pct
전자기기,12500000,42.5
생활용품,7800000,26.5
패션,6200000,21.1
식품,2900000,9.9

보고서용 해석 초안을 작성해 주세요.

조건:
- 수치를 다시 확인해 요약할 것
- 관찰 결과와 원인 가설을 구분할 것
- 데이터에 없는 원인을 단정하지 말 것
- 이 값이 회계상 순매출이라고 단정하지 말 것
- 추가로 확인할 분석 질문을 제안할 것
```

### 잘못된 그래프 선택 검토 예시

```text
다음 시각화 제안이 적절한지 검토해 주세요.

1. 월별 완료 주문 금액을 파이 차트로 표현
2. 상품 가격 분포를 선 그래프로 표현
3. 카테고리별 완료 주문 금액을 산점도로 표현
4. 상품 가격과 완료 주문 판매 수량을 산점도로 표현

부적절한 경우 더 적합한 그래프와 이유를 설명해 주세요.
```

월별 금액은 시간 흐름을 보여야 하므로 선 그래프가 적합합니다. 상품 가격 분포는 히스토그램이 적합합니다. 카테고리별 금액은 범주별 비교이므로 막대그래프가 적합합니다. 가격과 판매 수량의 관계는 두 숫자형 변수의 관계이므로 산점도가 적합합니다.

### LLM이 만든 그래프 코드 검토 기준

| 검토 기준 | 확인할 질문 |
| --- | --- |
| 데이터 범위 | 완료·취소·환불 중 무엇을 포함했는가? |
| 집계 단위 | 주문, 주문 상세, 고객, 상품 중 무엇을 세었는가? |
| 병합 관계 | `many_to_one` 등 예상 관계가 검증되었는가? |
| 시간 정렬 | 월과 날짜가 시간 순서대로 정렬되었는가? |
| 그래프 선택 | 질문의 비교·추세·분포·관계 목적과 맞는가? |
| 축과 단위 | 축 이름과 금액·건수 단위가 명확한가? |
| 축 범위 | 범주 비교를 과장하는 축 절단이 없는가? |
| 결측치 | 그래프에서 제외된 결측치가 기록되어 있는가? |
| 저장 순서 | `savefig()`가 `show()`보다 먼저 실행되는가? |
| 개인정보 | 고객 이름과 식별 가능한 값이 제거되었는가? |
| 해석 | 관찰과 원인 가설을 구분했는가? |

## 11. 그래프를 해석할 때 주의할 점

그래프는 패턴을 보여 주지만 원인을 자동으로 설명하지는 않습니다.

카테고리별 완료 주문 금액이 높다는 사실은 관찰 결과입니다. 그 이유가 상품 수가 많아서인지, 판매 수량이 많아서인지, 단가가 높아서인지는 추가 분석이 필요합니다.

월별 완료 주문 금액이 증가하거나 감소했다면 다음을 함께 확인합니다.

- 완료 주문 수
- 주문당 평균 금액
- 카테고리 구성
- 신규·기존 고객 비중
- 데이터 수집 누락 여부
- 프로모션이나 가격 정책 변화

상품 가격 히스토그램에서 고가 상품이 일부 보인다면 실제 고가 상품군인지 입력 오류인지 확인합니다.

산점도에서 가격과 판매 수량 사이의 패턴이 보여도 가격이 판매량을 변화시켰다고 단정하지 않습니다. 카테고리별로 점의 분포가 다른지, 할인이나 노출량 같은 변수가 있는지 추가로 확인합니다.

구매 금액 상위 고객 그래프는 내부 분석에 유용할 수 있지만, 실제 이름이나 식별자를 보고서에 노출해서는 안 됩니다. 총 구매 금액뿐 아니라 주문 횟수와 평균 주문 금액도 함께 확인해야 합니다.

## 12. 최종 점검

| 점검 항목 | 확인 |
| --- | --- |
| 분석 질문에 맞는 그래프를 선택했는가? | □ |
| 데이터의 포함·제외 기준을 기록했는가? | □ |
| 완료 주문 금액과 전체 주문 상태를 구분했는가? | □ |
| `line_total`을 회계상 순매출로 단정하지 않았는가? | □ |
| x축과 y축 이름과 단위를 표시했는가? | □ |
| 범주형 데이터가 읽기 좋은 순서로 정렬되었는가? | □ |
| 시간 데이터가 올바른 순서로 정렬되었는가? | □ |
| 막대그래프 값 축이 특별한 이유 없이 잘리지 않았는가? | □ |
| 한글 폰트와 음수 기호가 정상적으로 표시되는가? | □ |
| 그래프 레이블이 겹치거나 잘리지 않는가? | □ |
| `savefig()`를 `show()`보다 먼저 실행했는가? | □ |
| 그래프 해석에서 관찰과 원인 가설을 구분했는가? | □ |
| 개인정보와 식별 가능한 값을 익명화했는가? | □ |
| LLM이 제안한 코드와 해석을 실제 데이터로 검증했는가? | □ |

직접 더 연습하려면 다음을 수행해 봅니다.

- 카테고리별 완료 주문 금액과 완료 주문 판매 수량을 각각 시각화합니다.
- 월별 완료 주문 수와 월별 완료 주문 금액을 비교합니다.
- 히스토그램의 `bins`를 10, 20, 30으로 바꾸어 분포를 비교합니다.
- 상품 가격과 완료 주문 판매 수량 산점도를 카테고리별로 나누어 살펴봅니다.
- 익명화한 고객 그래프에 주문 횟수 정보를 함께 제시합니다.
- 생성한 그래프를 `reports/figures` 폴더에 저장하고 보고서에 포함·제외 기준을 기록합니다.
- LLM에게 그래프 해석을 요청한 뒤 데이터에 없는 원인이나 과장된 표현이 포함되었는지 검토합니다.

이번 장에서는 전처리 결과를 바탕으로 데이터 시각화를 수행했습니다. 막대그래프는 범주별 크기를 비교할 때, 선 그래프는 시간에 따른 변화를 확인할 때, 히스토그램은 숫자형 데이터의 분포를 볼 때, 산점도는 두 숫자형 변수의 관계를 탐색할 때 사용합니다.

좋은 시각화는 단순히 보기 좋은 그래프가 아닙니다. 분석 질문, 데이터 범위, 축과 단위, 개인정보 보호, 해석의 한계가 모두 분명해야 합니다. 다음 장에서는 데이터 불러오기, 전처리, EDA, 시각화를 종합한 중간 프로젝트를 수행합니다.
