# ch06 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch06_eda_questions.md`

---

## 검토 지침 (Codex Prompt Format)

아래 각 항목은 `[섹션명]` 위치를 기준으로 문제를 설명하고, 구체적인 수정/보완 방향을 제시합니다.  
**[필수 수정]** = 학습에 직접적 혼란을 야기하는 항목  
**[보완 권장]** = 추가 시 학습 효과가 크게 향상되는 항목

---

## 1. 필수 수정 항목

---

### [1-1] 수업 시간 합계와 본문 불일치 — [수업 시간 구성 표]

**문제**  
수업 시간 구성 표 합계:  
30+25+40+45+50+50+40+30 = **310분 = 5시간 10분**  
본문에 "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"라고 적혀 있다.  
ch05와 마찬가지로 2시간 이상 격차가 발생한다.

**수정 지시**  
다음 두 방법 중 하나를 선택해 수정한다:

- 방법 A: 표 항목을 재조정해 합계를 180분(3시간) 이내로 맞춘다.
- 방법 B: 본문을 "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"로 수정한다.

**참고**: ch01~ch06에서 동일 오류가 반복되므로 전체 장 일괄 검토가 필요하다.

---

### [1-2] Notebook 파일명 불일치 — [섹션 5, 강의안 도입부]

**문제**  
강의안 섹션 5에서 Notebook 파일명을 다음과 같이 안내한다:
```
notebooks/ch06_eda_analysis_questions.ipynb
```
그러나 실제 workspace에 존재하는 파일명은:
```
notebooks/ch06_eda_questions.ipynb
```
학생이 강의안 경로를 따라 파일을 열면 "파일을 찾을 수 없습니다" 오류가 발생한다.  
ch04 리뷰 [1-1]에서도 동일 패턴의 오류가 발생했다.

**수정 지시**  
강의안의 파일명 참조를 실제 파일명과 일치하도록 수정한다:

```
# 수정 전
notebooks/ch06_eda_analysis_questions.ipynb

# 수정 후
notebooks/ch06_eda_questions.ipynb
```

전체 장의 Notebook 파일명이 실제 파일과 일치하는지 일괄 검토가 필요하다.

---

### [1-3] CSV 재로드 시 날짜 컬럼이 문자열로 돌아오는 이유 미설명 — [섹션 5.3]

**문제**  
섹션 5.3에서 "CSV로 저장했다가 다시 불러오면 날짜 컬럼이 문자열로 돌아올 수 있습니다"라고만 쓰고, 왜 이런 일이 발생하는지 설명이 없다. 비전공자는 "5장에서 분명히 변환했는데 왜 다시 변환해야 하는가?"라는 의문을 갖게 된다.

**수정 지시**  
섹션 5.3 앞에 다음 설명을 추가한다:

```
날짜형은 CSV에 저장할 수 없는 이유

CSV 파일은 모든 값을 문자열로 저장합니다.
따라서 Chapter 5에서 날짜형(datetime)으로 변환했어도,
CSV로 저장하고 다시 불러오면 문자열로 돌아옵니다.

이는 CSV 형식의 한계이며, 오류가 아닙니다.
pandas DataFrame을 불러올 때마다 날짜형으로 다시 변환해야 합니다.

→ 이를 자동화하고 싶다면 pd.read_csv(..., parse_dates=["order_date"])를 사용할 수 있습니다.
```

`parse_dates` 파라미터 소개를 추가하면 코드를 줄일 수 있다:
```python
orders = pd.read_csv(processed_dir / "orders_clean.csv",
                     parse_dates=["order_date"])
```

---

### [1-4] 병합(merge) 후 행 수 검증이 섹션 5.9에만 있고 5.10, 5.11에는 없음 — [섹션 5.10, 5.11]

**문제**  
섹션 5.9에서는 `merge()` 후 검증 코드(shape 비교, 결측치 확인)를 제공했다. 그러나 섹션 5.10(`order_sales`)과 5.11(`customer_sales_base`)의 병합 후에는 검증 코드가 없다. 일관성이 없어 학습자에게 "이 경우는 왜 검증을 안 하나요?"라는 혼란을 줄 수 있다.

**수정 지시**  
섹션 5.10과 5.11의 `merge()` 직후에 간단한 검증 코드를 추가한다:

