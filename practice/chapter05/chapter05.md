# 5장 실습. 분석을 믿을 수 있게 만드는 데이터 전처리

> 이 문서는 학생이 그대로 따라 할 수 있도록 작성한 실습 진행 가이드입니다.  
> Chapter 05의 목표는 **데이터를 무조건 깨끗하게 만드는 것이 아니라, 처리 기준과 전후 변화를 직접 검증하고 재현 가능한 전처리 결과를 만드는 것**입니다.

---

## 실습 목표

이 실습을 마치면 다음을 직접 수행할 수 있어야 합니다.

- `data/raw` 원본을 보존하고 `data/processed` 결과를 별도로 만들 수 있습니다.
- 전처리 전에 데이터 크기·결측치·중복 상태를 기록할 수 있습니다.
- 문자열 공백과 빈 문자열을 정리할 수 있습니다.
- 숫자·날짜 변환과 변환 실패를 확인할 수 있습니다.
- 결측치 처리 기준을 설명할 수 있습니다.
- 전체 행 중복과 고유 ID 중복을 구분할 수 있습니다.
- 범주값을 표준화하고 허용되지 않은 값을 다시 확인할 수 있습니다.
- 이상값 후보를 업무 의미와 분리해 검토할 수 있습니다.
- 전처리 후 PK/FK 관계를 재검증할 수 있습니다.
- `order_month`, `order_dayofweek`, `line_total`을 만들 수 있습니다.
- clean CSV와 `ch05_preprocessing_summary.md`를 생성할 수 있습니다.
- `scripts/preprocess_data.py`를 다시 실행해 결과를 재현할 수 있습니다.

---

## 실습에서 사용할 파일

```text
notebooks/ch05_data_preprocessing.ipynb
scripts/preprocess_data.py
src/preprocessing.py

data/raw/
data/processed/
reports/ch05_preprocessing_summary.md
```

이번 실습에서는 다음 4개 원본 CSV를 사용합니다.

```text
customers.csv
products.csv
orders.csv
order_items.csv
```

---

## STEP 1. 프로젝트 루트와 실행 환경 확인

### 목적

Notebook이 실제 저장소 안에서 실행되고 있는지 확인합니다.

### 실행

`notebooks/ch05_data_preprocessing.ipynb`를 열고 첫 셀부터 실행합니다.

Notebook에서는 다음 경로를 준비합니다.

```python
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"
```

### 확인할 결과

다음 항목이 실제 저장소 경로를 가리켜야 합니다.

```text
현재 실행 위치
프로젝트 루트
원본 데이터 폴더
전처리 데이터 폴더
보고서 폴더
```

### 성공 기준

- `data/raw` 경로가 존재합니다.
- `data/processed`와 `reports` 폴더를 만들 수 있습니다.
- Python/Jupyter 커널 오류가 없습니다.

### 오류 해결

경로가 이상하면 먼저 다음을 확인합니다.

```python
from pathlib import Path
print(Path.cwd())
```

Notebook은 저장소 내부에서 실행해야 합니다.

---

## STEP 2. 원본 CSV 4개 불러오기

### 목적

전처리 대상 원본을 확인합니다.

### 실행

```python
customers = pd.read_csv(RAW_DIR / "customers.csv")
products = pd.read_csv(RAW_DIR / "products.csv")
orders = pd.read_csv(RAW_DIR / "orders.csv")
order_items = pd.read_csv(RAW_DIR / "order_items.csv")
```

### 성공 기준

4개 DataFrame이 모두 생성되어야 합니다.

```python
print(customers.shape)
print(products.shape)
print(orders.shape)
print(order_items.shape)
```

파일이 없다면 프로젝트 루트에서 다음을 실행합니다.

```powershell
python scripts/generate_sample_data.py
```

---

## STEP 3. 전처리 전 상태 기록

### 목적

데이터를 바꾸기 전 기준점을 남깁니다.

### 실행

```python
raw_data = {
    "customers": customers,
    "products": products,
    "orders": orders,
    "order_items": order_items,
}

for name, df in raw_data.items():
    print(name)
    print("shape:", df.shape)
    print("missing:", int(df.isna().sum().sum()))
    print("duplicated rows:", int(df.duplicated().sum()))
    print()
```

### 성공 기준

각 데이터셋에 대해 다음을 기록할 수 있어야 합니다.

```text
행 수
열 수
전체 결측 셀 수
전체 중복 행 수
```

