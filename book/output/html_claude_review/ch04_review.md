# ch04 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch04_pandas_basic.md`

---

## 검토 지침 (Codex Prompt Format)

아래 각 항목은 `[섹션명]` 위치를 기준으로 문제를 설명하고, 구체적인 수정/보완 방향을 제시합니다.  
**[필수 수정]** = 학습에 직접적 혼란을 야기하는 항목  
**[보완 권장]** = 추가 시 학습 효과가 크게 향상되는 항목

---

## 1. 필수 수정 항목

---

### [1-1] Notebook 파일명 불일치 — [섹션 5]

**문제**  
섹션 5에서 "이번 장의 전체 실습은 다음 Notebook에서 진행합니다"라며 안내하는 파일명이:

```
notebooks/ch04_pandas_basic_analysis.ipynb
```

그런데 실제 workspace에 존재하는 파일명은:

```
notebooks/ch04_pandas_basic.ipynb
```

두 이름이 다르다. 학생이 해당 파일을 찾지 못해 실습을 시작하지 못하는 상황이 발생한다.

**수정 지시**  
섹션 5의 Notebook 경로를 실제 파일명과 일치하도록 수정한다:

```
notebooks/ch04_pandas_basic.ipynb
```

---

### [1-2] 수업 시간 구성표 합계와 본문 불일치 — [수업 시간 구성 표]

**문제**  
수업 시간 구성 표의 권장 시간 합계: 40+35+35+50+50+30 = 240분 = 4시간.  
그런데 본문에 "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"라고 적혀 있다. ch01~ch03과 동일한 구조적 오류이며, ch04에서는 격차가 1시간으로 가장 크다.

**수정 지시**  
다음 두 방법 중 하나를 선택해 수정한다:

- 방법 A: 표의 항목 시간을 조정해 합계를 180분(3시간)으로 맞춘다.
- 방법 B: 본문을 "기본 수업은 약 4시간을 기준으로 구성되어 있습니다"로 수정한다.

ch01~ch04 모두 동일한 오류가 반복되고 있으므로 전체 장에서 일괄 검토가 필요하다.

---

### [1-3] 데이터 경로 설정 결론 미제시 — [섹션 5.2]

**문제**  
ch03과 동일하게 `data_dir = Path("data/raw")`와 `data_dir = Path("../data/raw")` 두 가지를 제시하고, 어떤 경로를 써야 하는지 결론이 없다. ch03 리뷰에서 이미 자동 감지 패턴을 제안했으며, ch04에서도 같은 문제가 반복된다.

**수정 지시**  
ch03 리뷰 [1-2]와 동일한 자동 감지 패턴으로 교체하거나, 다음 안내를 추가한다:

```
이 교재의 Notebook은 프로젝트 루트에서 실행하는 것을 권장합니다.
data/raw 경로로 파일을 찾지 못하면 ../data/raw를 사용합니다.
경로 자동 감지 방법은 ch03 5.3절을 참고하세요.
```

---

### [1-4] `mkdir(exist_ok=True)` 개념 미설명 — [섹션 5.1]

**문제**  
섹션 5.1에서 `report_dir.mkdir(exist_ok=True)` 코드가 등장하는데, 이 코드가 무엇을 하는지 설명이 없다. 비전공자에게는 디렉토리(폴더) 생성 명령이 낯설 수 있다.

**수정 지시**  
해당 코드 아래에 다음 설명을 추가한다:

```
mkdir()은 폴더를 만드는 명령입니다.
exist_ok=True는 폴더가 이미 존재해도 오류를 내지 않도록 합니다.
이 코드를 실행하면 프로젝트 안에 reports/ 폴더가 생성됩니다.
폴더가 이미 있으면 아무 일도 일어나지 않습니다.
```

---

### [1-5] `how="left"` vs `how="inner"` 차이 설명 불충분 — [섹션 3.7]

**문제**  
섹션 3.7에서 "이번 장에서는 기본적으로 `how="left"`를 사용합니다"라고만 언급하고, `left`와 `inner`의 실질적 차이를 설명하지 않는다. 학생이 나중에 merge 결과에서 예상치 못한 데이터 누락을 경험했을 때 원인을 이해하지 못한다.

**수정 지시**  
섹션 3.7의 merge 설명에 다음 비교 표를 추가한다:

| how 옵션 | 동작 | 결과 |
|---------|------|------|
| `"left"` | 왼쪽 DataFrame의 모든 행 유지 | 오른쪽에 매칭 없으면 NaN |
| `"inner"` | 양쪽 모두에 있는 행만 유지 | 매칭 안 되는 행 제거 |
| `"outer"` | 양쪽의 모든 행 유지 | 매칭 없는 쪽 NaN |
| `"right"` | 오른쪽 DataFrame의 모든 행 유지 | 왼쪽에 매칭 없으면 NaN |

```
이 교재에서는 how="left"를 기본으로 사용합니다.
order_items를 기준으로 products 정보를 가져오는 것이므로,
products에 없는 product_id가 있어도 order_items 행은 보존됩니다.
병합 후 NaN이 발생한 경우 키 관계를 다시 확인해야 합니다.
```

---

### [1-6] `agg()` named aggregation 문법 미설명 — [섹션 5.14, 5.17, 5.18]

**문제**  
섹션 5.14에서 다음 문법이 처음 등장한다:
```python
.agg(
    total_quantity=("quantity", "sum"),
    total_sales=("line_total", "sum")
)
```
이 형식(named aggregation)은 pandas 1.1 이후에 도입된 것으로, 기초 pandas 학습 자료에서는 잘 나오지 않는다. 형식이 왜 이렇게 생겼는지 설명이 없다.

**수정 지시**  
섹션 5.14 또는 처음 `agg()`가 등장하는 위치 앞에 다음 설명을 추가한다:

```
agg() 함수로 여러 집계를 한 번에 계산하기

.agg(새컬럼명=("원본컬럼명", "집계함수")) 형식으로 작성합니다.

예시:
.agg(
    total_quantity=("quantity", "sum"),   # quantity 합계를 total_quantity로 저장
    total_sales=("line_total", "sum")     # line_total 합계를 total_sales로 저장
)

자주 사용하는 집계 함수:
- "sum": 합계
- "mean": 평균
- "count": 개수 (결측치 포함)
- "nunique": 고유값 개수
- "min", "max": 최솟값, 최댓값
```

---

### [1-7] `dt.to_period("M").astype(str)` 미설명 — [섹션 5.16]

**문제**  
섹션 5.16에서 주문 월 컬럼을 만드는 코드:
```python
order_sales["order_month"] = order_sales["order_date"].dt.to_period("M").astype(str)
```
`.dt` 속성, `to_period("M")`, `astype(str)`가 한 줄에 연결되어 있고 각각 무엇인지 설명이 없다.

**수정 지시**  
해당 코드 앞에 단계별 설명을 추가한다:

```python
# .dt는 날짜 타입 컬럼에서 날짜 관련 속성을 사용할 때 붙이는 접두사입니다
# .dt.year: 연도, .dt.month: 월, .dt.day: 일 등을 추출할 수 있습니다

# 방법 1: to_period("M")으로 연월 표현 (예: "2024-01")
order_sales["order_month"] = order_sales["order_date"].dt.to_period("M").astype(str)

# 방법 2: 연도와 월을 직접 조합 (더 직관적)
# order_sales["order_month"] = (
#     order_sales["order_date"].dt.year.astype(str) + "-" +
#     order_sales["order_date"].dt.month.astype(str).str.zfill(2)
# )
```

```
astype(str)은 Period 타입을 문자열("2024-01" 형태)로 변환합니다.
groupby()에서 월별로 묶으려면 문자열 형태가 더 편리합니다.
```

---

### [1-8] `as_index=False` 매개변수 미설명 — [섹션 5.13, 5.14, 5.17, 5.18]

**문제**  
`groupby("category", as_index=False)`가 여러 곳에서 반복 등장하는데, `as_index=False`가 무엇인지 설명이 없다. 이를 사용하지 않으면 groupby 기준 컬럼이 인덱스가 되어 이후 코드 작성에 차이가 생긴다.

**수정 지시**  
처음 `as_index=False`가 등장하는 섹션 5.13에 다음 설명을 추가한다:

```
as_index=False를 쓰는 이유

groupby() 결과에서 기준 컬럼이 인덱스가 되지 않고 일반 컬럼으로 남습니다.
이후 sort_values(), rename() 등을 사용할 때 더 편리합니다.

비교:
as_index=True (기본값): category가 인덱스로 이동
as_index=False: category가 일반 컬럼으로 유지

as_index=False와 .reset_index()는 거의 같은 결과를 만듭니다.
이 교재에서는 as_index=False를 권장합니다.
```

---

### [1-9] `Series`와 `DataFrame`의 차이 설명 없음 — [섹션 5.4]