```python
# 섹션 5.10: order_items + orders 병합 검증
print("병합 전 order_items:", order_items.shape)
print("병합 후 order_sales:", order_sales.shape)
print("order_date 누락:", order_sales["order_date"].isna().sum())
```

```python
# 섹션 5.11: customer_sales_base 병합 검증
print("병합 전 order_sales:", order_sales.shape)
print("병합 후 customer_sales_base:", customer_sales_base.shape)
print("customer_id 누락:", customer_sales_base["customer_id"].isna().sum())
```

---

### [1-5] `order_count` 계산에 `nunique()` vs `count()` 차이 미설명 — [섹션 5.10]

**문제**  
섹션 5.10에서 `order_count=("order_id", "nunique")`를 사용하는데, 왜 `count()`가 아닌 `nunique()`를 쓰는지 설명이 없다. `order_items`는 주문 하나에 여러 행이 있기 때문에 `count()`를 쓰면 주문 수가 아닌 주문 상세 항목 수가 계산된다. 이 차이를 모르면 결과를 잘못 해석한다. ch04 리뷰 [1-7]에서도 동일하게 지적한 문제다.

**수정 지시**  
해당 코드 앞에 다음 설명을 추가한다:

```python
monthly_sales = (
    order_sales
    .groupby("order_month", as_index=False)
    .agg(
        total_sales=("line_total", "sum"),
        # nunique(): 고유한 order_id 수 = 실제 주문 건수
        # count()를 쓰면 order_items의 행 수(상세 항목 수)가 계산됨
        order_count=("order_id", "nunique")
    )
    .sort_values("order_month")
)
```

---

### [1-6] 취소 주문이 포함된 매출 집계의 문제 미설명 — [섹션 5.9]

**문제**  
섹션 5.9에서 카테고리별 매출을 집계할 때, `orders` 테이블의 `order_status`(취소, 반품 등)를 고려하지 않는다. `order_items`를 `products`와만 병합하므로 취소된 주문의 `line_total`도 매출에 포함된다. 이는 실무적으로 부정확한 매출 집계다.

**수정 지시**  
섹션 5.9 도입부에 다음 주의사항을 추가하고, 선택적으로 필터링 코드를 제공한다:

```
⚠️ 매출 집계 범위 주의

이 예시에서는 order_status(주문 상태)에 관계없이 모든 주문 상세를 집계합니다.
실무에서는 취소(cancelled)나 반품(returned) 주문을 제외하고 집계하는 것이 일반적입니다.

# 완료된 주문만 필터링하는 예시 (선택 사항)
completed_orders = orders[orders["order_status"] == "completed"]["order_id"]
sales_items_completed = sales_items[sales_items["order_id"].isin(completed_orders)]
```

---

### [1-7] `to_csv()` 저장에 인코딩 없음 — [섹션 5.13]

**문제**  
섹션 5.13에서 6개 파일을 저장할 때 `encoding` 옵션이 없다. Windows에서 한글이 포함된 CSV 파일을 Excel로 열면 깨질 수 있다. ch04, ch05에서도 동일하게 지적된 반복 문제다.

**수정 지시**  
섹션 5.13의 모든 `to_csv()` 호출에 `encoding="utf-8-sig"` 추가:

```python
customer_city.to_csv(report_dir / "ch06_customer_city.csv", index=False, encoding="utf-8-sig")
product_category.to_csv(report_dir / "ch06_product_category.csv", index=False, encoding="utf-8-sig")
category_sales.to_csv(report_dir / "ch06_category_sales.csv", index=False, encoding="utf-8-sig")
monthly_sales.to_csv(report_dir / "ch06_monthly_sales.csv", index=False, encoding="utf-8-sig")
customer_sales.to_csv(report_dir / "ch06_customer_sales.csv", index=False, encoding="utf-8-sig")
eda_result_summary.to_csv(report_dir / "ch06_eda_questions.csv", index=False, encoding="utf-8-sig")
```

---

### [1-8] `base_dir` 자동 감지 패턴의 한계 미설명 — [섹션 5.1]

**문제**  
섹션 5.1에서 경로 자동 감지 패턴을 제공했다:
```python
if current_dir.name == "notebooks":
    base_dir = current_dir.parent
else:
    base_dir = current_dir
```
ch06에서 경로 문제를 개선하려는 의도는 좋지만, 이 패턴은 완전하지 않다. VS Code에서 Notebook을 실행하면 `cwd`가 Notebook 파일이 있는 위치가 아닌 워크스페이스 루트가 될 수 있다. 이 경우 `current_dir.name == "notebooks"` 조건이 False가 되어 `base_dir`가 올바르지 않게 설정된다.

