# 4장 실습. pandas로 데이터에 질문하기

> 이 문서는 학생이 그대로 따라 할 수 있도록 작성한 실습 진행 가이드입니다.  
> Chapter 04의 목표는 **pandas 문법을 외우는 것이 아니라, 질문에 필요한 데이터만 선택하고 안전하게 병합·집계한 뒤 결과를 검증하는 흐름**을 익히는 것입니다.

---

## 실습 목표

이 실습을 마치면 다음을 직접 수행할 수 있어야 합니다.

- 필요한 컬럼과 행을 선택할 수 있습니다.
- 실제 값의 종류를 확인한 뒤 필터링할 수 있습니다.
- 데이터를 정렬할 수 있습니다.
- `quantity × unit_price`로 `line_total`을 만들 수 있습니다.
- `validate`와 `indicator`로 `merge()` 결과를 검증할 수 있습니다.
- `completed` 주문만 남겨 완료 주문 기준 금액을 계산할 수 있습니다.
- 카테고리별·상품별·월별·고객별 요약표를 만들 수 있습니다.
- 결과 CSV를 저장하고 다시 확인할 수 있습니다.
- LLM이 만든 pandas 코드를 실제 데이터 구조와 비교해 검증할 수 있습니다.

---

## 사용할 파일

- Notebook: `notebooks/ch04_pandas_basic.ipynb`
- 데이터: `data/raw/customers.csv`
- 데이터: `data/raw/products.csv`
- 데이터: `data/raw/orders.csv`
- 데이터: `data/raw/order_items.csv`
- 결과 폴더: `reports/`

공식 저장소:

https://github.com/GilbertMoon/llm-data-analysis-course

---

## 시작하기 전에

Chapter 02와 03이 정상적으로 완료되어 있어야 합니다.

다음 조건을 먼저 확인하세요.

```text
.venv 활성화
Notebook 커널 == 프로젝트 .venv
4개 CSV 존재
ch03_data_overview.ipynb 실행 가능
```

데이터가 없다면 프로젝트 루트에서 실행합니다.

```powershell
python scripts/generate_sample_data.py
```

> **중요**  
> 이번 장의 `total_sales`는 **completed 주문에 포함된 `line_total`의 합계**입니다. 회계상 순매출이라고 단정하지 않습니다.

---

# STEP 1. Chapter 04 Notebook 열기

## 목적

이번 장에서 사용할 실습 Notebook을 열고 올바른 Python 커널을 선택합니다.

## 실행

VS Code에서 다음 파일을 엽니다.

```text
notebooks/ch04_pandas_basic.ipynb
```

오른쪽 위 커널 선택 메뉴에서 프로젝트의 `.venv`를 선택합니다.

첫 셀부터 순서대로 실행합니다.

## 예상 결과

다음 값이 출력됩니다.

```text
Python 실행 파일
현재 작업 폴더
프로젝트 루트
데이터 폴더
결과 저장 폴더
```

## 성공 기준

- Python 실행 파일 경로에 프로젝트 `.venv`가 포함됩니다.
- `DATA_DIR`이 `data/raw`를 가리킵니다.
- `REPORT_DIR`이 `reports`를 가리킵니다.

## 오류 해결

`FileNotFoundError: 프로젝트 루트 폴더를 찾을 수 없습니다.`가 나오면 Notebook을 저장소 밖에서 실행하고 있지 않은지 확인합니다.

---

# STEP 2. 4개 CSV를 확인하고 불러오기

## 목적

분석에 필요한 데이터가 모두 존재하는지 확인한 뒤 pandas DataFrame으로 읽습니다.

## 실행

Notebook의 데이터 파일 확인 셀을 실행합니다.

핵심 코드는 다음과 같습니다.

```python
required_files = [
    "customers.csv",
    "products.csv",
    "orders.csv",
    "order_items.csv",
]
```

그다음 CSV를 읽습니다.

```python
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")
order_items = pd.read_csv(DATA_DIR / "order_items.csv")
```

## 예상 결과

```text
데이터 불러오기 완료
```

과 함께 4개의 DataFrame이 생성됩니다.

## 성공 기준

- 누락 파일 오류가 없습니다.
- `customers`, `products`, `orders`, `order_items` 변수가 생성됩니다.

## 오류 해결

파일이 없다면 프로젝트 루트에서 다음 명령을 실행합니다.

```powershell
python scripts/generate_sample_data.py
```

---

# STEP 3. 실제 컬럼명 확인하기

## 목적

LLM이나 예제 코드가 실제 데이터에 없는 컬럼명을 사용하지 않도록 먼저 구조를 확인합니다.

## 실행

Notebook의 필수 컬럼 검증 셀을 실행합니다.

```python
for name, df in datasets.items():
    print(name, df.shape, df.columns.tolist())
```

## 예상 결과

