# ch08 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch08_midterm_project.md`

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
30+30+50+40+60+50+60+30+40 = **390분 = 6시간 30분**  
본문에 "기본 수업은 약 4시간을 기준으로 구성되어 있습니다"라고 적혀 있다.  
이전 장들보다 더 솔직하게 "4시간"을 제시했지만, 실제 합계와 2시간 30분 격차가 존재한다.

**수정 지시**  
방법 A: 표 항목을 재조정해 합계를 240분(4시간) 이내로 맞춘다.  
방법 B: 본문을 "기본 수업은 약 6시간을 기준으로 구성되어 있습니다. 개인별 피드백까지 포함하면 8시간 분량으로 확장할 수 있습니다"로 수정한다.

---

### [1-2] `to_csv()` 저장에 인코딩 없음 — [섹션 5.2, 5.9, 5.12, 5.13, 5.14]

**문제**  
섹션 5.2(`dataset_summary`), 5.9(`customers_clean` 등 4개), 5.12(`category_sales`), 5.13(`monthly_sales`), 5.14(`customer_sales`) 총 10회 이상의 `to_csv()` 호출 중 `encoding` 옵션이 없다. Windows에서 한글이 포함된 CSV를 Excel로 열면 깨진다. ch04~ch08 전체 반복 문제다.

**수정 지시**  
모든 `to_csv()` 호출에 `encoding="utf-8-sig"` 추가. 대표 예시:

```python
# 섹션 5.9
customers_clean.to_csv(processed_dir / "customers_clean.csv", index=False, encoding="utf-8-sig")
products_clean.to_csv(processed_dir / "products_clean.csv", index=False, encoding="utf-8-sig")
orders_clean.to_csv(processed_dir / "orders_clean.csv", index=False, encoding="utf-8-sig")
order_items_clean.to_csv(processed_dir / "order_items_clean.csv", index=False, encoding="utf-8-sig")

# 섹션 5.12
category_sales.to_csv(report_dir / "ch08_category_sales.csv", index=False, encoding="utf-8-sig")
```

---

### [1-3] `customer_sales`에서 `name` 컬럼 존재 미확인 — [섹션 5.14]

**문제**  
섹션 5.14에서 `groupby(["customer_id", "name", "city"])`를 사용하는데, `customers_clean.csv`에 실제로 `name` 컬럼이 있는지 확인 없이 사용한다. `name`이 없으면 `KeyError`가 발생한다. ch06, ch07 리뷰에서도 동일하게 지적된 반복 문제다.

**수정 지시**  
```python
# customers 컬럼 확인
print("customers_clean 컬럼:", customers_clean.columns.tolist())

# 방어적 groupby 설정
group_cols = ["customer_id"]
if "name" in customers_clean.columns:
    group_cols.append("name")
if "city" in customers_clean.columns:
    group_cols.append("city")

customer_sales = (
    customer_sales_base
    .groupby(group_cols, as_index=False)
    .agg(
        order_count=("order_id", "nunique"),
        total_sales=("line_total", "sum")
    )
    .sort_values("total_sales", ascending=False)
)
```

---

### [1-4] 한글 폰트 하드코딩 — [섹션 5.1]

**문제**  
`plt.rcParams["font.family"] = "Malgun Gothic"` Windows 전용 설정만 있다. Mac/Linux 학생은 한글이 □□□로 표시된다. ch07 리뷰 [1-5]에서 동일하게 지적했다.

**수정 지시**  
ch07 리뷰에서 제안한 OS 자동 감지 코드로 교체한다:

```python
import platform

system = platform.system()
if system == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif system == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "NanumGothic"

plt.rcParams["axes.unicode_minus"] = False
print(f"OS: {system}, 폰트: {plt.rcParams['font.family']}")
```

---

### [1-5] 취소 주문 포함 매출 집계 문제: 인식은 했으나 처리 코드 없음 — [섹션 5.12, 5.19]

**문제**  
섹션 5.19 `interpretation_notes`에 "취소 주문이 매출 계산에 포함되었는지 확인해야 합니다"라고 경고했다. 그런데 섹션 5.12 카테고리별 매출, 5.13 월별 매출 계산 코드에서 실제로 `order_status` 필터링을 하지 않아 취소 주문이 포함된 채로 집계된다. 학생은 이 경고를 보고도 어떻게 처리해야 하는지 알 수 없다.

**수정 지시**  
섹션 5.12 앞에 필터링 옵션을 명시한다:

```python
# 매출 집계 범위 설정
# 옵션 A: 완료된 주문만 포함 (권장)
completed_ids = orders_clean[
    orders_clean["order_status"] == "completed"
]["order_id"]
order_items_completed = order_items_clean[
    order_items_clean["order_id"].isin(completed_ids)
]

# 옵션 B: 모든 주문 포함 (이번 실습에서 사용)
# 취소 주문 포함 여부는 보고서에 명시해야 합니다.
order_items_for_analysis = order_items_clean  # 전체 포함

# ⚠️ 이 선택이 매출 집계 결과에 영향을 줍니다.
# 보고서의 "전처리 내용" 섹션에 어느 방식을 선택했는지 기록해야 합니다.
```

---

### [1-6] `xticks(rotation=45)` `ha="right"` 누락 — [섹션 5.16, 5.17]

**문제**  
ch07 리뷰 [1-6]에서 지적한 것과 동일하다. `xticks(rotation=45)` 단독 사용 시 레이블이 막대 중앙 위에 걸쳐 보기 불편하다.

**수정 지시**  
섹션 5.16, 5.17의 모든 `xticks(rotation=45)`에 `ha="right"` 추가:

```python
plt.xticks(rotation=45, ha="right")
```

---

### [1-7] `base_dir` 자동 감지 패턴 한계 — [섹션 5.1]

**문제**  
ch06, ch07과 동일한 `Path.cwd().name == "notebooks"` 패턴이 ch08에서도 반복된다.

**수정 지시**  
ch06 리뷰 [1-8]에서 제안한 파일 존재 기반 자동 감지 방식으로 통일한다:

```python
from pathlib import Path

def find_project_root():
    candidates = [Path("."), Path("..")]
    for base in candidates:
        if (base / "data" / "raw" / "customers.csv").exists():
            return base
    raise FileNotFoundError(
        "data/raw 폴더를 찾을 수 없습니다. "
        "python scripts/generate_sample_data.py를 먼저 실행하세요."
    )

root = find_project_root()
raw_dir = root / "data" / "raw"
processed_dir = root / "data" / "processed"
report_dir = root / "reports"
figure_dir = report_dir / "figures"

processed_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)
figure_dir.mkdir(parents=True, exist_ok=True)
```

---

## 2. 보완 권장 항목

---

### [2-1] ch08에서 원본 데이터부터 시작하는 이유 미설명 — [섹션 5.2, 강의안 도입부]

**문제**  
ch06~ch07에서는 ch05에서 저장한 `processed_dir` 데이터를 사용했다. 그런데 ch08에서 다시 `raw_dir` 원본 데이터부터 전처리를 진행한다. "중간 프로젝트에서는 전처리 과정도 포함해야 한다"는 의도가 있을 텐데, 학생이 "왜 ch05~ch07에서 한 작업을 또 하나요?"라고 혼란을 느낄 수 있다.

**보완 지시**  
섹션 5.2 또는 강의안 도입부에 다음 설명을 추가한다:

```
⚠️ 왜 원본 데이터부터 시작하나요?

Chapter 6~7에서는 이미 전처리된 데이터를 사용했습니다.
이번 중간 프로젝트에서는 전처리부터 보고서 작성까지 전 과정을 하나의 Notebook에서
재현할 수 있도록 원본 데이터부터 시작합니다.

이것이 "재현 가능한 분석"의 의미입니다.
누군가 이 Notebook을 처음 열어도 처음부터 끝까지 실행할 수 있어야 합니다.
```

---

### [2-2] LLM 활용 내역 기록 방법 미안내 — [섹션 9 제출 체크리스트]

**문제**  
제출 체크리스트에 "LLM 활용 내용을 검토하고 기록했는가?"가 있지만, 어떻게 기록하는지 양식이나 예시가 없다. 학생이 막막해할 수 있다.

**보완 지시**  
제출 체크리스트 섹션에 다음 LLM 활용 기록 예시를 추가한다:

```markdown
## LLM 활용 기록 예시

| 활용 목적 | 프롬프트 요약 | LLM 답변 요약 | 실제 사용 여부 | 검증 결과 |
|---------|------------|-------------|------------|---------|
| 카테고리별 매출 코드 작성 | groupby + agg 코드 요청 | 코드 제안 받음 | 일부 수정 후 사용 | 결과 일치 |
| 보고서 해석 문장 작성 | 카테고리별 매출 해석 요청 | 3문단 제안 | 원인 단정 문장 삭제 후 사용 | 데이터 근거 확인 |
| 이상값 처리 판단 | 음수 수량 처리 방향 질문 | 삭제 권장 | 실습 목적으로 삭제 적용 | 삭제 기준 보고서에 기록 |
```

