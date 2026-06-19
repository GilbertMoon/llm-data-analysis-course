# ch09 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch09_llm_prompt_analysis.md`

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
30+35+40+45+40+45+35+40 = **310분 = 5시간 10분**  
본문에 "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"라고 적혀 있다.  
2시간 이상 격차로, ch01~ch09 전 장 반복 문제다.

**수정 지시**  
방법 A: 표 항목을 재조정해 합계를 180분(3시간) 이내로 맞춘다.  
방법 B: 본문을 "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"로 수정한다.

---

### [1-2] Notebook 파일명 불일치 — [섹션 5, 강의안 도입부]

**문제**  
강의안 섹션 5에서 Notebook 파일명을 다음과 같이 안내한다:
```
notebooks/ch09_llm_prompt_analysis_assistant.ipynb
```
그러나 실제 workspace에 존재하는 파일명은:
```
notebooks/ch09_llm_prompt_analysis.ipynb
```
ch04(`ch04_pandas_basic_analysis`), ch06(`ch06_eda_analysis_questions`), ch07(`ch07_data_visualization`)에 이어 ch09에서도 동일 패턴 오류가 4번째로 반복된다.

**수정 지시**  
```
# 수정 전
notebooks/ch09_llm_prompt_analysis_assistant.ipynb

# 수정 후
notebooks/ch09_llm_prompt_analysis.ipynb
```
전체 장(ch01~ch15)의 Notebook 파일명 일괄 검토가 필요하다.

---

### [1-3] `to_csv()` 저장에 인코딩 없음 — [섹션 5.3, 5.4, 5.8, 5.9]

**문제**  
섹션 5.3(`ch09_dataset_summary_for_llm.csv`), 5.4(`ch09_column_summary_for_llm.csv`), 5.8(`ch09_llm_review_checklist.csv`), 5.9(`ch09_llm_usage_log.csv`) 4회 `to_csv()` 호출 모두 `encoding` 옵션이 없다. Windows에서 한글이 포함된 CSV를 Excel로 열면 깨진다. ch04~ch09 전 장 반복 문제다.

**수정 지시**  
```python
dataset_summary.to_csv(
    report_dir / "ch09_dataset_summary_for_llm.csv", 
    index=False, encoding="utf-8-sig"
)
column_summary.to_csv(
    report_dir / "ch09_column_summary_for_llm.csv", 
    index=False, encoding="utf-8-sig"
)
llm_review_checklist.to_csv(
    report_dir / "ch09_llm_review_checklist.csv", 
    index=False, encoding="utf-8-sig"
)
llm_usage_log.to_csv(
    report_dir / "ch09_llm_usage_log.csv", 
    index=False, encoding="utf-8-sig"
)
```

---

### [1-4] `base_dir` 자동 감지 패턴 한계 — [섹션 5.1]

**문제**  
ch06~ch09까지 동일한 `Path.cwd().name == "notebooks"` 패턴이 반복된다. VS Code에서 실행 시 `cwd`가 워크스페이스 루트여서 조건이 False가 되어 `processed_dir`가 잘못 설정될 수 있다.

**수정 지시**  
ch06 리뷰 [1-8]에서 제안한 파일 존재 기반 자동 감지 방식으로 통일한다:

```python
from pathlib import Path

def find_project_root():
    candidates = [Path("."), Path("..")]
    for base in candidates:
        if (base / "data" / "processed" / "customers_clean.csv").exists():
            return base
    raise FileNotFoundError(
        "data/processed 폴더를 찾을 수 없습니다. "
        "Chapter 5 또는 Chapter 8 전처리를 먼저 완료하세요."
    )

root = find_project_root()
processed_dir = root / "data" / "processed"
report_dir = root / "reports"
report_dir.mkdir(parents=True, exist_ok=True)
```

---

### [1-5] LLM 입력용 텍스트와 파일 저장 방식의 혼동 위험 — [섹션 5.7]

