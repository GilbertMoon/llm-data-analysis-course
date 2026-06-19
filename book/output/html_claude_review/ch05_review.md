# ch05 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch05_data_preprocessing.md`

---

## 검토 지침 (Codex Prompt Format)

아래 각 항목은 `[섹션명]` 위치를 기준으로 문제를 설명하고, 구체적인 수정/보완 방향을 제시합니다.  
**[필수 수정]** = 학습에 직접적 혼란을 야기하는 항목  
**[보완 권장]** = 추가 시 학습 효과가 크게 향상되는 항목

---

## 1. 필수 수정 항목

---

### [1-1] 수업 시간 구성표 합계와 본문 불일치 — 가장 큰 격차 — [수업 시간 구성 표]

**문제**  
수업 시간 구성 표의 권장 시간 합계:  
30+45+35+45+45+40+45+30 = **315분 = 5시간 15분**  
그런데 본문에 "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"라고 적혀 있다.  
ch01~ch05 중 격차가 가장 크며(2시간 이상), 학습자의 시간 계획을 크게 왜곡한다.

**수정 지시**  
다음 두 방법 중 하나를 선택해 수정한다:

- 방법 A: 표의 항목을 재조정해 핵심 항목만 남기고 합계를 180분(3시간)으로 맞춘다.
- 방법 B: 본문을 "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"로 수정하고, 이 장이 볼륨이 큰 이유를 안내한다.

**참고**: ch01~ch05에서 이 오류가 반복되고 있으므로 전체 장 일괄 검토가 필요하다.

---

### [1-2] `import numpy as np`가 실제로 사용되지 않음 — [섹션 5.1]

**문제**  
섹션 5.1에서 `import numpy as np`를 포함하지만, ch05 전체 실습 코드에서 `np`를 직접 사용하는 코드가 없다. 이유 없이 등장하는 import는 비전공자에게 "numpy를 어디서 쓰는 건지" 혼란을 준다.

**수정 지시**  
다음 두 방법 중 하나를 선택한다:

- 방법 A: `import numpy as np`를 삭제한다.
- 방법 B: numpy가 필요한 코드(예: `np.nan` 활용, IQR 계산)를 추가하고, 간단한 사용 목적 설명을 추가한다:

```python
import numpy as np  # 수치 계산 및 NaN 값 처리에 사용
```

---

### [1-3] `df.copy()` 필요성 미설명 — [섹션 5.3]

**문제**  
섹션 5.3에서 `customers_clean = customers.copy()`를 권장하지만, 왜 `.copy()`를 써야 하는지 설명이 없다. `.copy()` 없이 `customers_clean = customers`처럼 직접 대입하면 이후 수정 시 원본 `customers`도 함께 변경된다. 이를 모르는 학생이 원본을 실수로 수정할 위험이 있다.

**수정 지시**  
섹션 5.3 코드 앞에 다음 설명을 추가한다:

```
.copy()가 필요한 이유

pandas에서 단순 대입은 복사가 아니라 같은 데이터를 가리키는 것입니다.

# 잘못된 방법 (원본도 함께 변경됨)
customers_clean = customers

# 올바른 방법 (독립적인 복사본 생성)
customers_clean = customers.copy()

.copy()를 쓰지 않으면 customers_clean을 수정할 때
원본 customers도 함께 바뀝니다. 이를 방지하기 위해 항상 .copy()를 사용합니다.
```

---

### [1-4] `where()` 로직이 반직관적이며 설명 부족 — [섹션 5.8]

**문제**  
`strip_string_columns()` 함수 안의 핵심 코드:
```python
df[col] = df[col].where(
    df[col].isna(),
    df[col].astype(str).str.strip()
)
```
`where(condition, other)` 동작 방식이 반직관적이다. `condition`이 True인 곳은 원본 값 유지, False인 곳만 `other`로 대체한다. 즉, 결측치(`isna() = True`)는 그대로 두고, 실제 값(`isna() = False`)만 strip한다. 이 논리를 설명 없이 사용하면 학생이 코드를 이해하지 못한 채 따라 치게 된다.