> 현재 기본 샘플 데이터는 결측치나 주요 ID 중복이 없을 수 있습니다. 값이 0이라고 해서 실습 오류가 아닙니다.

### Evidence

Notebook에 전처리 전 크기와 품질 요약 결과가 남아 있어야 합니다.

---

## STEP 4. 원본을 복사해 전처리용 DataFrame 만들기

### 목적

원본 DataFrame을 직접 수정하지 않습니다.

### 실행

```python
customers_clean = customers.copy()
products_clean = products.copy()
orders_clean = orders.copy()
order_items_clean = order_items.copy()
```

### 성공 기준

`raw`용 변수와 `clean`용 변수가 분리되어 있어야 합니다.

### 꼭 기억할 것

```text
원본 덮어쓰기 X
복사본에서 처리 O
```

---

## STEP 5. 문자열 공백과 빈 문자열 점검

### 목적

같은 범주가 공백 때문에 다른 값처럼 보이는 문제를 줄입니다.

### 확인

문자열 컬럼의 대표값을 확인합니다.

```python
for col in customers_clean.select_dtypes(include="object").columns:
    print(col)
    print(customers_clean[col].head())
```

### 처리 개념

```python
result[column] = result[column].where(
    result[column].isna(),
    result[column].astype(str).str.strip(),
)
```

빈 문자열은 필요하면 `pd.NA`로 바꿉니다.

### 성공 기준

문자열 처리 후 결측치 수를 다시 확인합니다.

```python
customers_clean.isna().sum()
```

---

## STEP 6. 숫자와 날짜 변환 + 실패 건수 확인

### 목적

`errors="coerce"`를 사용했을 때 새로 생긴 `NaN`/`NaT`를 놓치지 않습니다.

### 숫자 예시

```python
products_clean["price"] = pd.to_numeric(
    products_clean["price"],
    errors="coerce",
)
```

### 날짜 예시

```python
orders_clean["order_date"] = pd.to_datetime(
    orders_clean["order_date"],
    errors="coerce",
)
```

### 검증

```python
print("price 변환 실패/결측:", products_clean["price"].isna().sum())
print("order_date 변환 실패/결측:", orders_clean["order_date"].isna().sum())
print("최소 주문일:", orders_clean["order_date"].min())
print("최대 주문일:", orders_clean["order_date"].max())
```

### 성공 기준

단순히 코드가 실행되는 것이 아니라 **변환 실패 건수와 날짜 범위를 확인**해야 합니다.

---

## STEP 7. 결측치 처리 기준 확인

### 목적

결측치를 자동 삭제하거나 자동 대체하지 않고 처리 이유를 이해합니다.

### 나이 중앙값 대체 예시

```python
age_median = customers_clean["age"].median()
customers_clean["age"] = customers_clean["age"].fillna(age_median)
```

### 도시 별도 범주 예시

```python
customers_clean["city"] = customers_clean["city"].fillna("Unknown")
```

### 성공 기준

다음 질문에 답할 수 있어야 합니다.

```text
왜 중앙값을 사용했는가?
왜 Unknown을 유지했는가?
몇 건이 바뀌었는가?
분석 결과에 어떤 영향을 줄 수 있는가?
```

### 주의

고유 ID, 핵심 날짜, 금액, 상태값은 근거 없이 대표값으로 대체하지 않습니다.

---

## STEP 8. 전체 행 중복과 키 중복 확인

### 전체 중복

```python
for name, df in raw_data.items():
    print(name, df.duplicated().sum())
```

### 고유 ID 중복

```python
key_columns = {
    "customers": "customer_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "order_item_id",
}

for name, key in key_columns.items():
    df = raw_data[name]
    print(name, key, df[key].duplicated().sum())
```

### 성공 기준

다음 차이를 설명할 수 있어야 합니다.

```text
전체 행 중복
고유 ID 중복
관계용 ID의 자연스러운 반복
```

예: `order_items.order_id` 반복은 한 주문에 여러 상품이 있을 수 있으므로 자연스러울 수 있습니다.

---

## STEP 9. 주문 상태 범주값 확인 및 표준화

### 먼저 현재 값 확인

```python
orders_clean["order_status"].value_counts(dropna=False)
```

### 실습 대표 상태

```text
completed
cancelled
refunded
```

### 표준화 예시

```python
status_map = {
    "complete": "completed",
    "완료": "completed",
    "cancel": "cancelled",
    "취소": "cancelled",
    "refund": "refunded",
    "환불": "refunded",
}

orders_clean["order_status"] = (
    orders_clean["order_status"].replace(status_map)
)
```

