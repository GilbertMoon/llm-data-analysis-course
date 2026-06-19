# ch11 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch11_insight_generation.md`

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
수업 시간 구성 표 합계 (연습 문제 60~90분 제외):  
30+40+45+45+40+45+45+40 = **330분 = 5시간 30분**  
본문: "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"  
2시간 30분 격차. ch01~ch11 전 장 반복 문제.

**수정 지시**  
방법 A: 각 항목 시간을 줄여 합계 180분 이내로 재편성한다.  
방법 B: 본문을 "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"로 수정하고, "최대 5시간" 표현도 조정한다.

---

### [1-2] Notebook 파일명 불일치 — [섹션 5 도입부]

**문제**  
강의안 섹션 5에서 Notebook 파일명을 다음과 같이 안내한다:
```
notebooks/ch11_insight_interpretation.ipynb
```
그러나 실제 workspace에 존재하는 파일명은:
```
notebooks/ch11_insight_generation.ipynb
```
ch04, ch06, ch07, ch09, ch10에 이어 ch11에서 6번째로 반복되는 동일 패턴 오류다.

**수정 지시**  
```
# 수정 전
notebooks/ch11_insight_interpretation.ipynb

# 수정 후
notebooks/ch11_insight_generation.ipynb
```
ch01~ch15 전체의 Notebook 파일명을 실제 파일과 일괄 대조하는 검수 과정이 필요하다.

---

### [1-3] `to_csv()` 저장에 인코딩 없음 — [섹션 5.8, 5.9, 5.10]

**문제**  
섹션 5.8(`ch11_interpretation_table.csv`), 5.9(`ch11_insight_cards.csv`), 5.10(`ch11_llm_interpretation_review.csv`) 3회 `to_csv()` 호출 모두 `encoding` 없음. 한글 컬럼·내용이 포함된 CSV를 Windows에서 Excel로 열면 깨진다. ch04~ch11 전 장 반복 문제.

**수정 지시**  
```python
interpretation_table.to_csv(
    report_dir / "ch11_interpretation_table.csv",
    index=False, encoding="utf-8-sig"
)

insight_cards.to_csv(
    report_dir / "ch11_insight_cards.csv",
    index=False, encoding="utf-8-sig"
)

llm_interpretation_review.to_csv(
    report_dir / "ch11_llm_interpretation_review.csv",
    index=False, encoding="utf-8-sig"
)
```

---

### [1-4] `base_dir` 자동 감지 패턴 한계 — [섹션 5.1]

**문제**  
ch06~ch11 모두 동일한 `Path.cwd().name == "notebooks"` 패턴 반복. VS Code에서 실행 시 `cwd`가 워크스페이스 루트가 되어 조건이 False가 된다.

**수정 지시**  
ch06 리뷰 [1-8] 제안 방식으로 통일:

```python
from pathlib import Path

def find_project_root():
    candidates = [Path("."), Path("..")]
    for base in candidates:
        if (base / "reports").is_dir():
            return base
    raise FileNotFoundError(
        "reports 폴더를 찾을 수 없습니다. "
        "Chapter 8 또는 이전 실습을 먼저 완료하세요."
    )

root = find_project_root()
report_dir = root / "reports"
report_dir.mkdir(parents=True, exist_ok=True)
```

---

### [1-5] 이전 장 결과 파일 의존성 미검증 — [섹션 5.2]

**문제**  
섹션 5.2에서 ch08 분석 결과 파일을 다음과 같이 로드한다:
```python
category_sales = pd.read_csv(report_dir / "ch08_category_sales.csv")
monthly_sales = pd.read_csv(report_dir / "ch08_monthly_sales.csv")
customer_sales = pd.read_csv(report_dir / "ch08_customer_sales.csv")
```
세 가지 문제가 있다:
1. 이 파일명이 ch08 Notebook에서 실제로 저장한 파일명과 일치하는지 확인이 필요하다.
2. 파일이 없을 경우 오류만 발생하고 학생이 어느 단계를 다시 실행해야 하는지 명확하지 않다.
3. 주석에 "Chapter 8 또는 Chapter 10"이라고 하면서 실제 코드에는 `ch08_*` 만 쓰고 있어 일관성이 없다.