**수정 지시**  
해당 코드 앞에 단계별 설명을 추가한다:

```python
# pandas의 where(condition, other)는 다음과 같이 동작합니다:
# - condition이 True인 곳: 원본 값 유지
# - condition이 False인 곳: other 값으로 대체

# 즉, isna()가 True(결측치)인 곳 → 결측치 그대로 유지
#     isna()가 False(실제 값)인 곳 → str.strip() 적용

df[col] = df[col].where(
    df[col].isna(),          # 결측치인 곳은 건드리지 않음
    df[col].astype(str).str.strip()  # 결측치가 아닌 곳은 공백 제거
)
```

또는 더 직관적인 대안 코드로 교체한다:
```python
# 더 직관적인 방법: 결측치가 아닌 값에만 strip 적용
mask = df[col].notna()
df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()
```

---

### [1-5] `to_csv()` 저장에 인코딩 없음 — [섹션 5.18, 섹션 5.19]

**문제**  
섹션 5.18에서 전처리 데이터를 저장할 때:
```python
customers_clean.to_csv(processed_dir / "customers_clean.csv", index=False)
```
`encoding` 옵션이 없다. Windows에서 한글 컬럼명이나 한글 값이 포함된 CSV를 Excel로 열면 깨질 수 있다. ch04 리뷰 [2-3]에서 이미 지적한 문제가 ch05에서도 반복된다.

**수정 지시**  
섹션 5.18의 모든 `to_csv()` 호출에 `encoding="utf-8-sig"`를 추가한다:

```python
customers_clean.to_csv(
    processed_dir / "customers_clean.csv",
    index=False,
    encoding="utf-8-sig"   # Windows Excel에서 한글 깨짐 방지
)
products_clean.to_csv(processed_dir / "products_clean.csv", index=False, encoding="utf-8-sig")
orders_clean.to_csv(processed_dir / "orders_clean.csv", index=False, encoding="utf-8-sig")
order_items_clean.to_csv(processed_dir / "order_items_clean.csv", index=False, encoding="utf-8-sig")
```

섹션 5.19 보고서 저장도 동일하게 `encoding="utf-8"`을 명시한다 (이미 있으나 주석으로 이유 설명 추가).

---

### [1-6] `to_markdown()` 함수가 선택적 의존성(`tabulate`) 요구 — [섹션 5.19]

**문제**  
섹션 5.19에서 `comparison.to_markdown(index=False)`를 사용하는데, 이 메서드는 `tabulate` 패키지가 설치되어 있어야 작동한다. `requirements.txt`에 `tabulate`가 없으면 `ImportError: Unable to import required dependencies: tabulate` 오류가 발생한다. 학생이 이 오류를 만났을 때 원인을 알 수 없다.

**수정 지시**  
다음 두 방법 중 하나를 선택한다:

- 방법 A: `to_markdown()` 대신 문자열 포맷 방식으로 교체한다:

```python
# tabulate 패키지 없이 사용하는 방법
summary_text = f"""
# Chapter 5 데이터 전처리 요약

## 전처리 전후 데이터 크기

{comparison.to_string(index=False)}
"""
```

- 방법 B: `requirements.txt`에 `tabulate`를 추가하고, 섹션 5.19에 다음 안내를 추가한다:

```
to_markdown()을 사용하려면 tabulate 패키지가 필요합니다.
pip install tabulate
ImportError가 발생하면 위 명령으로 설치하거나, to_string()을 사용합니다.
```

---

### [1-7] `{...}.issubset(df.columns)` 문법 미설명 — [섹션 5.20]

**문제**  
`preprocess_order_items()` 함수에서:
```python
if {"quantity", "unit_price"}.issubset(df.columns):
```
파이썬 집합(set)의 `issubset()` 메서드가 등장한다. 비전공자에게는 이 문법이 낯설고, 왜 일반 `if` 문 대신 이 형식을 쓰는지 이해하기 어렵다.