**문제**  
섹션 5.4에서 "컬럼을 하나만 선택하면 Series가 됩니다"라고 하는데, Series가 무엇인지 설명이 없다. ch01~ch03에서도 언급된 적이 없어 비전공자는 이 용어를 모른다.

**수정 지시**  
섹션 5.4에 다음 설명을 추가한다:

```
Series와 DataFrame의 차이

DataFrame: 여러 컬럼으로 구성된 표 (2차원)
Series: 하나의 컬럼 또는 행으로 구성된 목록 (1차원)

customers["city"]           → Series (도시 목록 하나)
customers[["city", "age"]]  → DataFrame (두 컬럼짜리 표)

Series는 평균, 합계, 고유값 확인 등 단일 컬럼 분석에 사용됩니다.
DataFrame은 여러 컬럼을 함께 다룰 때 사용됩니다.
```

---

### [1-10] `nunique()` vs `count()` 차이 설명 없음 — [섹션 5.17]

**문제**  
섹션 5.17에서 `order_count=("order_id", "nunique")`를 사용하는데, 왜 `count()`가 아니라 `nunique()`를 쓰는지 이유가 없다. 한 고객이 여러 주문 상세 행을 가지기 때문에 `count()`를 쓰면 주문 수가 아닌 상세 행 수가 계산되어 값이 부풀려진다. 이 차이를 설명하지 않으면 학생이 나중에 부정확한 분석을 하게 된다.

**수정 지시**  
`nunique()` 사용 위치에 다음 설명을 추가한다:

```
왜 count()가 아닌 nunique()인가?

order_items를 order_id로 groupby하면 한 주문에 여러 상품이 있을 경우
같은 order_id가 여러 행에 걸쳐 나타납니다.

count("order_id")  → 행 수를 세므로 상품 수(X)
nunique("order_id") → 고유한 주문 번호 수를 세므로 주문 수(O)

예:
order_id=1에 상품 3개 → count는 3, nunique는 1
```

---

## 2. 보완 권장 항목

---

### [2-1] 메서드 체이닝(Method Chaining) 개념 미설명 — [섹션 5.13]

**문제**  
섹션 5.13에서 `.groupby().sum().sort_values()` 형태의 메서드 체이닝이 처음 등장한다. 이 패턴은 편리하지만, 파이썬 기초 경험이 있는 학생도 처음 보면 낯설 수 있다.

**보완 지시**  
섹션 5.13 코드 앞에 다음 설명을 추가한다:

```
메서드 체이닝이란?

함수(메서드)를 점(.)으로 연결해 순서대로 실행하는 방식입니다.
각 단계의 결과가 다음 단계의 입력이 됩니다.

아래 코드를 단계별로 나눠보면:
step1 = sales_items.groupby("category", as_index=False)
step2 = step1["line_total"].sum()
step3 = step2.sort_values("line_total", ascending=False)

이를 한 줄로 이어서 쓰면:
sales_items.groupby("category", as_index=False)["line_total"].sum().sort_values(...)
```

---

### [2-2] `value_counts(normalize=True)` 결과 해석 예시 없음 — [섹션 5.10]

**문제**  
`value_counts(normalize=True) * 100` 코드가 있지만 결과가 어떻게 보이는지, 어떻게 해석하는지 예시가 없다.

**보완 지시**  
섹션 5.10에 예상 출력과 해석을 추가한다:

```python
orders["payment_method"].value_counts(normalize=True) * 100
# 출력 예:
# credit_card    45.3
# bank_transfer  30.1
# paypal         24.6
# Name: payment_method, dtype: float64

# 해석: 신용카드 결제 비중이 약 45%로 가장 높습니다.
```

---

### [2-3] `to_csv()` 저장 시 인코딩 문제 미안내 — [섹션 5.19 또는 섹션 2 결과물]

**문제**  
결과물 목록에 분석 결과 CSV 저장이 있고, 체크리스트에도 "결과 파일을 적절한 폴더에 저장했는가?"가 있다. 그러나 실습 코드 섹션에 `to_csv()` 코드가 없다. 또한 Windows에서 UTF-8로 저장하면 한글 컬럼명이 포함된 경우 Excel에서 열 때 깨질 수 있다.

**보완 지시**  
섹션 5 마지막에 저장 코드 섹션을 추가한다:

```python
### 5.19 분석 결과 CSV로 저장하기

# Windows에서 Excel로 열 때 한글 깨짐을 방지하려면 utf-8-sig 인코딩을 사용합니다
category_sales.to_csv(
    report_dir / "ch04_category_sales.csv",
    index=False,
    encoding="utf-8-sig"
)

monthly_sales.to_csv(
    report_dir / "ch04_monthly_sales.csv",
    index=False,
    encoding="utf-8-sig"
)

customer_sales.to_csv(
    report_dir / "ch04_customer_sales.csv",
    index=False,
    encoding="utf-8-sig"
)

print("분석 결과 저장 완료")
```

---

### [2-4] `groupby()` 후 `reset_index()` vs `as_index=False` 차이 안내 — [섹션 5.13]

**문제**  
검색하면 `groupby().sum().reset_index()` 패턴이 많이 등장한다. 이 교재는 `as_index=False`를 사용하는데 두 방법의 관계를 설명하지 않으면 학생이 다른 자료를 참고할 때 혼란스럽다.

**보완 지시**  
섹션 5.13 또는 섹션 3.6 끝에 다음 주석을 추가한다:

```python
# 아래 두 코드는 같은 결과를 만듭니다

# 방법 1: as_index=False
df.groupby("category", as_index=False)["sales"].sum()

# 방법 2: reset_index()
df.groupby("category")["sales"].sum().reset_index()

# 이 교재에서는 as_index=False를 사용합니다
```

---

### [2-5] 고객별 집계에서 `name` 컬럼 실무 주의사항 없음 — [섹션 5.18]

**문제**  
섹션 5.18에서 `groupby(["customer_id", "name", "city"])` 형식으로 고객 이름을 그룹키에 포함한다. 샘플 데이터라 실습상 문제는 없지만, 실무에서는 고객 이름을 분석 키로 사용하는 것이 개인정보 보호 측면에서 부적절할 수 있다는 언급이 없다.

**보완 지시**  
섹션 5.18 관련 코드 아래에 다음 주의사항을 추가한다:

```
⚠️ 실무 주의사항

이 교재의 데이터는 Faker로 생성한 가상 데이터이므로 실습에서 이름을 사용해도 됩니다.
실무 데이터에서는 고객 이름 대신 customer_id만 그룹키로 사용하는 것이 바람직합니다.
고객 이름은 보고서 출력 시에만 참조합니다.
```

---

### [2-6] `isin()` 활용 시 ch03 연계 안내 없음 — [섹션 5.6]

**문제**  
섹션 5.6에서 `isin()`을 필터링에 활용하는데, ch03 섹션 5.14에서 이미 소개된 함수다. 앞 장에서 배운 내용을 연계하면 복습 효과를 높일 수 있다.

**보완 지시**  
섹션 5.6의 `isin()` 코드 앞에 한 줄 연계 안내를 추가한다:

```
isin()은 ch03에서 파일 간 키 관계 확인에도 사용한 함수입니다.
여기서는 여러 도시 조건을 한 번에 필터링하는 데 활용합니다.
```

---

### [2-7] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch03과 동일하게 복습용 용어 정리 섹션이 없다.  
4장 신규 용어: Series, DataFrame, 파생 컬럼, 메서드 체이닝, merge, left join, inner join, groupby, agg, as_index, named aggregation, dt, to_period.