**수정 지시**  
ch05 리뷰 [1-9]에서 제안한 파일 존재 기반 자동 감지 방식으로 통일한다:

```python
from pathlib import Path

def find_project_root():
    """data/raw 폴더가 있는 프로젝트 루트를 자동으로 찾습니다."""
    candidates = [Path("."), Path("..")]
    for base in candidates:
        if (base / "data" / "processed" / "customers_clean.csv").exists():
            return base
    raise FileNotFoundError(
        "data/processed 폴더를 찾을 수 없습니다. "
        "Chapter 5 전처리를 먼저 완료하고 CSV 파일을 저장하세요."
    )

root = find_project_root()
processed_dir = root / "data" / "processed"
report_dir = root / "reports"
report_dir.mkdir(exist_ok=True)
print("processed_dir:", processed_dir)
```

이 방식은 실행 위치와 무관하게 항상 동작한다.

---

## 2. 보완 권장 항목

---

### [2-1] `value_counts().reset_index()` + `.columns =` 패턴 반복 설명 없음 — [섹션 5.5, 5.6, 5.7]

**문제**  
섹션 5.5, 5.6, 5.7에서 같은 패턴이 반복된다:
```python
customer_city = customers["city"].value_counts().reset_index()
customer_city.columns = ["city", "customer_count"]
```
이 패턴을 한 번도 설명하지 않고 반복 사용한다. 비전공자는 왜 `reset_index()`를 해야 하는지, 왜 `.columns`로 컬럼명을 재지정하는지 이해하기 어렵다.

**보완 지시**  
첫 번째 등장하는 섹션 5.5에 다음 설명을 추가한다:

```python
# value_counts()는 인덱스에 값, 컬럼에 개수를 반환합니다.
# reset_index()로 인덱스를 컬럼으로 변환한 뒤
# .columns로 컬럼명을 읽기 좋게 변경합니다.
customer_city = customers["city"].value_counts().reset_index()
customer_city.columns = ["city", "customer_count"]

# pandas 2.0 이상에서는 다음 방법도 사용할 수 있습니다.
# customer_city = customers["city"].value_counts().rename_axis("city").reset_index(name="customer_count")
```

이후 섹션에서는 "같은 패턴" 한 줄 안내만 추가하면 된다.

---

### [2-2] 단변량/이변량 EDA 구분 표시 없음 — [섹션 5.5~5.11]

**문제**  
핵심 개념(3.4~3.6)에서 단변량, 이변량, 다변량 EDA를 설명했지만, 실습 코드 섹션에서 어느 섹션이 어떤 EDA 유형인지 표시가 없다. 개념과 실습이 연결되지 않아 학습 효과가 줄어든다.

**보완 지시**  
각 실습 섹션 제목에 EDA 유형을 병기한다:

```
5.5 고객 데이터 단변량 EDA  →  5.5 고객 데이터 단변량 EDA (하나의 변수 분포 확인)
5.6 상품 데이터 단변량 EDA  →  5.6 상품 데이터 단변량 EDA (하나의 변수 분포 확인)
5.9 카테고리별 매출 EDA     →  5.9 카테고리별 매출 EDA (이변량: 카테고리 × 매출)
5.10 월별 매출 EDA          →  5.10 월별 매출 EDA (이변량: 시간 × 매출)
5.11 고객별 구매 금액 EDA   →  5.11 고객별 구매 금액 EDA (이변량: 고객 × 매출)
```

---

### [2-3] `eda_result_summary`의 `next_question` 활용 방법 미설명 — [섹션 5.12]

**문제**  
섹션 5.12에서 `eda_result_summary` DataFrame을 만들고 "EDA는 여기서 끝나지 않습니다. 한 번의 결과는 다음 질문으로 이어집니다"라고만 적혀 있다. 이 표가 다음 장(시각화, 인사이트 도출)에서 어떻게 사용되는지 연결이 없다.

**보완 지시**  
섹션 5.12 끝에 다음 안내를 추가한다:

```
이 표는 Chapter 7 시각화에서 "어떤 질문을 그래프로 표현할 것인가"를 결정하는 기준이 됩니다.
next_question 컬럼의 질문들은 Chapter 9(LLM 인사이트 도출)에서 LLM 프롬프트의 입력으로 사용합니다.
EDA에서 정리한 질문이 이후 장 전체의 분석 방향을 이끌어갑니다.
```