**수정 지시**  
해당 코드를 더 직관적인 형식으로 교체하거나 설명을 추가한다:

```python
# 방법 1 (기존 코드 - 집합 issubset 활용)
if {"quantity", "unit_price"}.issubset(df.columns):
    df["line_total"] = df["quantity"] * df["unit_price"]

# 방법 2 (더 직관적 - 개별 컬럼 존재 확인)
if "quantity" in df.columns and "unit_price" in df.columns:
    df["line_total"] = df["quantity"] * df["unit_price"]
```

방법 2를 기본으로 사용하고, 방법 1은 "같은 결과를 얻는 다른 표현"으로 주석 처리하는 것을 권장한다.

---

### [1-8] `strip_string_columns()` 함수에서 `select_dtypes()` 미설명 — [섹션 5.8]

**문제**  
함수 내부에서 `df.select_dtypes(include="object").columns`가 사용되는데, `select_dtypes()`가 무엇인지 설명이 없다. ch03 리뷰 [2-10]에서 `describe(include="all")`을 안내할 때 `select_dtypes` 개념을 처음 접했을 수도 있지만, 여기서 별도 설명이 필요하다.

**수정 지시**  
`select_dtypes()` 코드 앞에 다음 설명을 추가한다:

```python
# select_dtypes(include="object")는 문자열(object 타입) 컬럼만 선택합니다.
# 숫자형, 날짜형 컬럼은 제외하고 문자열 컬럼에만 공백 제거를 적용합니다.
string_columns = df.select_dtypes(include="object").columns
```

---

### [1-9] 경로 설정 결론 미제시 — ch03~ch05 반복 문제 — [섹션 5.1]

**문제**  
`raw_dir = Path("data/raw")` vs `Path("../data/raw")` 두 가지를 제시하고 어떤 것을 쓸지 결론이 없다. ch03, ch04에서도 동일하게 지적된 문제가 ch05에서도 반복된다.

**수정 지시**  
ch03 리뷰 [1-2]에서 제안한 자동 감지 패턴을 ch05에도 동일하게 적용한다:

```python
from pathlib import Path

def find_project_root():
    """data/raw 폴더가 있는 프로젝트 루트를 자동으로 찾습니다."""
    candidates = [Path("."), Path("..")]
    for base in candidates:
        if (base / "data" / "raw" / "customers.csv").exists():
            return base
    raise FileNotFoundError("data/raw 폴더를 찾을 수 없습니다. "
                            "python scripts/generate_sample_data.py를 먼저 실행하세요.")

root = find_project_root()
raw_dir = root / "data" / "raw"
processed_dir = root / "data" / "processed"
report_dir = root / "reports"

processed_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(exist_ok=True)
print("데이터 경로:", raw_dir)
```

---

### [1-10] `drop_duplicates()` 호출 순서 문제 — [섹션 5.6]

**문제**  
섹션 5.6에서 중복 행 제거를 `customers_clean.drop_duplicates()`처럼 바로 적용하지만, 이전 단계에서 결측치를 이미 채웠다. 결측치를 채운 뒤 중복을 제거하면, 원래는 결측치 차이 때문에 고유했던 행이 대체값(중앙값) 부여 후 완전히 동일해져서 제거될 수 있다. 순서의 영향을 설명하지 않는다.

**수정 지시**  
섹션 5.6 또는 섹션 3.4에 다음 주의사항을 추가한다:

```
⚠️ 전처리 순서 주의

결측치를 채운 뒤 중복을 제거하면, 결측치 대체로 인해 원래 고유했던 행이
동일해진 경우 제거될 수 있습니다.

이 교재에서는 다음 순서를 권장합니다:
1. 먼저 중복 행 확인 (원본 기준)
2. 결측치 처리
3. 문자열 표기 통일
4. 타입 변환
5. 파생 컬럼 생성
6. 이상값 처리
7. 최종 중복 확인

실습에서는 간략하게 진행하지만, 처리 순서가 결과에 영향을 줄 수 있음을 인식해야 합니다.
```