### 검증

```python
orders_clean["order_status"].value_counts(dropna=False)
```

### 성공 기준

표준화 후 예상하지 못한 값이 남는지 확인합니다.

---

## STEP 10. 이상값 후보 확인

### 목적

이상값 후보와 실제 오류를 구분합니다.

### 확인 예시

```python
print(customers_clean.loc[(customers_clean["age"] < 0) | (customers_clean["age"] > 120)])
print(products_clean.loc[products_clean["price"] <= 0])
print(order_items_clean.loc[order_items_clean["quantity"] <= 0])
print(order_items_clean.loc[order_items_clean["unit_price"] <= 0])
```

### 해석

```text
0원 상품 = 무조건 오류 X
음수 수량 = 무조건 오류 X
```

실제 업무에서는 증정품, 반품 같은 의미일 수 있습니다.

### 성공 기준

삭제 전에 **업무 의미 확인이 필요하다**는 것을 설명할 수 있어야 합니다.

---

## STEP 11. 파생 컬럼 만들기

### 주문 월

```python
orders_clean["order_month"] = (
    orders_clean["order_date"]
    .dt.to_period("M")
    .astype(str)
)
```

### 주문 요일

```python
orders_clean["order_dayofweek"] = (
    orders_clean["order_date"].dt.day_name()
)
```

### 주문 상세 금액

```python
order_items_clean["line_total"] = (
    order_items_clean["quantity"]
    * order_items_clean["unit_price"]
)
```

### 성공 기준

`line_total`은 **주문 상세 한 행의 수량 × 단가**라는 의미를 설명할 수 있어야 합니다.

> 전체 `line_total` 합계를 곧바로 매출 또는 순매출이라고 부르지 않습니다.

---

## STEP 12. 전처리 후 파일 관계 재검증

### 목적

전처리로 일부 행이 제외된 뒤에도 참조 관계가 유지되는지 확인합니다.

검사 관계는 다음 세 가지입니다.

```text
orders.customer_id → customers.customer_id
order_items.order_id → orders.order_id
order_items.product_id → products.product_id
```

공통 함수 사용 예시:

```python
from src.preprocessing import validate_relationships

processed_data = {
    "customers": customers_clean,
    "products": products_clean,
    "orders": orders_clean,
    "order_items": order_items_clean,
}

relationship_checks = validate_relationships(processed_data)
relationship_checks
```

### 성공 기준

현재 정상 샘플 데이터에서는 `invalid_count`가 모두 0인 것을 기대합니다.

0보다 크다면 바로 삭제하지 말고 원인을 확인합니다.

---

## STEP 13. processed CSV 저장

### 저장할 파일

```text
data/processed/customers_clean.csv
data/processed/products_clean.csv
data/processed/orders_clean.csv
data/processed/order_items_clean.csv
```

### 확인

```python
from pathlib import Path

for path in sorted(Path("data/processed").glob("*_clean.csv")):
    print(path, path.exists(), path.stat().st_size)
```

### 성공 기준

4개 파일이 실제로 존재하고 크기가 0보다 커야 합니다.

---

## STEP 14. 반복 실행 스크립트 실행

Notebook으로 전처리 흐름을 이해했다면 프로젝트 루트 터미널에서 실행합니다.

```powershell
python scripts/preprocess_data.py
```

### 예상 결과

터미널에 다음 정보가 출력됩니다.

```text
전처리 완료
전처리 전후 데이터 크기
중복 점검 결과
파일 간 관계 점검 결과
저장된 전처리 파일
요약 보고서 경로
```

그리고 다음 보고서가 생성됩니다.

```text
reports/ch05_preprocessing_summary.md
```

### 성공 기준

- 스크립트가 오류 없이 종료됩니다.
- 4개 clean CSV가 존재합니다.
- 전처리 보고서가 존재합니다.
- 관계 검증 결과를 확인할 수 있습니다.

---

## STEP 15. 저장 결과 다시 읽어 검증

### 목적

저장 성공과 데이터 내용 정상은 같은 말이 아닙니다.

```python
customers_check = pd.read_csv(
    "data/processed/customers_clean.csv"
)
orders_check = pd.read_csv(
    "data/processed/orders_clean.csv"
)
```

### 확인

```python
print(customers_check.shape)
print(customers_check.columns.tolist())
print(orders_check.shape)
print(orders_check.columns.tolist())
```

CSV에서는 날짜가 다시 문자열로 읽힐 수 있으므로 필요하면 다음처럼 변환합니다.