각 데이터셋의 shape와 컬럼 목록이 출력됩니다.

예를 들어 다음 컬럼이 포함되어 있어야 합니다.

```text
customers: customer_id, gender, age, city
products: product_id, product_name, category, price
orders: order_id, customer_id, order_date, order_status
order_items: order_id, product_id, quantity, unit_price
```

## 성공 기준

필수 컬럼 누락으로 인한 `KeyError`가 발생하지 않습니다.

## 오류 해결

컬럼이 다르면 임의로 코드부터 수정하지 말고 실제 CSV 헤더와 `df.columns.tolist()` 결과를 비교합니다.

---

# STEP 4. 컬럼 선택과 행 필터링

## 목적

질문에 필요한 데이터만 선택하는 기본 pandas 패턴을 익힙니다.

## 실행

필요한 컬럼만 선택합니다.

```python
customer_basic = customers[[
    "customer_id",
    "gender",
    "age",
    "city",
]]
```

30세 이상 고객을 선택합니다.

```python
customers_over_30 = customers[
    customers["age"] >= 30
]
```

서울 또는 부산 고객을 선택합니다.

```python
city_customers = customers[
    customers["city"].isin(["서울", "부산"])
]
```

필터링 전에 실제 값을 확인합니다.

```python
customers["city"].value_counts()
orders["order_status"].value_counts()
```

## 예상 결과

각 조건에 해당하는 고객 수와 실제 도시·주문 상태 값이 출력됩니다.

## 성공 기준

- 코드가 오류 없이 실행됩니다.
- 필터 값이 실제 `value_counts()` 결과에 존재합니다.

## 오류 해결

결과가 0건이면 먼저 `서울` 대신 다른 표기인지 확인합니다.

```python
customers["city"].unique()
```

---

# STEP 5. 정렬과 파생 컬럼 만들기

## 목적

데이터를 원하는 기준으로 정렬하고, 기존 컬럼으로 새로운 계산 컬럼을 만듭니다.

## 실행

가격이 높은 상품을 확인합니다.

```python
products.sort_values(
    "price",
    ascending=False,
).head(10)
```

`line_total`을 만듭니다.

```python
order_items = order_items.copy()
order_items["line_total"] = (
    order_items["quantity"]
    * order_items["unit_price"]
)
```

## 예상 결과

`order_items`에 `line_total` 컬럼이 추가됩니다.

## 성공 기준

다음 컬럼이 함께 보입니다.

```text
order_id
product_id
quantity
unit_price
line_total
```

## 오류 해결

`KeyError`가 발생하면 `quantity`, `unit_price` 컬럼명을 다시 확인합니다.

> 아직 주문 상태를 연결하지 않았으므로 `line_total.sum()`을 완료 주문 금액이라고 부르지 않습니다.

---

# STEP 6. orders와 병합하고 검증하기

## 목적

주문 상세에 주문 상태와 주문일을 연결하고 병합이 안전했는지 확인합니다.

## 실행

먼저 `orders.order_id`가 고유한지 확인합니다.

```python
print(
    "orders.order_id 중복 수:",
    orders["order_id"].duplicated().sum(),
)
```

그다음 병합합니다.

```python
order_sales = order_items.merge(
    orders[[
        "order_id",
        "customer_id",
        "order_date",
        "order_status",
    ]],
    on="order_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)
```

병합 직후 확인합니다.

```python
print("병합 전 행 수:", len(order_items))
print("병합 후 행 수:", len(order_sales))
print(order_sales["_merge"].value_counts())
```

## 예상 결과

현재 샘플 데이터에서는 일반적으로 다음을 기대합니다.

```text
orders.order_id 중복 수: 0
병합 전 행 수 == 병합 후 행 수
_merge는 both만 존재
```

## 성공 기준

- `validate="many_to_one"` 오류가 없습니다.
- 병합 전후 행 수가 같습니다.
- `left_only`가 없습니다.

## 오류 해결

`MergeError`가 나면 오른쪽 키인 `orders.order_id`가 중복되어 있는지 확인합니다.

`left_only`가 있다면 해당 `order_id`가 `orders`에 실제 존재하는지 확인합니다.

---

# STEP 7. 날짜 변환 후 completed 주문만 선택하기

## 목적

이번 장의 계산 범위를 `completed` 주문으로 명확하게 제한합니다.

## 실행

```python
order_sales["order_date"] = pd.to_datetime(
    order_sales["order_date"],
    errors="coerce",
)

print(
    "날짜 변환 실패:",
    order_sales["order_date"].isna().sum(),
)
```

완료 주문만 선택합니다.

```python
completed_order_sales = order_sales[
    order_sales["order_status"] == "completed"
].copy()
```

월 컬럼을 만듭니다.

```python
completed_order_sales["order_month"] = (
    completed_order_sales["order_date"]
    .dt.to_period("M")
    .astype(str)
)
```