---

## 2. 보완 권장 항목

---

### [2-1] `fillna()` vs `mask()` vs `where()` 관계 미설명 — [섹션 5.5]

**문제**  
결측치 처리에 `fillna()`, `mask()`, `where()` 등 여러 방법이 있는데, 왜 `fillna()`를 선택했는지 설명이 없다.

**보완 지시**  
섹션 5.5에 다음 비교를 추가한다:

| 함수 | 역할 | 사용 상황 |
|------|------|-----------|
| `fillna(값)` | 결측치를 지정한 값으로 채움 | 가장 일반적인 결측치 처리 |
| `dropna()` | 결측치가 있는 행(또는 열) 제거 | 결측치 비율이 낮고 제거해도 괜찮을 때 |
| `where(condition, other)` | 조건이 False인 위치만 other로 대체 | 조건부 값 교체 |
| `mask(condition, other)` | 조건이 True인 위치만 other로 대체 | where의 반대 동작 |

```
이 교재에서는 fillna()를 주로 사용합니다. 가장 직관적이기 때문입니다.
```

---

### [2-2] `drop_duplicates()` `keep` 파라미터 미안내 — [섹션 5.6]

**문제**  
중복 행을 제거할 때 어떤 행을 남기는지(`keep="first"`, `keep="last"`, `keep=False`) 설명이 없다.

**보완 지시**  
섹션 5.6에 다음 내용을 추가한다:

```python
# drop_duplicates() 기본값은 keep="first": 중복 중 첫 번째 행을 유지
customers_clean = customers_clean.drop_duplicates()            # = keep="first"

# 마지막 행 유지
# customers_clean = customers_clean.drop_duplicates(keep="last")

# 중복인 모든 행 제거 (하나도 남기지 않음)
# customers_clean = customers_clean.drop_duplicates(keep=False)
```

---

### [2-3] 문자열 정리 관련 자주 쓰는 메서드 목록 없음 — [섹션 5.8, 5.9]

**문제**  
`str.strip()`만 소개되고, 비전공자가 실무에서 자주 접하는 다른 문자열 정리 메서드(`str.lower()`, `str.upper()`, `str.replace()`, `str.contains()`)가 안내되지 않는다.

**보완 지시**  
섹션 5.8 또는 5.9 끝에 자주 쓰는 문자열 메서드 표를 추가한다:

| 메서드 | 설명 | 예시 |
|--------|------|------|
| `str.strip()` | 앞뒤 공백 제거 | `" Seoul " → "Seoul"` |
| `str.lower()` | 소문자로 변환 | `"SEOUL" → "seoul"` |
| `str.upper()` | 대문자로 변환 | `"seoul" → "SEOUL"` |
| `str.replace("a", "b")` | 문자열 교체 | `"Complete" → "completed"` |
| `str.contains("패턴")` | 패턴 포함 여부 True/False | 특정 단어 포함 확인 |

---

### [2-4] 이상값 확인에 IQR 방법 언급 없음 — [섹션 5.13]

**문제**  
이상값 확인을 `price <= 0` 같은 수동 기준으로만 설명하고, 통계적 이상값 탐지(IQR 방법)를 언급하지 않는다. 비전공자에게 간단한 개념만 소개해도 학습 깊이가 높아진다.

**보완 지시**  
섹션 5.13 끝에 다음 보충 내용을 추가한다:

```python
# 통계적 이상값 탐지: IQR(사분위수 범위) 방법
Q1 = products_clean["price"].quantile(0.25)  # 1사분위수
Q3 = products_clean["price"].quantile(0.75)  # 3사분위수
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR  # 이상값 하한
upper = Q3 + 1.5 * IQR  # 이상값 상한

outliers = products_clean[
    (products_clean["price"] < lower) | (products_clean["price"] > upper)
]
print("IQR 기준 이상값 후보:", len(outliers))
```