**보완 지시**  
섹션 10(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| Series | pandas의 1차원 데이터 구조. 단일 컬럼 선택 시 반환됨 |
| 파생 컬럼 | 기존 컬럼을 계산해 만든 새로운 컬럼 |
| sort_values() | 특정 컬럼 기준으로 오름차순/내림차순 정렬 |
| groupby() | 특정 컬럼 기준으로 데이터를 묶어 집계하는 함수 |
| agg() | groupby 후 여러 집계를 한 번에 계산하는 함수 |
| merge() | 두 DataFrame을 공통 컬럼 기준으로 연결 |
| how="left" | 왼쪽 DataFrame 기준, 오른쪽에 매칭 없으면 NaN |
| how="inner" | 양쪽 모두 있는 행만 결과에 포함 |
| as_index=False | groupby 기준 컬럼을 인덱스가 아닌 일반 컬럼으로 유지 |
| nunique() | 고유값의 개수를 반환 |
| dt | 날짜 타입 컬럼에서 날짜 속성을 접근하기 위한 접두사 |
| to_period() | 날짜를 연-월 등 기간 단위로 변환 |
| 메서드 체이닝 | 함수를 점(.)으로 연결해 순서대로 실행하는 방식 |

---

### [2-8] 연습 문제에 힌트/채점 기준 없음 — [섹션 9]

**문제**  
ch01~ch03과 동일하게 연습 문제에 채점 기준이나 힌트가 없다.  
특히 심화 과제 3번(LLM 코드 검토)은 어떤 기준으로 "맞지 않는 부분"을 판단해야 하는지 안내가 없다.

**보완 지시**  
심화 과제 3번에 다음 힌트와 평가 기준을 추가한다:

```
힌트: LLM이 작성한 코드에서 다음 항목을 중심으로 검토합니다.

1. 컬럼명: LLM이 사용한 컬럼명이 실제 데이터와 일치하는가?
   확인: list(customers.columns)

2. 파일 연결: LLM이 제안한 merge() 기준 컬럼이 실제 파일에 있는가?
   확인: print(order_items.columns), print(products.columns)

3. 집계 함수: 매출 합계는 sum(), 주문 횟수는 nunique()인지 확인

4. 날짜 처리: order_date를 날짜 타입으로 변환했는가?

5. 인코딩: CSV 저장 시 encoding="utf-8-sig"가 적용되었는가?

평가 기준:
- 컬럼명 검증 후 수정 여부 (20%)
- 집계 논리 정확성 (30%)
- 결과 파일 저장 (20%)
- 검증 결과 정리 (30%)
```

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-1] Notebook 파일명 불일치 | 필수 수정 |
| 🔴 높음 | [1-5] `how="left"` vs `how="inner"` 차이 불충분 | 필수 수정 |
| 🔴 높음 | [1-6] `agg()` named aggregation 미설명 | 필수 수정 |
| 🔴 높음 | [1-7] `dt.to_period().astype(str)` 미설명 | 필수 수정 |
| 🔴 높음 | [1-10] `nunique()` vs `count()` 차이 미설명 | 필수 수정 |
| 🟠 중간 | [1-4] `mkdir(exist_ok=True)` 미설명 | 필수 수정 |
| 🟠 중간 | [1-8] `as_index=False` 미설명 | 필수 수정 |
| 🟠 중간 | [1-9] `Series` 개념 미설명 | 필수 수정 |
| 🟡 낮음 | [1-2] 수업 시간 합계 불일치 | 필수 수정 |
| 🟡 낮음 | [1-3] 경로 설정 결론 미제시 (ch03 반복) | 필수 수정 |
| 🟢 권장 | [2-1] 메서드 체이닝 개념 미설명 | 보완 권장 |
| 🟢 권장 | [2-3] `to_csv()` 저장 코드 없음 + 인코딩 주의 | 보완 권장 |
| 🟢 권장 | [2-7] 핵심 용어 정리 섹션 부재 | 보완 권장 |
| 🟢 참고 | [2-2] `value_counts(normalize=True)` 해석 예시 없음 | 보완 권장 |
| 🟢 참고 | [2-4] `reset_index()` vs `as_index=False` 비교 없음 | 보완 권장 |
| 🟢 참고 | [2-5] 고객 이름 그룹키 실무 주의사항 없음 | 보완 권장 |
| 🟢 참고 | [2-6] `isin()` ch03 연계 안내 없음 | 보완 권장 |
| 🟢 참고 | [2-8] 연습 문제 힌트/채점 기준 없음 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 학습 목표와 결과물이 명확하게 대응되어 있음
- 분석 질문 → 사용 데이터 → pandas 기능 매핑 표(섹션 4)가 학습 방향을 잘 안내함
- `line_total` 파생 컬럼을 중심으로 이후 모든 분석(카테고리별, 월별, 고객별)이 이어지는 구조가 일관성 있음
- 병합 후 검증(섹션 5.12)을 별도 단계로 포함한 점이 실무적 관점에서 우수함
- `order_status` 필터링 전 `value_counts()`로 실제 값을 확인하도록 안내한 점이 좋음
- pandas 기본 분석 체크리스트(섹션 8)가 실무 흐름을 잘 반영함

**전체적 방향 제안**  
4장은 pandas의 핵심 기능들이 집중적으로 등장하는 장이다. 현재 가장 큰 문제는 **고급 문법이 설명 없이 등장**하는 것으로, `agg()` named aggregation, `dt.to_period()`, `as_index=False`, `nunique()`의 필요성이 그것이다. 이 항목들은 학생이 다른 분석 문제에 적용하려 할 때 반드시 이해해야 하는 핵심 개념이므로 보강이 필요하다. 또한 **Notebook 파일명 오류(ch04_pandas_basic_analysis.ipynb → ch04_pandas_basic.ipynb)**는 학생이 실습을 시작조차 못하게 하는 치명적 오류이므로 즉시 수정이 필요하다.