---

### [2-4] 카테고리별 매출 섹션에서 `products` 병합 시 `how="left"` 결과 미검증 가능성 — [섹션 5.9]

**문제**  
섹션 5.9에서 `order_items.merge(products, on="product_id", how="left")`를 사용한다. 이 경우 `order_items`에 있는 `product_id`가 `products`에 없으면 해당 행의 `category`와 `product_name`이 `NaN`이 된다. 코드 뒤에 검증 코드가 있지만, 카테고리가 `NaN`인 행이 있을 때 `groupby("category")`에서 어떻게 처리되는지 설명이 없다.

**보완 지시**  
병합 검증 코드 뒤에 다음 안내를 추가한다:

```python
# 카테고리 누락이 있다면 집계 결과에 NaN 그룹이 생깁니다.
if sales_items["category"].isna().sum() > 0:
    print("⚠️ 카테고리 미분류 상품이 있습니다. 매출 집계에서 제외됩니다.")
    # 필요하다면 dropna()로 제거하거나 별도 처리
    sales_items = sales_items.dropna(subset=["category"])
```

---

### [2-5] `avg_order_value` 계산 시 0으로 나누기 가능성 — [섹션 5.10, 5.11]

**문제**  
`avg_order_value = total_sales / order_count`를 계산할 때, `order_count`가 0이면 `ZeroDivisionError` 또는 `inf`가 발생한다. 실습 데이터에서는 발생 가능성이 낮지만, 학생이 직접 데이터를 변경하거나 필터링 후 사용할 때 문제가 생길 수 있다.

**보완 지시**  
해당 계산 뒤에 간단한 방어 코드 또는 안내를 추가한다:

```python
# order_count가 0인 경우를 방지하기 위해 replace(0, pd.NA)를 사용할 수 있습니다.
monthly_sales["avg_order_value"] = (
    monthly_sales["total_sales"] / monthly_sales["order_count"].replace(0, pd.NA)
).round(0)
```

---

### [2-6] `reports/` 폴더에 파일이 누적되는 구조에 대한 설명 없음 — [섹션 5.13]

**문제**  
ch05에서 `reports/ch05_preprocessing_summary.md`를 저장했고, ch06에서 `reports/ch06_*.csv`와 `reports/ch06_eda_summary.md`를 저장한다. 이후 장도 같은 폴더에 저장된다면 파일이 계속 누적된다. 비전공자는 "이 폴더에 모든 결과물을 다 넣어도 괜찮은가?"라는 의문을 갖게 된다.

**보완 지시**  
섹션 5.13 앞에 또는 5.1 경로 설정에서 다음 안내를 추가한다:

```
reports/ 폴더 구조
이 교재에서는 reports/ 폴더를 장별 결과물 저장 공간으로 사용합니다.
파일명에 ch06_ 접두사가 붙어 있어 다른 장의 결과물과 혼동을 방지합니다.

reports/
├── ch05_preprocessing_summary.md
├── ch06_category_sales.csv
├── ch06_monthly_sales.csv
└── ch06_eda_summary.md

기말 프로젝트(Chapter 15)에서는 이 파일들이 최종 보고서의 재료로 활용됩니다.
```

---

### [2-7] 연습 문제에 힌트/채점 기준 없음 — [섹션 9]

**문제**  
ch01~ch05와 동일.

**보완 지시**  
심화 과제 평가 기준 예시:

```
평가 기준 (EDA 요약 보고서):
- 분석 질문을 계산 가능한 지표로 구체화했는가? (20%)
- 단변량/이변량 EDA를 구분해 수행했는가? (15%)
- 병합 결과를 검증했는가? (15%)
- 관찰 결과와 원인 가설을 구분해 서술했는가? (25%)
- 추가 분석 질문을 데이터 기반으로 작성했는가? (15%)
- LLM이 제안한 질문 중 검증 불가능한 것을 수정했는가? (10%)
```

---

### [2-8] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch05와 동일. ch06 신규 용어: EDA, 단변량(univariate), 이변량(bivariate), 다변량(multivariate), `value_counts()`, `nunique()`, `sales_ratio`, 분석 질문(analytical question), 관찰(observation), 가설(hypothesis), 상관관계(correlation).