```
IQR 방법은 데이터의 중간 50% 범위를 기준으로 이상값을 탐지합니다.
이 교재에서는 분석 목적에 맞는 수동 기준(price <= 0)을 우선 사용하고,
통계적 방법은 6장(EDA)에서 추가로 다룹니다.
```

---

### [2-5] `preprocess_*` 함수들의 `df.copy()` 중복 호출 비효율 설명 없음 — [섹션 5.20]

**문제**  
`preprocess_customers(df)` 내부에서 `df = df.copy()`를 하고, 내부적으로 호출하는 `strip_string_columns(df)` 안에서도 `df = df.copy()`를 한다. 이중 복사가 발생한다. 비전공자는 왜 같은 것을 두 번 하는지 의아하게 생각할 수 있다.

**보완 지시**  
`strip_string_columns()` 함수 설명에 다음 주석을 추가한다:

```python
def strip_string_columns(df):
    # 내부에서 copy()를 해 호출한 쪽의 원본을 보호합니다.
    # 이미 copy()된 df를 받아도 안전하게 동작합니다.
    df = df.copy()
    ...
```

또는 함수 설계 원칙을 한 줄로 설명한다:

```
함수 안에서 df.copy()를 하면, 함수 밖에서 copy()를 했는지 여부와 관계없이
항상 안전하게 동작합니다. 이중 복사는 메모리를 조금 더 사용하지만, 안전성을 높입니다.
```

---

### [2-6] 섹션 간 전환 문장 부재 — [전체 구조]

**문제**  
ch01~ch04와 동일하게, 결측치(5.4-5.5) → 중복(5.6-5.7) → 문자열 정리(5.8-5.9) → 날짜 변환(5.10-5.11) → 숫자형 변환(5.12) → 이상값(5.13-5.14) → 파생 컬럼(5.15) 순으로 이동할 때 전환 문장이 없다.

**보완 지시**  
각 섹션 전환 시점에 1문장씩 전환 안내를 추가한다:

```
예시 (5.7 → 5.8):
"ID 기준 중복까지 확인했습니다. 이번에는 눈에 보이지 않는 공백 때문에
같은 값이 다르게 인식되는 문자열 표기 문제를 정리합니다."

예시 (5.9 → 5.10):
"문자열 표기를 통일했으면, 이번에는 날짜 컬럼을 날짜형으로 변환해
월별·요일별 분석을 가능하게 합니다."
```

---

### [2-7] 연습 문제에 힌트/채점 기준 없음 — [섹션 9]

**문제**  
ch01~ch04와 동일.

**보완 지시**  
심화 과제의 채점 기준 예시를 추가한다:

```
평가 기준 (전처리 보고서 작성):
- 결측치 처리 이유와 방법을 명시했는가? (20%)
- 중복 데이터 확인 결과를 기록했는가? (15%)
- 날짜·숫자형 변환 결과와 실패 건수를 확인했는가? (20%)
- 이상값 처리 기준을 문서화했는가? (20%)
- 전처리 전후 데이터 크기를 비교했는가? (15%)
- 파일 간 키 관계를 전처리 후 재확인했는가? (10%)
```

---

### [2-8] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch04와 동일. 5장 신규 용어: `.copy()`, `fillna()`, `dropna()`, `drop_duplicates()`, `str.strip()`, `select_dtypes()`, `replace()`, `day_name()`, `issubset()`, IQR, 전처리(preprocessing), 파생 컬럼.

