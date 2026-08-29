# 3장 실습. 데이터의 첫인상 읽기

> 이 문서는 학생이 그대로 따라 할 수 있도록 작성한 실습 진행 가이드입니다.  
> Chapter 03의 목표는 **CSV를 읽은 뒤 바로 분석하지 않고, 데이터 구조와 품질을 먼저 검증하는 습관**을 만드는 것입니다.

---

## 실습 목표

이 실습을 마치면 다음을 직접 수행할 수 있어야 합니다.

- 4개 CSV 파일의 존재 여부를 확인할 수 있습니다.
- `pd.read_csv()`로 CSV를 DataFrame으로 불러올 수 있습니다.
- `shape`, `head()`, `tail()`, `columns`, `info()`, `dtypes`를 확인할 수 있습니다.
- 결측치와 전체 행 중복을 확인할 수 있습니다.
- 주요 ID의 결측·중복 여부를 검사할 수 있습니다.
- 숫자형·범주형·날짜 컬럼의 기본 상태를 확인할 수 있습니다.
- 여러 CSV의 연결 대상 ID가 실제로 존재하는지 검사할 수 있습니다.
- LLM에 원본 데이터를 그대로 넣지 않고 구조 요약만 제공할 수 있습니다.
- LLM의 설명을 실제 실행 결과와 비교해 검증할 수 있습니다.

---

## 사용할 파일

- Notebook: `notebooks/ch03_data_overview.ipynb`
- 고객 데이터: `data/raw/customers.csv`
- 상품 데이터: `data/raw/products.csv`
- 주문 데이터: `data/raw/orders.csv`
- 주문 상세: `data/raw/order_items.csv`
- 샘플 데이터 생성: `scripts/generate_sample_data.py`

공식 저장소:

https://github.com/GilbertMoon/llm-data-analysis-course

---

# STEP 1. Chapter 02 환경이 준비되었는지 확인하기

## 목적

Chapter 03은 pandas와 Notebook이 정상 연결되어 있어야 진행할 수 있습니다.

## 실행

프로젝트 루트의 VS Code 터미널에서 확인합니다.

```powershell
python -c "import sys; print(sys.executable)"
```

출력 경로에 프로젝트의 `.venv`가 포함되어 있는지 확인합니다.

Notebook에서는 다음도 확인합니다.

```python
from pathlib import Path
import sys

print(sys.executable)
print(Path.cwd())
```

## 예상 결과

- Python 실행 파일이 프로젝트 `.venv`를 가리킵니다.
- Notebook이 저장소 안에서 실행되고 있습니다.

## 성공 기준

- [ ] `.venv` Python을 사용 중입니다.
- [ ] `notebooks/ch03_data_overview.ipynb`를 열었습니다.
- [ ] 첫 셀 실행 시 오류가 없습니다.

## 오류가 나면

`ModuleNotFoundError`가 발생하면 Chapter 02로 돌아가 Notebook 커널과 패키지를 설치한 `.venv`가 같은지 확인합니다.

---

# STEP 2. 프로젝트 루트와 데이터 폴더 찾기

## 목적

상대경로를 추측하지 않고 실제 프로젝트 구조를 기준으로 데이터 위치를 찾습니다.

## 실행

Notebook의 `find_project_root()` 셀을 실행합니다.

핵심 코드는 다음과 같습니다.

```python
from pathlib import Path


def find_project_root(start: Path) -> Path:
    start = start.resolve()

    for candidate in [start, *start.parents]:
        if (
            (candidate / "data" / "raw").exists()
            and (candidate / "book").exists()
        ):
            return candidate

    raise FileNotFoundError(
        "프로젝트 루트를 찾지 못했습니다. "
        "Notebook을 저장소 안에서 실행해 주세요."
    )


PROJECT_ROOT = find_project_root(Path.cwd())
DATA_DIR = PROJECT_ROOT / "data" / "raw"

print(PROJECT_ROOT)
print(DATA_DIR)
```

## 예상 결과

프로젝트 루트와 `data/raw` 경로가 출력됩니다.

## 성공 기준

- [ ] `PROJECT_ROOT`가 `llm-data-analysis-course`를 가리킵니다.
- [ ] `DATA_DIR`가 `data/raw`를 가리킵니다.

## 오류가 나면

Notebook을 저장소 밖으로 복사해 실행하지 않았는지 확인합니다. VS Code에서 저장소 루트 폴더를 다시 연 뒤 Notebook을 실행합니다.

---

# STEP 3. CSV 파일 4개가 실제로 있는지 확인하기

## 목적

CSV를 읽기 전에 파일 존재 여부부터 확인합니다.

## 실행