**수정 지시**  
파일 존재 여부 확인 코드를 추가한다:

```python
required_files = [
    report_dir / "ch08_category_sales.csv",
    report_dir / "ch08_monthly_sales.csv",
    report_dir / "ch08_customer_sales.csv"
]

missing = [str(f) for f in required_files if not f.exists()]
if missing:
    raise FileNotFoundError(
        f"다음 파일이 없습니다: {missing}\n"
        "notebooks/ch08_midterm_project.ipynb 을 먼저 실행하세요."
    )

category_sales = pd.read_csv(report_dir / "ch08_category_sales.csv")
monthly_sales = pd.read_csv(report_dir / "ch08_monthly_sales.csv")
customer_sales = pd.read_csv(report_dir / "ch08_customer_sales.csv")
```

---

### [1-6] `top_customer` 변수 선언 후 미사용 — [섹션 5.7]

**문제**  
섹션 5.7에서 다음과 같이 변수를 선언한다:
```python
top_customer = customer_sales_sorted.iloc[0]
```
그러나 바로 다음 `customer_interpretation` f-string 안에서 `top_customer`는 한 번도 사용되지 않는다. 변수만 선언하고 쓰지 않으면 학생이 "왜 선언했지?"라고 혼란스럽고, 실수로 빠뜨린 것처럼 보인다.

**수정 지시**  
두 가지 선택지:

선택 A — 변수를 f-string에 활용:
```python
top_customer = customer_sales_sorted.iloc[0]
top_customer_id = top_customer["customer_id"]
top_customer_sales = top_customer["total_sales"]

customer_interpretation = f"""
구매 금액 기준 1위 고객(ID: {top_customer_id})의 총 구매 금액은 {top_customer_sales:,.0f}원입니다.
다만 총 구매 금액이 높다는 사실만으로 충성 고객이라고 단정할 수는 없습니다.
...
"""
```

선택 B — 변수 선언을 제거하고 `.iloc[0]` 사용을 다음 단계에서만 한다.

---

## 2. 보완 권장 항목

---

### [2-1] `diff()` / `pct_change()` 첫 행 NaN 미설명 — [섹션 5.6]

**문제**  
섹션 5.6에서 전월 대비 증감률을 다음과 같이 계산한다:
```python
monthly_sales_sorted["sales_change"] = monthly_sales_sorted["total_sales"].diff()
monthly_sales_sorted["sales_change_ratio"] = (
    monthly_sales_sorted["total_sales"].pct_change() * 100
).round(2)
```
`diff()`와 `pct_change()`는 첫 행에서 이전 값이 없으므로 `NaN`을 반환한다. 이를 설명하지 않으면 결과표를 처음 보는 비전공자가 "왜 첫 달 데이터가 비어 있나요?"라고 당황한다.

**보완 지시**  
계산 후 결과에 대한 설명을 추가한다:

```python
# diff()와 pct_change()는 이전 행과의 차이를 계산합니다.
# 첫 번째 행은 이전 데이터가 없으므로 NaN(비어 있음)으로 표시됩니다.
# NaN은 계산 불가능한 것이 아니라, 비교할 이전 값이 없다는 의미입니다.
monthly_sales_sorted["sales_change"] = monthly_sales_sorted["total_sales"].diff()
```

---

### [2-2] ch11에서 취소 주문 처리 기준 미확정 — [섹션 7.4]

**문제**  
섹션 7.4에서 "취소 주문이 매출 계산에 포함되어 있다면 실제 매출이 과대 계산될 수 있습니다"라고 경고하지만, 실습 코드에서는 ch08 결과 파일을 그대로 불러오기 때문에 실제로 취소 주문이 포함되어 있는지 학생이 확인할 방법이 없다. ch06~ch11까지 6장 연속으로 이 문제가 언급되거나 반복된다.