**보완 지시**  
섹션 10(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| `.copy()` | DataFrame을 독립적으로 복사. 원본 보호 |
| `fillna(값)` | 결측치를 지정 값으로 채움 |
| `dropna()` | 결측치가 있는 행 제거 |
| `drop_duplicates()` | 중복 행 제거. 기본값 첫 번째 행 유지 |
| `str.strip()` | 문자열 앞뒤 공백 제거 |
| `select_dtypes()` | 특정 타입의 컬럼만 선택 |
| `replace(dict)` | 딕셔너리 기준으로 값 매핑·교체 |
| `dt.day_name()` | 날짜 타입 컬럼에서 요일 이름 추출 |
| IQR | 사분위수 범위(Q3-Q1). 통계적 이상값 기준으로 활용 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-1] 수업 시간 합계 격차 최대(2시간 이상) | 필수 수정 |
| 🔴 높음 | [1-3] `df.copy()` 필요성 미설명 | 필수 수정 |
| 🔴 높음 | [1-4] `where()` 반직관적 로직 미설명 | 필수 수정 |
| 🔴 높음 | [1-6] `to_markdown()` tabulate 의존성 미안내 | 필수 수정 |
| 🟠 중간 | [1-2] `import numpy as np` 미사용 | 필수 수정 |
| 🟠 중간 | [1-5] `to_csv()` 인코딩 누락 (ch04 반복) | 필수 수정 |
| 🟠 중간 | [1-7] `issubset()` 문법 미설명 | 필수 수정 |
| 🟠 중간 | [1-8] `select_dtypes()` 미설명 | 필수 수정 |
| 🟠 중간 | [1-10] 전처리 순서 영향 미설명 | 필수 수정 |
| 🟡 낮음 | [1-9] 경로 설정 결론 미제시 (ch03~ch05 반복) | 필수 수정 |
| 🟢 권장 | [2-1] `fillna()` vs `mask()` vs `where()` 비교 없음 | 보완 권장 |
| 🟢 권장 | [2-3] 문자열 정리 메서드 목록 없음 | 보완 권장 |
| 🟢 권장 | [2-4] IQR 이상값 탐지 미언급 | 보완 권장 |
| 🟢 권장 | [2-8] 핵심 용어 정리 섹션 부재 | 보완 권장 |
| 🟢 참고 | [2-2] `drop_duplicates()` `keep` 파라미터 미안내 | 보완 권장 |
| 🟢 참고 | [2-5] `df.copy()` 이중 호출 미설명 | 보완 권장 |
| 🟢 참고 | [2-6] 섹션 간 전환 문장 부재 | 보완 권장 |
| 🟢 참고 | [2-7] 연습 문제 채점 기준 없음 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 원본 데이터와 전처리 데이터를 `raw/` vs `processed/`로 분리하는 개념을 명확히 전달함
- 전처리 함수(`preprocess_customers()` 등)를 만들어 실무형 코드 패턴을 보여준 점이 우수함
- `if "컬럼명" in df.columns:` 패턴으로 컬럼 존재 여부를 확인하는 방어적 코드 습관을 일관되게 보여줌
- 이상값을 무조건 삭제하지 않고 확인 후 판단하도록 강조한 점이 실무적으로 적절함
- 전처리 기준을 텍스트로 기록(`text` 코드 블록)하도록 안내한 점이 좋음
- 전처리 전후 비교표(섹션 5.17)를 만드는 과정이 학습 흐름상 자연스럽게 배치됨
- 파일 간 키 관계를 전처리 후 다시 확인하는 섹션(5.16)이 포함된 점이 실무적으로 우수함
- LLM 전처리 코드 검토 프롬프트(섹션 6.5)가 매우 구체적이고 교육적 가치가 높음

**전체적 방향 제안**  
5장은 코드 양이 가장 많은 장 중 하나다. 현재 가장 큰 문제는 **함수 내부 코드의 고급 패턴**(`where()`, `select_dtypes()`, `issubset()`, `.copy()` 동작 원리)이 설명 없이 등장하는 것이다. 비전공자는 이 함수들을 "그냥 복사해서 쓰는 것"으로 인식하게 되어 변형 적용 능력을 갖추지 못한다. 핵심 함수에 대한 설명 1~2줄 추가만으로 학습 효과를 크게 높일 수 있다. 또한 **수업 시간 구성표 격차(2시간 이상)**는 이 장이 실제로 한 번 수업에 모두 다루기 어렵다는 신호이므로, 핵심 전처리와 심화 전처리로 섹션을 구분하는 것을 검토할 필요가 있다.