```python
expected_files = [
    "customers.csv",
    "products.csv",
    "orders.csv",
    "order_items.csv",
]

file_check = {
    filename: (DATA_DIR / filename).exists()
    for filename in expected_files
}

file_check
```

## 예상 결과

네 파일이 모두 `True`입니다.

## 성공 기준

- [ ] `customers.csv: True`
- [ ] `products.csv: True`
- [ ] `orders.csv: True`
- [ ] `order_items.csv: True`

## 오류가 나면

하나라도 `False`라면 프로젝트 루트 터미널에서 실행합니다.

```powershell
python scripts/generate_sample_data.py
```

그다음 파일 존재 여부를 다시 확인합니다.

---

# STEP 4. CSV를 DataFrame으로 불러오기

## 목적

4개 CSV를 pandas DataFrame으로 불러옵니다.

## 실행

```python
import pandas as pd

customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")
order_items = pd.read_csv(DATA_DIR / "order_items.csv")

datasets = {
    "customers": customers,
    "products": products,
    "orders": orders,
    "order_items": order_items,
}
```

## 예상 결과

오류 없이 네 DataFrame이 생성됩니다.

## 성공 기준

- [ ] `type(customers)`가 DataFrame입니다.
- [ ] 네 DataFrame을 `datasets`에 묶었습니다.

## 오류가 나면

`FileNotFoundError`이면 STEP 2·3의 경로와 파일 존재 여부를 다시 확인합니다.

---

# STEP 5. `shape`로 데이터 규모 확인하기

## 목적

각 데이터셋의 행과 열 개수를 확인합니다.

## 실행

```python
for name, df in datasets.items():
    print(name, df.shape)
```

기본 샘플 데이터에서는 다음과 비슷한 결과가 나올 수 있습니다.

```text
customers    (150, 6)
products     (100, 4)
orders       (300, 5)
order_items  (764, 5)
```

## 예상 결과

각 데이터셋의 `(행, 열)`이 출력됩니다.

## 성공 기준

- [ ] 네 데이터셋의 행 수를 기록했습니다.
- [ ] 네 데이터셋의 열 수를 기록했습니다.
- [ ] `order_items`가 왜 `orders`보다 많을 수 있는지 설명할 수 있습니다.

## 오류가 나면

예시 숫자와 다르더라도 오류라고 단정하지 않습니다. 샘플 생성 스크립트나 데이터가 바뀌었는지 먼저 확인하고 **현재 실행 결과를 기준으로 기록**합니다.

---

# STEP 6. `head()`와 `tail()`로 실제 값 보기

## 목적

컬럼명과 값의 형태를 눈으로 확인합니다.

## 실행

```python
customers.head()
customers.tail()
products.head()
orders.head()
order_items.head()
```

## 예상 결과

표 형태로 데이터 일부가 표시됩니다.

## 확인할 것

```text
날짜처럼 보이는 컬럼
숫자처럼 보이는 컬럼
ID처럼 보이는 컬럼
표기가 이상한 값
```

## 성공 기준

- [ ] 최소 4개 DataFrame의 `head()`를 확인했습니다.
- [ ] `customers.tail()`도 확인했습니다.
- [ ] 앞 5행만 보고 전체 데이터가 정상이라고 판단하지 않았습니다.

## 오류가 나면

DataFrame 변수가 없다는 오류가 나오면 STEP 4 셀부터 다시 실행합니다.

---

# STEP 7. 컬럼과 데이터 타입 확인하기

## 목적

실제 컬럼명과 타입을 확인합니다.

## 실행

```python
for name, df in datasets.items():
    print(f"\n===== {name} =====")
    print(list(df.columns))
    print(df.dtypes)
```

그리고 `info()`도 확인합니다.

```python
customers.info()
```

## 예상 결과

컬럼명, Non-Null Count, 데이터 타입이 출력됩니다.

## 성공 기준

- [ ] 실제 컬럼명을 확인했습니다.
- [ ] 날짜처럼 보이지만 문자열인 컬럼을 찾았습니다.
- [ ] ID와 일반 숫자형 변수를 구분했습니다.

## 오류가 나면

LLM이 제안한 컬럼명이 실제 컬럼과 다르면 LLM 코드를 고치는 것이 우선입니다. 실제 데이터를 LLM 답변에 맞추려고 하지 않습니다.

---

# STEP 8. 결측치 확인하기

## 목적

어느 컬럼에 값이 비어 있는지 확인합니다.

## 실행

```python
for name, df in datasets.items():
    print(f"\n[{name}]")
    print(df.isna().sum())
```

비율까지 보고 싶다면 다음을 실행합니다.

```python
(customers.isna().mean() * 100).round(2)
```

## 예상 결과

기본 샘플 데이터에서는 주요 컬럼의 결측치가 0일 수 있습니다.

## 성공 기준