**보완 지시**  
섹션 5.3(분석 결과 기본 검증)에 다음 확인 코드를 추가한다:

```python
# ch08 결과가 취소 주문을 포함했는지 확인
# (ch08 Notebook에서 order_status 필터를 적용했다면 이 확인은 생략 가능)
# 아래는 참고용: ch08에서 저장하기 전 취소 주문 포함 여부를 메모해두는 것이 좋습니다.

print("⚠️ 이 분석 결과는 ch08에서 저장한 데이터를 사용합니다.")
print("ch08 실습에서 취소 주문(order_status='cancelled')을 필터링했는지 확인하세요.")
print("포함 여부에 따라 실제 매출과 차이가 있을 수 있습니다.")
```

---

### [2-3] `ch08_customer_sales.csv`의 컬럼 구조 보장 없음 — [섹션 5.7]

**문제**  
섹션 5.7에서 `customer_sales`에 `avg_order_value` 컬럼이 없을 경우 직접 계산한다:
```python
if "avg_order_value" not in customer_sales_sorted.columns:
    customer_sales_sorted["avg_order_value"] = (...)
```
이 패턴 자체는 좋지만, ch08에서 저장한 파일에 `order_count` 컬럼이 보장되어 있는지도 확인해야 한다. `order_count`가 없으면 이 계산도 `KeyError`를 발생시킨다.

**보완 지시**  
```python
required_columns = ["customer_id", "total_sales", "order_count"]
missing_cols = [c for c in required_columns if c not in customer_sales.columns]
if missing_cols:
    raise ValueError(f"customer_sales에 필요한 컬럼이 없습니다: {missing_cols}")
```

---

### [2-4] 인사이트 카드 `caution` 컬럼이 체계적이지 않음 — [섹션 5.9]

**문제**  
인사이트 카드 DataFrame에 `caution` 컬럼이 있어 "단정하지 말 것" 경고를 포함한다. 이 구조는 좋지만, `caution` 항목이 단지 "하면 안 된다"를 반복하는 형태로 작성되어 있어 학생이 왜 그것이 위험한지 이해하기 어렵다. 예를 들어 "충성 고객이라고 단정할 수 없습니다" 대신 "총 구매 금액 = 충성 고객의 충분 조건이 아님 (반복 구매 여부 미확인)"처럼 구체적 이유를 제시하면 교육적 가치가 높아진다.

**보완 지시**  
`caution` 컬럼 내용을 이유 중심으로 수정한다:

```python
"caution": [
    "판매 수량·단가·프로모션 정보가 없어 매출의 원인을 선호도로 단정할 수 없습니다.",
    "프로모션·계절 정보가 없어 매출 증가 원인을 단정할 수 없습니다.",
    "반복 구매율·최근 구매일 등 충성도 지표가 없어 충성 고객으로 단정할 수 없습니다."
]
```

---

### [2-5] 연습 문제에 힌트/채점 기준 없음 — [섹션 9]

**문제**  
ch01~ch10과 동일.

**보완 지시**  
심화 과제 평가 기준 예시:

```
평가 기준 (인사이트 보고서):
- 관찰·가설·추가 질문을 명확히 구분했는가? (25%)
- 원인 단정 표현(고객 선호, 프로모션 성공 등)을 피했는가? (25%)
- 매출을 판매 수량과 단가로 분해했는가? (25%)
- 인사이트가 다음 행동 또는 추가 분석으로 연결되는가? (25%)
```

---

### [2-6] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch10과 동일. ch11 신규 용어: 관찰, 해석, 가설, 인사이트, 실행 제안, 증거 수준, 인사이트 카드, 과장된 해석, 안전한 해석.