---

### [2-3] 평가 기준 배점 합계 확인 필요 — [섹션 8]

**문제**  
평가 기준 표의 배점 합계: 15+20+15+20+15+15 = **100점**. 이는 수치 자체는 맞지만, 각 배점에 대한 구체적인 세부 기준(예: "전처리 20점" 중 결측치 처리 5점, 중복 처리 5점 등)이 없어 학생이 무엇을 얼마나 해야 하는지 알기 어렵다.

**보완 지시**  
평가 기준 표에 각 항목의 세부 기준을 추가하거나, 다음처럼 확장한다:

```
전처리 (20점):
- 결측치 확인 및 처리 기준 기록 (5점)
- 중복 데이터 확인 (3점)
- 날짜형/숫자형 변환 (5점)
- 이상값 확인 및 처리 기준 기록 (4점)
- 전처리 전후 비교표 작성 (3점)
```

---

### [2-4] 보고서 `to_markdown()` 의존성 재반복 — [섹션 5.20]

**문제**  
ch05, ch06, ch07에서 `tabulate` 설치 안내를 섹션 5.1에 넣었는데, ch08에서도 같은 안내가 반복된다. 이는 불필요한 반복이 아니라 정상이지만, 교재 전반에서 한 번만 안내하는 구조도 고려할 수 있다.

**보완 지시**  
`to_markdown()` 사용 전에 안전한 대안 코드를 보여준다:

```python
# to_markdown()이 설치되지 않았을 때 대안
try:
    table_str = category_sales.to_markdown(index=False)
except ImportError:
    table_str = category_sales.to_string(index=False)
```

---

### [2-5] 프로젝트 자유 주제 도전 안내 없음 — [전체 구조]

**문제**  
교재가 제시한 5개 분석 질문을 그대로 따라가는 것만 안내하고, 학생 스스로 새로운 질문을 추가하거나 교재 범위를 넘는 분석을 시도하도록 격려하는 내용이 없다.

**보완 지시**  
섹션 8 평가 기준 뒤에 다음 도전 과제를 추가한다:

```
[선택 과제] 자신만의 분석 질문 추가하기

이번 프로젝트에서 제시된 5개 질문 외에, 스스로 분석 질문을 1개 이상 추가해 보세요.
추가 점수는 없지만, 추가 분석 시도 여부를 보고서에 기록하면 평가에 참고합니다.

예시:
- 특정 결제수단을 자주 사용하는 고객의 구매 금액은 다른 고객과 차이가 있는가?
- 가입 기간이 오래된 고객과 신규 고객의 구매 패턴에 차이가 있는가?
- 특정 카테고리는 특정 월에 매출이 집중되는가?
```

---

### [2-6] `product_name` 컬럼 존재 미확인 — [섹션 5.11]

**문제**  
섹션 5.11 병합 검증에서 `sales_items["product_name"].isna().sum()`을 확인하는데, `products_clean`에 실제로 `product_name` 컬럼이 있는지 미리 확인하지 않는다. 컬럼명이 다를 경우(`name`이나 `product`) `KeyError`가 발생한다.

**보완 지시**  
병합 전에 컬럼 확인 코드를 추가한다:

```python
print("products_clean 컬럼:", products_clean.columns.tolist())

# 병합 후 검증: 존재하는 컬럼만 확인
for col in ["product_name", "category"]:
    if col in sales_items.columns:
        print(f"{col} 누락:", sales_items[col].isna().sum())
    else:
        print(f"⚠️ {col} 컬럼이 없습니다.")
```

---

### [2-7] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch08은 종합 프로젝트 장이므로 새 용어보다 기존 용어 종합 정리가 더 적합하다. "정리" 섹션 10에서 사용된 함수 목록만 제시하고 표가 없다.

**보완 지시**  
섹션 10(정리) 마지막에 "이 프로젝트에서 사용한 주요 pandas·matplotlib 함수" 표를 추가한다:

| 함수 | 용도 | 사용 섹션 |
|------|------|---------|
| `pd.read_csv()` | CSV 파일 불러오기 | 5.2 |
| `df.isna().sum()` | 결측치 개수 확인 | 5.3 |
| `df.duplicated().sum()` | 중복 행 확인 | 5.3 |
| `pd.to_datetime()` | 날짜형 변환 | 5.7 |
| `df.merge()` | 두 DataFrame 병합 | 5.11 |
| `df.groupby().agg()` | 그룹 집계 | 5.12~5.14 |
| `plt.bar() / plt.plot() / plt.barh()` | 시각화 | 5.16~5.18 |
| `plt.savefig()` | 그래프 저장 | 5.16~5.18 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-2] `to_csv()` 인코딩 10회 이상 누락 (ch04~ch08 반복) | 필수 수정 |
| 🔴 높음 | [1-3] `name` 컬럼 존재 미확인 (ch06~ch08 반복) | 필수 수정 |
| 🔴 높음 | [1-4] 한글 폰트 하드코딩 (ch07~ch08 반복) | 필수 수정 |
| 🔴 높음 | [1-5] 취소 주문 인식만 하고 처리 없음 | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (390분 vs "약 4시간") | 필수 수정 |
| 🟠 중간 | [1-6] `xticks(rotation=45)` `ha="right"` 누락 (ch07~ch08 반복) | 필수 수정 |
| 🟡 낮음 | [1-7] `base_dir` 자동 감지 패턴 한계 (ch06~ch08 반복) | 필수 수정 |
| 🟢 권장 | [2-1] 원본 데이터부터 시작 이유 미설명 | 보완 권장 |
| 🟢 권장 | [2-2] LLM 활용 기록 양식 없음 | 보완 권장 |
| 🟢 권장 | [2-3] 평가 기준 세부 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-4] `to_markdown()` 의존성 안전 처리 없음 | 보완 권장 |
| 🟢 참고 | [2-5] 자유 주제 도전 과제 없음 | 보완 권장 |
| 🟢 참고 | [2-6] `product_name` 컬럼 존재 미확인 | 보완 권장 |
| 🟢 참고 | [2-7] 핵심 용어 정리 표 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- Notebook 파일명이 실제 파일(`ch08_midterm_project.ipynb`)과 일치한다. ch04·ch06·ch07의 반복 오류가 없다.
- 수업 시간 구성에서 "약 4시간"으로 명시하고 "5~6시간 분량으로 확장할 수 있습니다"라는 현실적 안내를 추가한 점이 이전 장보다 개선됐다.
- 평가 기준 표(섹션 8)가 배점·평가 기준으로 명확하게 제시되어 학생이 무엇을 기준으로 채점받는지 파악할 수 있다.
- 제출 체크리스트(섹션 9)가 14개 항목으로 매우 구체적이어서 학생이 빠뜨리기 어렵다.
- `interpretation_notes` DataFrame(섹션 5.19)에서 관찰·주의사항을 구조화해 보고서로 연결하는 패턴이 훌륭하다.
- 파일 간 키 관계 확인(섹션 5.10)을 프로젝트 흐름에 자연스럽게 포함시킨 점이 실무적으로 우수하다.
- 재현 가능한 분석 개념(섹션 3.4)을 명시적으로 설명한 점이 좋다.
- 보고서 구조(섹션 3.5)를 표로 제시해 학생이 무엇을 작성해야 할지 명확하다.

**전체적 방향 제안**  
ch08은 ch01~ch07의 내용을 통합하는 장답게 완성도가 가장 높은 편이다. 가장 시급한 수정은 **(1) `to_csv()` 인코딩 10회 이상 누락** — 중간 프로젝트 최종 산출물(CSV 파일들)을 Windows에서 Excel로 열었을 때 한글이 깨지면 제출물 평가에 바로 영향을 주기 때문이다. **(2) 취소 주문 집계 문제** — `interpretation_notes`에서 경고만 하고 실제 처리 코드가 없으면, 학생이 경고를 읽고도 어떻게 해야 할지 모른 채 프로젝트를 제출하게 된다. 나머지 이슈(한글 폰트, `name` 컬럼 등)는 ch06~ch07에서 지속 반복된 문제이므로, 한 번 패턴을 수정하면 ch08 이후 장에도 일괄 적용이 가능하다. **LLM 활용 기록 양식**은 비전공자에게 특히 유용한 추가 사항으로, ch09(LLM 프롬프트 분석) 이전에 ch08에서 먼저 안내해두면 이후 장 학습에 도움이 된다.