- [ ] 결측치 개수를 확인했습니다.
- [ ] 결측치가 없더라도 직접 확인했습니다.
- [ ] 발견 즉시 삭제하지 않았습니다.

## 오류가 나면

결측치가 예상과 다르면 현재 데이터가 재생성되었거나 수정되었는지 확인하고 실제 결과를 기록합니다.

---

# STEP 9. 전체 행 중복과 주요 ID 중복 확인하기

## 목적

전체 행 중복과 업무 ID 중복을 구분합니다.

## 실행

전체 중복:

```python
for name, df in datasets.items():
    print(name, df.duplicated().sum())
```

주요 ID:

```python
key_columns = {
    "customers": "customer_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "order_item_id",
}

for name, key in key_columns.items():
    df = datasets[name]
    print(
        name,
        "missing:", df[key].isna().sum(),
        "duplicated:", df[key].duplicated().sum(),
    )
```

## 예상 결과

기본 샘플에서는 주요 ID의 결측과 중복이 0입니다.

## 성공 기준

- [ ] 전체 행 중복을 확인했습니다.
- [ ] 주요 ID 중복을 별도로 확인했습니다.
- [ ] `order_items.order_id`가 반복될 수 있는 이유를 설명할 수 있습니다.

## 오류가 나면

중복 숫자가 0보다 크다고 바로 삭제하지 않습니다. 그 컬럼이 고유 ID인지 연결용 FK인지 먼저 판단합니다.

---

# STEP 10. 숫자형·범주형 컬럼 확인하기

## 목적

숫자형 값의 범위와 범주형 값의 종류를 확인합니다.

## 실행

숫자형:

```python
customers[["age"]].describe()
products[["price"]].describe()
order_items[["quantity", "unit_price"]].describe()
```

범주형:

```python
customers["city"].value_counts(dropna=False)
products["category"].value_counts(dropna=False)
orders["order_status"].value_counts(dropna=False)
```

## 예상 결과

숫자형은 최소·최대·평균·중앙값을, 범주형은 값별 빈도를 확인할 수 있습니다.

## 성공 기준

- [ ] `age`, `price`, `quantity`, `unit_price` 범위를 확인했습니다.
- [ ] `city`, `category`, `order_status` 빈도를 확인했습니다.
- [ ] ID를 평균값 분석 대상으로 사용하지 않았습니다.

## 오류가 나면

컬럼 이름이 다르면 `list(df.columns)`로 실제 컬럼명을 먼저 다시 확인합니다.

---

# STEP 11. 날짜 컬럼 변환 가능 여부 확인하기

## 목적

날짜처럼 보이는 문자열이 실제 날짜로 변환 가능한지 검사합니다.

## 실행

```python
orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    errors="coerce",
)

print("변환 실패:", orders["order_date"].isna().sum())
print("가장 빠른 주문일:", orders["order_date"].min())
print("가장 최근 주문일:", orders["order_date"].max())
```

가입일도 별도로 확인합니다.

```python
signup_check = pd.to_datetime(
    customers["signup_date"],
    errors="coerce",
)

print("가입일 변환 실패:", signup_check.isna().sum())
```

## 예상 결과

기본 샘플에서는 날짜 변환 실패가 0입니다.

## 성공 기준

- [ ] 날짜 타입으로 변환했습니다.
- [ ] 변환 실패 건수를 확인했습니다.
- [ ] 최소·최대 날짜를 기록했습니다.

## 오류가 나면

`errors="coerce"`는 잘못된 날짜를 `NaT`로 바꾸므로 코드가 끝났다는 사실만 보지 말고 실패 건수를 반드시 확인합니다.

---

# STEP 12. CSV 간 키 관계 검증하기

## 목적

연결하려는 ID가 부모 데이터에 실제로 존재하는지 확인합니다.

## 실행

```python
invalid_customers = orders.loc[
    ~orders["customer_id"].isin(customers["customer_id"])
]

invalid_orders = order_items.loc[
    ~order_items["order_id"].isin(orders["order_id"])
]

invalid_products = order_items.loc[
    ~order_items["product_id"].isin(products["product_id"])
]

print("없는 customer_id:", len(invalid_customers))
print("없는 order_id:", len(invalid_orders))
print("없는 product_id:", len(invalid_products))
```

## 예상 결과

기본 샘플에서는 세 값 모두 0입니다.

## 성공 기준

- [ ] `orders.customer_id → customers.customer_id`를 확인했습니다.
- [ ] `order_items.order_id → orders.order_id`를 확인했습니다.
- [ ] `order_items.product_id → products.product_id`를 확인했습니다.

## 오류가 나면

0보다 크다면 바로 삭제하지 말고 다음을 확인합니다.

```text
파일 누락
ID 데이터 타입 차이
앞뒤 공백
생성·수집 시점 차이
```