**보완 지시**  
섹션 10(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| 관찰(Observation) | 데이터에서 직접 확인한 사실 |
| 해석(Interpretation) | 관찰 결과의 의미 설명 |
| 가설(Hypothesis) | 원인에 대해 조심스럽게 제시하는 가능성 |
| 인사이트(Insight) | 의사결정에 도움이 되는 핵심 메시지 |
| 실행 제안(Action) | 다음 행동 또는 추가 분석 방향 |
| 증거 수준 | 어떤 주장이 데이터로 얼마나 뒷받침되는지의 정도 |
| 인사이트 카드 | 분석 결과를 구조화된 양식으로 정리한 문서 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-2] Notebook 파일명 불일치 (ch04~ch11까지 6번째) | 필수 수정 |
| 🔴 높음 | [1-5] 이전 장 결과 파일 의존성 미검증 (ch08 파일명 미확인) | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (330분 vs "약 3시간") | 필수 수정 |
| 🟠 중간 | [1-3] `to_csv()` 인코딩 3회 누락 (ch04~ch11 반복) | 필수 수정 |
| 🟠 중간 | [1-6] `top_customer` 변수 선언 후 미사용 | 필수 수정 |
| 🟡 낮음 | [1-4] `base_dir` 자동 감지 패턴 한계 (ch06~ch11 반복) | 필수 수정 |
| 🟢 권장 | [2-2] 취소 주문 포함 여부 경고만 있고 확인 코드 없음 | 보완 권장 |
| 🟢 권장 | [2-1] `diff()`/`pct_change()` 첫 행 NaN 미설명 | 보완 권장 |
| 🟢 권장 | [2-3] `customer_sales`의 컬럼 구조 보장 코드 없음 | 보완 권장 |
| 🟢 참고 | [2-4] `caution` 항목이 이유 없이 "단정 금지"만 반복 | 보완 권장 |
| 🟢 참고 | [2-5] 연습 문제 채점 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-6] 핵심 용어 정리 섹션 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 섹션 3.1~3.4에서 "관찰 → 해석 → 가설 → 인사이트 → 실행 제안"의 5단계 구분을 표와 예시 문장으로 체계적으로 설명한 것이 ch09~ch10보다 한 단계 심화된 구성이다.
- 섹션 3.4의 "위험한 문장 vs 안전한 문장" 대비 표가 비전공자에게 매우 실용적이다.
- 섹션 3.5에서 "현재 데이터로 확인 가능 / 추가 분석 필요 / 현재 데이터로 판단 불가"를 명시적으로 구분한 것이 교육적으로 우수하다.
- 섹션 5.9의 인사이트 카드 DataFrame이 7개 컬럼으로 구조화되어 있어, 학생이 이 양식을 바탕으로 자신의 결과를 정리하는 데 유용한 템플릿을 제공한다.
- 섹션 5.10의 `llm_interpretation_review`에서 LLM 문장 → 문제점 → 안전한 문장의 3열 구조가 직관적이다.
- 섹션 6(LLM 활용 프롬프트)에서 실제 집계 결과 수치를 LLM 입력용 텍스트로 사용하는 패턴이 ch09 [1-5]에서 지적한 방식을 자연스럽게 보완한다.

**전체적 방향 제안**  
ch11은 이 교재 전체에서 "결과를 어떻게 읽는가"를 다루는 핵심 장이다. 관찰·해석·가설 구분은 데이터 리터러시의 핵심인데, 이를 5단계 표와 예시 문장으로 일관되게 설명한 구성은 매우 탁월하다. 가장 중요한 수정 사항은 두 가지다: **(1) Notebook 파일명 불일치** (6번째 반복)와 **(2) ch08 결과 파일 의존성 미검증** — 학생이 ch08을 실행하지 않았거나 파일명이 다를 경우 ch11 시작 단계에서 막힌다. ch11에서 `reports/ch08_*.csv` 파일이 없을 때의 대응 방법을 더 명확히 안내해야 한다. ch08 저장 파일명과 ch11 로드 파일명의 일치 여부를 교재 전체 수준에서 일괄 검수하는 것이 권장된다.