**보완 지시**  
섹션 10(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| EDA (탐색적 데이터 분석) | 데이터의 구조, 분포, 패턴, 관계를 탐색하는 과정 |
| 단변량 EDA | 하나의 변수만 살펴보는 탐색 |
| 이변량 EDA | 두 변수의 관계나 그룹 간 차이를 탐색 |
| `value_counts()` | 범주형 변수의 빈도(개수)를 집계 |
| `nunique()` | 고유한 값의 개수를 반환. `count()`와 다름 |
| 관찰 | 데이터에서 확인된 사실 |
| 가설 | 데이터 결과에 대한 잠정적 설명. 추가 검증 필요 |
| 상관관계 | 두 변수가 함께 변하는 경향. 원인-결과를 뜻하지 않음 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-2] Notebook 파일명 불일치 (ch04와 같은 패턴) | 필수 수정 |
| 🔴 높음 | [1-3] CSV 재로드 시 날짜 문자열 복귀 이유 미설명 | 필수 수정 |
| 🔴 높음 | [1-5] `nunique()` vs `count()` 차이 미설명 | 필수 수정 |
| 🔴 높음 | [1-6] 취소 주문 포함 매출 집계 문제 미설명 | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (310분 vs "약 3시간") | 필수 수정 |
| 🟠 중간 | [1-4] 병합 검증 코드 불일치 | 필수 수정 |
| 🟠 중간 | [1-7] `to_csv()` 인코딩 누락 (ch04~ch06 반복) | 필수 수정 |
| 🟡 낮음 | [1-8] `base_dir` 자동 감지 패턴 한계 | 필수 수정 |
| 🟢 권장 | [2-1] `value_counts().reset_index()` 패턴 미설명 | 보완 권장 |
| 🟢 권장 | [2-2] 단변량/이변량 EDA 구분 표시 없음 | 보완 권장 |
| 🟢 권장 | [2-3] `eda_result_summary` 활용 방법 미설명 | 보완 권장 |
| 🟢 권장 | [2-4] `category` NaN 처리 미설명 | 보완 권장 |
| 🟢 참고 | [2-5] `avg_order_value` 나누기 0 방어 없음 | 보완 권장 |
| 🟢 참고 | [2-6] `reports/` 폴더 누적 구조 미설명 | 보완 권장 |
| 🟢 참고 | [2-7] 연습 문제 채점 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-8] 핵심 용어 정리 섹션 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 섹션 5.1에서 `base_dir` 자동 감지 패턴을 도입해 ch05의 경로 이슈를 개선하려 한 시도가 좋다.
- "좋은 분석은 좋은 질문에서 시작된다"는 메시지를 반복 강조해 학습자의 사고방식 전환을 유도한다.
- 분석 질문 → 지표 → 코드 연결 구조(섹션 3.3, 5.4)가 실습 전 체계적인 설계를 가르쳐 잘 구성되었다.
- "좋은 분석 질문 조건" 표와 "잘못된 질문" 표의 대비가 명확해 비전공자에게 매우 유익하다.
- 섹션 5.9 병합 후 검증 코드(shape, 결측치 확인)가 포함된 점이 실무형 습관 형성에 좋다.
- LLM 프롬프트 섹션 6.4("LLM이 만든 분석 질문 검토 요청")가 매우 교육적이다. 데이터에 없는 정보를 요구하는 LLM의 한계를 직접 실습한다.
- 섹션 5.14 EDA 보고서에 "해석 시 주의사항"을 포함시킨 점이 매우 좋다.
- `tabulate` 설치 안내를 섹션 5.1에 포함시킨 점이 ch05 [1-6] 문제를 개선했다.

**전체적 방향 제안**  
ch06은 ch01~ch05 중 완성도가 가장 높은 편이다. 핵심 이슈는 크게 두 가지다: **(1) Notebook 파일명 불일치**는 학생이 첫 번째 실습 진입 단계에서 오류를 만나게 하는 가장 치명적인 문제이므로 즉시 수정이 필요하다. **(2) 취소 주문 포함 매출 집계**는 이후 장(ch07 시각화, ch08 중간 프로젝트)의 결과물 정확성에 영향을 주므로 반드시 한 줄 이상의 주의사항 안내가 필요하다. 나머지 이슈는 학습 품질 개선 수준으로, 현재도 충분히 학습 가능한 수준이다.