---

# STEP 13. 반복 점검 함수를 실행하기

## 목적

같은 구조 검사를 여러 DataFrame에 반복 적용합니다.

## 실행

Notebook의 `check_data_overview()` 함수를 실행합니다.

예:

```python
def check_data_overview(name, df, key_column=None):
    print(f"===== {name} =====")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print("dtypes:")
    print(df.dtypes)
    print("missing:")
    print(df.isna().sum())
    print("duplicated rows:", df.duplicated().sum())

    if key_column is not None:
        print("key missing:", df[key_column].isna().sum())
        print("key duplicated:", df[key_column].duplicated().sum())
```

## 예상 결과

네 DataFrame의 구조 점검 결과가 같은 형식으로 출력됩니다.

## 성공 기준

- [ ] 네 데이터셋에 함수를 적용했습니다.
- [ ] 반복 코드를 함수로 만드는 이유를 이해했습니다.

## 오류가 나면

함수 정의 셀을 먼저 실행했는지 확인합니다. Notebook은 실행 순서에 따라 변수와 함수 상태가 달라질 수 있습니다.

---

# STEP 14. LLM에게 구조 요약만 제공하기

## 목적

원본 개인정보나 상세 거래값을 전달하지 않고도 LLM의 도움을 받는 방법을 연습합니다.

## 실행

실제 실행 결과를 아래 형식으로 정리합니다.

```text
customers.csv 구조 요약

행/열: [실제 shape]
컬럼: [실제 columns]
데이터 타입: [실제 dtypes]
결측치: [실제 결과]
전체 중복: [실제 결과]
customer_id 중복: [실제 결과]

분석 전에 추가로 확인해야 할 점을 알려 주세요.
확인하지 않은 내용은 단정하지 말고,
추정과 실제 확인이 필요한 항목을 구분해 주세요.
```

## 예상 결과

LLM이 추가 점검 항목을 제안합니다.

## 성공 기준

- [ ] 실제 고객 이름이나 전체 원본 행을 보내지 않았습니다.
- [ ] 예시 숫자가 아니라 직접 실행한 결과를 사용했습니다.
- [ ] LLM 제안 중 실제 데이터에서 확인한 항목을 표시했습니다.

## 오류가 나면

LLM이 존재하지 않는 컬럼을 전제로 설명하면 실제 `columns` 결과를 기준으로 수정합니다.

---

# STEP 15. 최종 Evidence 기록하기

## 목적

이번 장의 완료 상태를 다시 확인할 수 있도록 결과를 남깁니다.

## 실행

아래 내용을 Notebook Markdown 셀 또는 개인 실습 노트에 기록합니다.

```text
[Chapter 03 Evidence]

1. CSV 파일 존재 여부
- customers.csv: PASS / FAIL
- products.csv: PASS / FAIL
- orders.csv: PASS / FAIL
- order_items.csv: PASS / FAIL

2. 데이터 규모
- customers: __ rows × __ cols
- products: __ rows × __ cols
- orders: __ rows × __ cols
- order_items: __ rows × __ cols

3. 품질 점검
- 주요 ID 결측: __
- 주요 ID 중복: __
- 전체 행 중복: __
- 날짜 변환 실패: __

4. 관계 검증
- 없는 customer_id: __
- 없는 order_id: __
- 없는 product_id: __

5. LLM 활용
- 요청 목적: __
- 실제 반영: __
- 사람이 검증한 항목: __
```

## 성공 기준

- [ ] 네 CSV의 구조를 모두 확인했습니다.
- [ ] 결측·중복·ID·날짜·관계 검증 결과를 기록했습니다.
- [ ] LLM 결과와 실제 데이터 검증을 구분해 기록했습니다.

---

## Chapter 03 완료 체크리스트

- [ ] CSV 4개 존재 확인
- [ ] DataFrame 4개 로딩
- [ ] `shape` 확인
- [ ] `head()` / `tail()` 확인
- [ ] `columns` / `info()` / `dtypes` 확인
- [ ] 결측치 확인
- [ ] 전체 행 중복 확인
- [ ] 주요 ID 결측·중복 확인
- [ ] 숫자형 범위 확인
- [ ] 범주형 빈도 확인
- [ ] 날짜 변환 실패와 범위 확인
- [ ] CSV 간 ID 관계 검증
- [ ] LLM 구조 설명 검증
- [ ] 최종 Evidence 작성

---

## 다음 장

다음은 **4장. pandas로 데이터에 질문하기**입니다.

Chapter 04에서는 이번 장에서 확인한 DataFrame을 대상으로 컬럼 선택, 조건 필터링, 정렬, 파생 컬럼, 병합, 기본 집계를 직접 수행합니다.