**문제**  
섹션 5.7에서 다음 코드가 등장한다:
```python
category_sales_text = category_sales.to_csv(index=False)
print(category_sales_text)
```
`to_csv(index=False)` 를 파일 경로 없이 호출하면 파일 저장이 아니라 **문자열 반환**이 된다. 비전공자는 이 동작 방식을 모르고, "파일이 저장되지 않았는데 왜 됐지?" 또는 반대로 "이게 저장 코드인가?"라고 혼동할 수 있다. 또한 학생이 이 패턴을 잘못 이해해 원본 raw 데이터를 같은 방식으로 LLM에 붙여 넣을 위험이 있다.

**수정 지시**  
코드에 명확한 설명을 추가한다:

```python
# to_csv()에 파일 경로를 지정하지 않으면 파일이 아닌 문자열로 반환됩니다.
# 이 방식은 LLM에 붙여 넣을 텍스트를 만들 때만 사용합니다.
category_sales_text = category_sales.to_csv(index=False)
print(category_sales_text)

# ⚠️ 이 방식은 집계 결과처럼 요약된 데이터에만 사용합니다.
# 원본 고객 데이터나 주문 상세 전체 데이터를 이 방식으로 LLM에 넣지 마세요.
```

---

### [1-6] `order_items`의 `line_total` 컬럼 존재 가정 — [섹션 5.7]

**문제**  
섹션 5.7에서 `sales_items = order_items.merge(products, ...)` 후 `category_sales` 집계에서 `line_total` 컬럼을 사용한다. 그런데 `order_items`(= `order_items_clean.csv`)에 `line_total`이 실제로 있는지 확인하지 않는다. ch05 전처리에서 `line_total`을 생성했지만, 해당 결과를 저장했을 때만 존재한다. 체크 없이 사용하면 `KeyError`가 발생한다.

**수정 지시**  
섹션 5.7에 다음 확인 코드를 추가한다:

```python
# line_total이 없으면 다시 생성
if "line_total" not in order_items.columns:
    if {"quantity", "unit_price"}.issubset(order_items.columns):
        order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]
    else:
        raise ValueError("line_total, quantity, unit_price 컬럼이 모두 없습니다.")
```

---

## 2. 보완 권장 항목

---

### [2-1] 사용할 LLM 도구 안내 없음 — [핵심 개념 3.1, 실습 5]

**문제**  
ch09 전체에서 어떤 LLM 도구를 사용해야 하는지 안내가 없다. ChatGPT, Claude, Gemini, GitHub Copilot 등 여러 선택지가 있는데, 학생이 어떤 것을 써야 하는지 모른다. ch01~ch02 환경 설정에서 LLM 도구를 설정했다면 연결 설명이 있어야 한다.

**보완 지시**  
섹션 5 도입부 또는 핵심 개념 3.1에 다음 내용을 추가한다:

```
이번 장에서는 다음 LLM 도구 중 하나를 사용할 수 있습니다.

- ChatGPT (https://chat.openai.com) — 가장 널리 사용
- Claude (https://claude.ai) — 긴 텍스트 처리에 강점
- Gemini (https://gemini.google.com) — Google 계정으로 사용

학교/직장 계정 정책에 따라 사용 가능한 서비스가 다를 수 있습니다.
이 교재에서는 프롬프트 예시만 제공하므로, 선택한 LLM에 직접 입력해 보세요.

⚠️ 기업 내부망 또는 학교 규정에 따라 외부 LLM 사용이 제한될 수 있습니다.
```

---

### [2-2] `.format()` 문법 미설명 — [섹션 5.5, 5.6]

**문제**  
섹션 5.5, 5.6에서 Python 문자열 `.format()` 메서드를 사용해 프롬프트 템플릿을 채운다:
```python
prompt_category_sales = code_prompt_template.format(
    analysis_goal="...",
    data_structure=data_structure_text,
    task="..."
)
```
이 문법을 설명하지 않으면 비전공자가 `{analysis_goal}` 같은 자리 표시자가 왜 있는지 이해하지 못한다.

**보완 지시**  
섹션 5.5 앞에 다음 설명을 추가한다:

```python
# 문자열 템플릿 활용
# {변수명} 자리 표시자가 있는 문자열을 .format()으로 채울 수 있습니다.
template = "안녕하세요, {name}님! {goal}을 도와드리겠습니다."
result = template.format(name="분석가", goal="카테고리별 매출 분석")
print(result)
# 출력: 안녕하세요, 분석가님! 카테고리별 매출 분석을 도와드리겠습니다.

# 이 방식을 사용하면 프롬프트 구조는 유지하면서 내용만 쉽게 바꿀 수 있습니다.
```