```python
orders_check["order_date"] = pd.to_datetime(
    orders_check["order_date"],
    errors="coerce",
)
```

### 성공 기준

- 예상 컬럼이 모두 존재합니다.
- 주요 ID 구조가 유지됩니다.
- 날짜 재변환 실패 여부를 확인할 수 있습니다.

---

## STEP 16. 전처리 보고서 검토

다음 파일을 엽니다.

```text
reports/ch05_preprocessing_summary.md
```

다음 항목이 설명되어 있는지 확인합니다.

```text
전처리 결과 파일
전처리 전후 데이터 크기
중복 점검
관계 점검
문자열·숫자·날짜 처리 기준
결측치 처리 기준
이상값 처리 기준
파생 컬럼
업무 적용 시 한계
```

### 성공 기준

다음처럼 구체적으로 설명할 수 있어야 합니다.

```text
무엇을 바꿨는가?
왜 바꿨는가?
몇 건이 영향을 받았는가?
전처리 후 무엇을 다시 검증했는가?
```

---

## STEP 17. LLM 전처리 제안 검증

LLM에는 원본 고객 행 대신 구조와 요약 정보를 제공합니다.

예시:

```text
customers 데이터 품질 요약
- rows: 150
- customer_id missing/duplicate: 0 / 0
- age missing: 3
- city missing: 2

age 결측치 처리 후보를 비교해 주세요.
각 방법의 장단점과 처리 전후 검증 항목을 제안해 주세요.
실제 업무 의미를 확인하지 않은 값은 단정하지 마세요.
```

LLM 답변을 받은 뒤 다음을 사람이 확인합니다.

```text
raw를 덮어쓰는가?
변환 실패를 확인하는가?
결측 처리 근거가 있는가?
키 중복을 자동 삭제하지 않는가?
이상값을 자동 삭제하지 않는가?
관계를 재검증하는가?
변경 내역을 기록하는가?
```

---

## 최종 Evidence 작성

실습 완료 후 다음 내용을 기록합니다.

```markdown
## Chapter 05 완료 Evidence

- Notebook 실행: PASS / FAIL
- raw 원본 보존 확인: PASS / FAIL
- processed CSV 4개 생성: PASS / FAIL
- 숫자/날짜 변환 실패 점검: PASS / FAIL
- 전체 중복/키 중복 점검: PASS / FAIL
- PK/FK 관계 검증: PASS / FAIL
- 파생 컬럼 확인: PASS / FAIL
- preprocess_data.py 재실행: PASS / FAIL
- ch05_preprocessing_summary.md 생성: PASS / FAIL
- 저장 결과 재확인: PASS / FAIL

### 내가 적용한 전처리 기준
- 

### 전처리 전후 달라진 점
- 

### 아직 업무 확인이 필요한 항목
- 
```

---

## 최종 완료 체크리스트

- [ ] 원본 `data/raw`를 덮어쓰지 않았습니다.
- [ ] 전처리 전 데이터 상태를 기록했습니다.
- [ ] 문자열 처리 후 결측치를 다시 확인했습니다.
- [ ] 숫자·날짜 변환 실패를 확인했습니다.
- [ ] 결측치 처리 기준을 설명할 수 있습니다.
- [ ] 전체 중복과 키 중복을 구분했습니다.
- [ ] 범주값 표준화 결과를 확인했습니다.
- [ ] 이상값 후보를 자동 오류로 단정하지 않았습니다.
- [ ] 전처리 후 PK/FK 관계를 재검증했습니다.
- [ ] `line_total`의 의미를 설명할 수 있습니다.
- [ ] clean CSV 4개를 생성했습니다.
- [ ] `reports/ch05_preprocessing_summary.md`를 확인했습니다.
- [ ] `python scripts/preprocess_data.py`로 재현했습니다.
- [ ] 저장한 CSV를 다시 읽어 구조를 검증했습니다.
- [ ] LLM 제안을 실제 데이터·업무 기준과 비교했습니다.

---

## 다음 장 준비

Chapter 06에서는 이번 장에서 만든 `data/processed/*.csv`를 사용합니다.

다음 장으로 넘어가기 전에 최소한 다음 두 가지는 반드시 완료되어야 합니다.

```text
processed CSV 4개 생성
전처리 요약 보고서 생성
```

Chapter 06에서는 전처리된 데이터에 대해 **질문 → 지표 → 계산 범위 → 결과 → 해석 한계**의 EDA 흐름을 진행합니다.