## 예상 결과

- 날짜 변환 실패 건수가 출력됩니다.
- 완료 주문 상세 행만 남습니다.
- `order_month` 컬럼이 생성됩니다.

## 성공 기준

```python
completed_order_sales["order_status"].unique()
```

결과가 `completed`만 포함합니다.

## 오류 해결

완료 주문이 0건이라면 먼저 실제 주문 상태를 확인합니다.

```python
orders["order_status"].value_counts(dropna=False)
```

---

# STEP 8. products와 병합하고 다시 검증하기

## 목적

완료 주문 상세에 상품명과 카테고리를 연결합니다.

## 실행

```python
completed_sales_items = completed_order_sales.merge(
    products,
    on="product_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)
```

확인합니다.

```python
print("병합 전:", len(completed_order_sales))
print("병합 후:", len(completed_sales_items))
print(completed_sales_items["_merge"].value_counts())
```

## 예상 결과

병합 전후 행 수가 같고 `_merge`는 모두 `both`입니다.

## 성공 기준

- `products.product_id` 고유성이 유지됩니다.
- 미매칭 상품이 없습니다.

## 오류 해결

병합 후 행 수가 늘었다면 `products.product_id` 중복 여부를 확인합니다.

```python
products["product_id"].duplicated().sum()
```

---

# STEP 9. 카테고리별·상품별 요약표 만들기

## 목적

`groupby()`와 `agg()`로 실제 분석 질문에 답하는 요약표를 만듭니다.

## 실행

카테고리별 집계:

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
```

상품별 집계:

```python
product_sales = (
    completed_sales_items
    .groupby(
        ["product_id", "product_name", "category"],
        as_index=False,
    )
    .agg(
        total_quantity=("quantity", "sum"),
        total_sales=("line_total", "sum"),
    )
    .sort_values("total_sales", ascending=False)
)
```

## 예상 결과

카테고리와 상품별로 `total_quantity`, `total_sales`가 계산됩니다.

## 성공 기준

카테고리 합계와 완료 주문 상세 합계가 일치하는지 확인합니다.

```python
print(category_sales["total_sales"].sum())
print(completed_sales_items["line_total"].sum())
```

두 값이 같아야 합니다.

## 오류 해결

값이 다르면 필터링 범위와 병합 후 중복 행이 생기지 않았는지 확인합니다.

---

# STEP 10. 월별·고객별 요약표 만들기

## 목적

분석 단위에 맞게 집계 기준을 바꾸는 연습을 합니다.

## 실행

월별 요약:

```python
monthly_summary = (
    completed_order_sales
    .groupby("order_month", as_index=False)
    .agg(
        total_sales=("line_total", "sum"),
        order_count=("order_id", "nunique"),
    )
    .sort_values("order_month")
)
```

고객별 요약:

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
```

필요한 고객 속성만 연결합니다.

```python
customer_sales = customer_sales.merge(
    customers[["customer_id", "city"]],
    on="customer_id",
    how="left",
    validate="one_to_one",
)
```

## 예상 결과

월별·고객별 요약 DataFrame이 생성됩니다.

## 성공 기준

- `order_count`는 `order_id.nunique()` 기준입니다.
- 월별 `total_sales` 합계와 완료 주문 전체 `line_total` 합계가 일치합니다.
- 고객별 `total_sales` 합계도 같은 전체 합계와 일치합니다.

## 오류 해결

월별 합계가 다르면 `order_month`가 결측인 행이 있는지 확인합니다.

```python
completed_order_sales["order_month"].isna().sum()
```

---

# STEP 11. 결과 CSV 저장하고 다시 읽기

## 목적

분석 결과를 파일로 저장하고 실제 저장 결과를 검증합니다.

## 실행

Notebook의 저장 셀을 실행합니다.

생성될 파일은 다음과 같습니다.

```text
reports/ch04_category_sales.csv
reports/ch04_product_sales.csv
reports/ch04_monthly_sales.csv
reports/ch04_customer_sales.csv
```

파일 존재와 크기를 확인합니다.

```python
for path in sorted(REPORT_DIR.glob("ch04_*.csv")):
    print(
        path.name,
        path.exists(),
        path.stat().st_size,
    )
```

한 파일을 다시 읽어 봅니다.

```python
check_category = pd.read_csv(
    REPORT_DIR / "ch04_category_sales.csv"
)

print(check_category.shape)
print(check_category.columns.tolist())
```

## 예상 결과

4개 CSV가 존재하고 파일 크기가 0보다 큽니다.

## 성공 기준

- 네 파일이 모두 존재합니다.
- 다시 읽을 수 있습니다.
- 필요한 컬럼이 유지됩니다.

## 오류 해결

`PermissionError`가 발생하면 해당 CSV를 Excel에서 열어 둔 상태인지 확인하고 닫은 뒤 다시 저장합니다.