---

### [2-3] f-string과 `.format()` 혼용 — [섹션 5.5~5.11]

**문제**  
섹션 5.5~5.6은 `"".format()` 방식, 섹션 5.7(해석 프롬프트), 5.10~5.11(보고서)은 `f"..."` f-string 방식이 혼용된다. 일관성 없는 혼용은 비전공자에게 "어느 방식이 맞는 건가요?"라는 의문을 준다.

**보완 지시**  
한 가지 방식으로 통일하거나, 처음 두 방식이 등장할 때 차이를 설명한다:

```python
# 방법 1: .format() - 템플릿을 재사용할 때 편리
template = "목적: {goal}"
result = template.format(goal="매출 분석")

# 방법 2: f-string - 변수를 직접 삽입할 때 편리 (Python 3.6 이상)
goal = "매출 분석"
result = f"목적: {goal}"

# 이 교재에서는 재사용 템플릿은 .format(), 일회성 문자열은 f-string을 사용합니다.
```

---

### [2-4] LLM 프롬프트 실행 결과 예시 없음 — [섹션 5.5~5.7, 섹션 6]

**문제**  
프롬프트를 만들고 `print()`로 출력하는 것까지만 안내하고, 실제 LLM에서 어떤 답변이 나오는지 예시가 없다. 학생이 LLM에서 답변을 받은 뒤 어떻게 검증해야 하는지 구체적인 과정을 보여주지 않는다.

**보완 지시**  
섹션 5.7 또는 섹션 7에 LLM 답변 예시와 검증 과정을 추가한다:

```markdown
## LLM 답변 예시와 검증

### 요청
category별 매출 집계 코드 생성 요청

### LLM 답변 예시
```python
category_sales = order_items.groupby("category")["line_total"].sum()
```

### 검증 결과
❌ 문제: order_items에는 "category" 컬럼이 없습니다.
   products 테이블과 먼저 merge해야 합니다.

### 수정 코드
```python
sales_items = order_items.merge(products, on="product_id", how="left")
category_sales = sales_items.groupby("category")["line_total"].sum()
```
```

---

### [2-5] 프롬프트 로그 저장 시 `~~~` 코드 펜스 사용 — [섹션 5.10]

**문제**  
섹션 5.10에서 Markdown 보고서 저장 시 코드 블록에 `` ~~~ `` 펜스를 사용한다. 일반적인 Markdown 관례는 ` ``` `(백틱 3개)인데, ` ~~~ `를 사용하면 일부 Markdown 렌더러에서 코드 블록이 올바르게 표시되지 않을 수 있다.

**보완 지시**  
f-string 내 백틱 충돌 문제를 해결하면서 표준 코드 펜스로 변경한다:

```python
# f-string 안에서 백틱 3개를 직접 쓰기 어려울 때
TRIPLE_TICK = "```"

prompt_log = f"""
# Chapter 9 LLM 프롬프트 로그

## 1. 카테고리별 매출 분석 코드 요청 프롬프트

{TRIPLE_TICK}text
{prompt_category_sales}
{TRIPLE_TICK}
"""
```

또는 `textwrap.dedent()`와 조합해 처리한다.

---

### [2-6] 연습 문제에 힌트/채점 기준 없음 — [섹션 9]

**문제**  
ch01~ch08과 동일.

**보완 지시**  
심화 과제 평가 기준 예시:

```
평가 기준 (LLM 활용 보고서):
- 원본 개인정보를 LLM에 입력하지 않았는가? (20%)
- 프롬프트에 역할·목적·데이터 구조·제약 조건이 포함되었는가? (20%)
- LLM이 만든 코드에서 실제 컬럼명과 다른 오류를 발견했는가? (20%)
- 해석 문장에서 원인 단정 표현을 수정했는가? (20%)
- LLM 활용 기록표를 작성했는가? (20%)
```

---

### [2-7] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch08과 동일. ch09 신규 용어/개념: 프롬프트(prompt), 역할 지정(role prompting), 제약 조건(constraint), 환각(hallucination), 컨텍스트 창(context window), 프롬프트 엔지니어링, 제로샷(zero-shot), f-string 템플릿, `.format()`, LLM 활용 기록.

**보완 지시**  
섹션 10(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| 프롬프트(Prompt) | LLM에게 작업을 요청하는 입력 텍스트 |
| 역할 지정 | "당신은 X입니다"로 LLM 답변 방향 설정 |
| 환각(Hallucination) | LLM이 없는 사실을 있는 것처럼 생성하는 현상 |
| 컨텍스트 창 | LLM이 한 번에 처리할 수 있는 텍스트 길이 제한 |
| 제로샷(Zero-shot) | 예시 없이 바로 요청하는 방식 |
| 프롬프트 엔지니어링 | 더 나은 답변을 얻기 위해 프롬프트를 설계하는 기술 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-2] Notebook 파일명 불일치 (ch04·ch06·ch07 이후 4번째) | 필수 수정 |
| 🔴 높음 | [1-5] `to_csv()`를 문자열 변환 용도로 사용 시 미설명 및 오남용 위험 | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (310분 vs "약 3시간") | 필수 수정 |
| 🟠 중간 | [1-3] `to_csv()` 인코딩 4회 누락 (ch04~ch09 반복) | 필수 수정 |
| 🟠 중간 | [1-6] `line_total` 컬럼 존재 미확인 | 필수 수정 |
| 🟡 낮음 | [1-4] `base_dir` 자동 감지 패턴 한계 (ch06~ch09 반복) | 필수 수정 |
| 🟢 권장 | [2-1] LLM 도구 선택 안내 없음 | 보완 권장 |
| 🟢 권장 | [2-2] `.format()` 문법 미설명 | 보완 권장 |
| 🟢 권장 | [2-4] LLM 답변 예시와 검증 과정 없음 | 보완 권장 |
| 🟢 참고 | [2-3] f-string과 `.format()` 혼용 | 보완 권장 |
| 🟢 참고 | [2-5] 코드 펜스 `~~~` 비표준 사용 | 보완 권장 |
| 🟢 참고 | [2-6] 연습 문제 채점 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-7] 핵심 용어 정리 섹션 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 섹션 3.2에서 LLM에게 입력 가능한 정보와 주의해야 할 정보를 두 개의 표로 대비시켜 명확하게 구분한 점이 매우 좋다.
- 섹션 3.4에서 나쁜 프롬프트와 좋은 프롬프트를 직접 대비해 보여주는 방식이 학습 효과가 높다.
- 섹션 3.5의 "LLM 답변 검증이 필요한 이유" 표가 실제 오류 유형을 구체적으로 제시해 실용적이다.
- 섹션 5.8의 `llm_review_checklist`를 DataFrame으로 만들어 CSV 저장까지 이어지는 구조가 체계적이다.
- 섹션 7.3의 위험한 해석 문장 vs 안전한 표현 비교가 비전공자에게 매우 유용하다.
- 섹션 6(LLM 활용 프롬프트)에서 6가지 유형의 프롬프트를 모두 제시해 실제 활용 시나리오를 풍부하게 다룬다.
- LLM 활용 기록표(섹션 5.9)를 체계적으로 제시해 ch08 리뷰 [2-2]에서 요청한 내용을 충족한다.

**전체적 방향 제안**  
ch09는 이 교재에서 가장 독창적인 장 중 하나다. LLM 활용에 관한 내용을 단순히 소개하는 데 그치지 않고, 실습 코드로 프롬프트 템플릿·검증 체크리스트·활용 기록을 직접 만들어 저장하는 과정이 잘 설계되어 있다. 가장 중요한 개선 사항은 두 가지다: **(1) Notebook 파일명 불일치**는 학생이 첫 실습 진입 단계에서 막히게 하므로 즉시 수정이 필요하다. **(2) LLM 답변 예시와 검증 과정 미제시** — 프롬프트를 만드는 법은 잘 가르치지만 답변을 어떻게 검증하는지 구체적인 사례를 보여주지 않는다. 잘못된 LLM 코드 예시(존재하지 않는 컬럼 사용)와 그것을 발견·수정하는 과정을 하나의 예시로 추가하면 ch09의 핵심 메시지인 "사람이 최종 검증"이 훨씬 구체적으로 전달된다.