---

# STEP 12. LLM 코드 검증하기

## 목적

LLM이 만든 코드가 실행되는지만 보지 않고 실제 분석 기준을 만족하는지 확인합니다.

## 실행

다음 질문을 LLM에 입력해 봅니다.

```text
orders와 order_items를 사용해
completed 주문 기준 월별 금액을 계산하려고 합니다.

다음을 반드시 포함해 주세요.
- line_total = quantity × unit_price
- orders.order_id 고유성 확인
- many-to-one merge + indicator
- 병합 전후 행 수 확인
- 미매칭 확인
- 날짜 변환 실패 확인
- completed만 필터링
- 월별 total_sales와 고유 order_count 계산
- 결과를 회계상 순매출이라고 단정하지 않기
```

LLM이 제안한 코드를 Notebook의 실제 코드와 비교합니다.

## 예상 결과

LLM 답변에서 빠진 검증 항목을 찾을 수 있습니다.

## 성공 기준

다음 질문에 답할 수 있습니다.

```text
실제 컬럼명을 썼는가?
키 관계가 맞는가?
completed 필터가 있는가?
병합 검증이 있는가?
집계 단위가 맞는가?
결과 의미를 과장하지 않았는가?
```

## 오류 해결

LLM 답변을 그대로 실행하지 말고 영향이 큰 수정이나 파일 삭제 명령은 별도로 검토합니다.

---

# STEP 13. 최종 Evidence 작성하기

## 목적

“실습했다”가 아니라 **무엇을 실행했고 무엇을 확인했는지** 남깁니다.

## 실행

아래 템플릿을 복사해 자신의 실제 결과를 작성합니다.

```text
[Chapter 04 Evidence]

1. Notebook
- notebooks/ch04_pandas_basic.ipynb 실행 완료: [예/아니오]

2. 병합 검증
- orders.order_id 중복: [직접 실행 결과]
- orders merge 전 행 수: [결과]
- orders merge 후 행 수: [결과]
- orders merge 미매칭: [결과]
- products merge 전 행 수: [결과]
- products merge 후 행 수: [결과]
- products merge 미매칭: [결과]

3. 계산 범위
- 사용 주문 상태: completed
- line_total 계산식: quantity × unit_price
- 날짜 변환 실패: [결과]

4. 교차 검증
- 완료 주문 상세 line_total 합계: [결과]
- category_sales 합계: [결과]
- monthly_summary 합계: [결과]
- customer_sales 합계: [결과]
- 합계 일치 여부: [PASS/FAIL]

5. 저장 파일
- ch04_category_sales.csv: [존재/없음]
- ch04_product_sales.csv: [존재/없음]
- ch04_monthly_sales.csv: [존재/없음]
- ch04_customer_sales.csv: [존재/없음]

6. LLM 검증
- LLM이 빠뜨린 검증 항목: [직접 작성]

7. 남은 질문
- [직접 작성]
```

## 성공 기준

Evidence의 숫자는 교재 예시가 아니라 **자신이 직접 실행한 결과**로 작성합니다.

---

# 최종 완료 체크리스트

- [ ] Chapter 04 Notebook을 올바른 `.venv` 커널로 실행했다.
- [ ] 4개 CSV를 불러왔다.
- [ ] 실제 컬럼명과 필터 값을 확인했다.
- [ ] `line_total`을 만들었다.
- [ ] orders merge에 `validate`와 `indicator`를 사용했다.
- [ ] 병합 전후 행 수와 미매칭을 확인했다.
- [ ] `completed` 주문만 분석 범위로 사용했다.
- [ ] products merge도 같은 방식으로 검증했다.
- [ ] 카테고리·상품·월·고객 집계를 만들었다.
- [ ] 여러 집계의 `total_sales` 합계를 교차 검증했다.
- [ ] 4개 결과 CSV를 저장하고 다시 확인했다.
- [ ] 고객 결과에서 불필요한 개인정보를 사용하지 않았다.
- [ ] LLM 코드를 실제 데이터 구조와 계산 기준에 대조했다.
- [ ] Evidence를 실제 실행 결과로 작성했다.

---

## 이 장의 핵심

```text
질문
→ 계산 기준
→ 선택·필터
→ 병합 검증
→ 집계
→ 교차 검증
→ 저장 검증
→ 사람 판단
```

pandas 코드를 실행하는 것보다 중요한 것은 **그 코드가 어떤 데이터를 어떤 기준으로 계산했는지 설명하고 검증할 수 있는 것**입니다.

---

## 다음 장

다음은 **5장. 분석 결과를 바꾸는 데이터 전처리**입니다.

Chapter 05에서는 지금까지 발견한 결측치, 중복, 데이터 타입 문제와 이상값 후보를 실제 분석 목적에 맞게 처리합니다.