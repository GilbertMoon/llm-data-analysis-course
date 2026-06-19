# ch10 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch10_llm_code_generation.md`

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
30+30+40+45+40+50+45+40 = **320분 = 5시간 20분**  
본문: "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"  
2시간 20분 격차. ch01~ch10 전 장 반복 문제.

**수정 지시**  
방법 A: 각 구성 항목 시간을 줄여 합계 180분 이내로 재편성한다.  
방법 B: 본문을 "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"로 수정한다.  

또한 "최대 5시간 분량으로 확장할 수 있습니다"라는 표현도 실제 기본 합계가 5시간을 넘으므로 수정이 필요하다:
```
# 수정 전
LLM 답변 비교, 오류 사례 분석, 코드 리뷰 보고서 작성까지 포함하면 최대 5시간 분량으로 확장할 수 있습니다.

# 수정 후
LLM 답변 비교, 오류 사례 분석, 코드 리뷰 보고서 작성까지 포함하면 최대 7시간 분량으로 확장할 수 있습니다.
```

---

### [1-2] Notebook 파일명 불일치 — [섹션 5 도입부]

**문제**  
강의안 섹션 5에서 Notebook 파일명을 다음과 같이 안내한다:
```
notebooks/ch10_llm_code_generation_validation.ipynb
```
그러나 실제 workspace에 존재하는 파일명은:
```
notebooks/ch10_llm_code_generation.ipynb
```
ch04, ch06, ch07, ch09에 이어 ch10에서 5번째로 반복되는 동일 패턴 오류다.

**수정 지시**  
```
# 수정 전
notebooks/ch10_llm_code_generation_validation.ipynb

# 수정 후
notebooks/ch10_llm_code_generation.ipynb
```

---

### [1-3] `to_csv()` 저장에 인코딩 없음 — [섹션 5.3, 5.12, 5.13]

**문제**  
섹션 5.3(`ch10_schema_summary_for_code_generation.csv`), 5.12(`ch10_code_review_checklist.csv`), 5.13(`ch10_code_validation_summary.csv`) 3회 `to_csv()` 호출 모두 `encoding` 없음. 한글 컬럼(`check_item`, `main_issue`, `fixed_action` 등)이 포함된 CSV를 Windows에서 Excel로 열면 깨진다. ch04~ch10 전 장 반복 문제.

**수정 지시**  
```python
schema_summary.to_csv(
    report_dir / "ch10_schema_summary_for_code_generation.csv",
    index=False, encoding="utf-8-sig"
)

code_review_checklist.to_csv(
    report_dir / "ch10_code_review_checklist.csv",
    index=False, encoding="utf-8-sig"
)

validation_summary.to_csv(
    report_dir / "ch10_code_validation_summary.csv",
    index=False, encoding="utf-8-sig"
)
```

---

### [1-4] `base_dir` 자동 감지 패턴 한계 — [섹션 5.1]

**문제**  
ch06~ch10 모두 동일한 `Path.cwd().name == "notebooks"` 패턴 반복. VS Code 또는 Jupyter Server에서 실행 시 `cwd`가 워크스페이스 루트가 되어 조건이 False가 된다.

**수정 지시**  
ch06 리뷰 [1-8] 제안 방식으로 통일:

```python
from pathlib import Path

def find_project_root():
    candidates = [Path("."), Path("..")]
    for base in candidates:
        if (base / "data" / "processed" / "customers_clean.csv").exists():
            return base
    raise FileNotFoundError(
        "data/processed 폴더를 찾을 수 없습니다. "
        "Chapter 5 전처리를 먼저 완료하세요."
    )

root = find_project_root()
processed_dir = root / "data" / "processed"
report_dir = root / "reports"
report_dir.mkdir(parents=True, exist_ok=True)
```

---

### [1-5] 취소 주문 포함 매출 집계 — [섹션 5.6, 5.8, 5.10]

**문제**  
섹션 5.6(카테고리별 매출), 5.8(월별 매출), 5.10(고객별 구매 금액) 모두 `order_status` 필터링 없이 집계한다. 취소 주문(cancelled)이 포함된 상태에서 `line_total`을 합산하면 실제 발생 매출보다 과대 계상된다. ch06부터 ch10까지 5장 연속 반복 문제.

**수정 지시**  
섹션 5.2 또는 5.6 상단에 주의 메시지와 선택적 필터 코드를 추가한다:

```python
# 주문 상태 확인
print(orders["order_status"].value_counts())

# 취소 주문 포함 여부를 고려해 분석 범위를 결정합니다.
# 매출 분석의 경우, 실제 완료 주문만 집계하려면 아래 필터를 사용하세요.
# orders_completed = orders[orders["order_status"] != "cancelled"]
# 이 교재에서는 전체 주문을 대상으로 집계하며, 취소 주문 포함 여부를 보고서에 명시합니다.
```

또한 섹션 5.6, 5.8의 LLM 생성 코드 검증 시 "취소 주문 포함 여부 확인"을 체크리스트에 추가한다.

---

### [1-6] 코드 펜스 `~~~` 비표준 사용 — [섹션 5.14]

**문제**  
섹션 5.14의 `prompt_log` f-string 내부에서 `` ~~~ `` 코드 펜스를 사용한다. ch09와 동일한 문제로, 일부 Markdown 렌더러에서 코드 블록이 올바르게 표시되지 않는다. f-string 내에서 백틱 3개를 직접 쓰기 어렵다는 기술적 이유가 있지만, 설명 없이 비표준 방식을 사용한다.

**수정 지시**  
```python
TRIPLE_TICK = "```"

prompt_log = f"""
# Chapter 10 LLM 코드 생성 프롬프트 로그

## 1. 카테고리별 매출 코드 생성 프롬프트

{TRIPLE_TICK}text
{category_sales_prompt}
{TRIPLE_TICK}
"""
```
또는 f-string 대신 템플릿 방식으로 변경한다.

---

### [1-7] `groupby(["customer_id", "city"])` 에 `city` 포함 — [섹션 5.10]

**문제**  
섹션 5.10에서 고객별 집계를 다음과 같이 수행한다:
```python
customer_sales = (
    customer_sales_base
    .groupby(["customer_id", "city"], as_index=False)
    .agg(...)
)
```
`city`를 groupby 키에 포함하면 같은 고객이 서로 다른 도시에 등록되어 있거나 주소를 변경한 경우 결과가 분리된다. 일반적으로 고객 단위 집계는 `customer_id`만으로 groupby한 뒤 `city`를 별도로 merge하는 것이 더 안전하다.

**수정 지시**  
```python
# 수정 전
.groupby(["customer_id", "city"], as_index=False)

# 수정 후
.groupby("customer_id", as_index=False)
```
그리고 집계 후 `customers[["customer_id", "city"]]`를 merge해 도시 정보를 붙인다:
```python
customer_sales = customer_sales_base.groupby("customer_id", as_index=False).agg(
    order_count=("order_id", "nunique"),
    total_sales=("line_total", "sum")
).sort_values("total_sales", ascending=False)

customer_sales = customer_sales.merge(
    customers[["customer_id", "city"]].drop_duplicates("customer_id"),
    on="customer_id",
    how="left"
)
```

---

## 2. 보완 권장 항목

---

### [2-1] `validation_summary`의 하드코딩된 평가 값 — [섹션 5.13]

**문제**  
섹션 5.13에서 `llm_output_status`와 `main_issue`, `fixed_action`이 미리 채워진 DataFrame으로 제공된다:
```python
"llm_output_status": ["사용 가능", "보완 후 사용", "보완 후 사용", "수정 필요"]
```
이 값은 "강사가 미리 채운 예시"인지, "학생이 실제로 평가해서 채워야 하는 양식"인지 명확하지 않다. 학생들이 예시를 그대로 제출할 가능성이 있다.

**보완 지시**  
DataFrame 앞에 다음 안내를 추가한다:

```python
# 아래 표는 예시입니다.
# 실제 LLM 코드를 검증한 후 각 항목을 직접 평가하고 수정하세요.
# llm_output_status: "사용 가능" / "보완 후 사용" / "수정 필요" 중 선택
```

---

### [2-2] `check_columns` 함수가 매 장마다 재정의 — [섹션 5.4]

**문제**  
ch10 섹션 5.4에서 `check_columns` 함수를 새로 정의한다. 이전 장(ch09 등)에서도 유사한 검증 코드가 반복 등장했다. 매 장마다 동일한 유틸리티 함수를 재정의하면 학생이 함수 위치를 찾기 어렵고, 함수 내용이 약간씩 다를 경우 혼란이 생긴다.

**보완 지시**  
중간~후반부 장의 도입부에 다음 안내를 추가한다:

```python
# check_columns는 실습에서 자주 쓰는 유틸리티 함수입니다.
# src/analysis.py 또는 src/utils.py에 포함시키면 import 한 줄로 재사용할 수 있습니다.
# 이 장에서는 함수를 직접 정의해 사용하지만, 프로젝트 규모가 커지면 공통 모듈로 분리하는 것이 좋습니다.
```

---

### [2-3] 프롬프트 6.4에서 "LLM 생성 코드 검토 요청"의 실제 답변 예시 없음 — [섹션 6.4]

**문제**  
섹션 6.4의 프롬프트는 LLM에게 "이 코드가 바로 실행 가능한지 검토해 주세요"를 요청한다. ch09에서도 지적했던 문제인데, 프롬프트는 있지만 LLM이 어떤 답변을 할 것인지 예시가 없다. 학생이 LLM 답변을 받은 뒤 어떻게 판단하고 코드를 수정해야 하는지 연결이 안 된다.

**보완 지시**  
섹션 7.1 또는 6.4 뒤에 LLM 답변 예시를 추가한다:

```markdown
### LLM 답변 예시

> [검토 결과]  
> 이 코드는 바로 실행할 수 없습니다.  
> order_items에는 category 컬럼이 없습니다.  
> category는 products 테이블에 있으므로, 먼저 product_id 기준으로 merge해야 합니다.  
>
> [수정 코드]  
> ```python
> sales_items = order_items.merge(products, on="product_id", how="left")
> category_sales = sales_items.groupby("category")["line_total"].sum()
> ```

학생이 위 답변을 받았을 때 확인해야 할 사항:
- 제안된 컬럼명(`category`, `line_total`)이 실제 데이터와 일치하는가?
- 병합 후 행 수 확인 코드가 없다면 직접 추가해야 한다.
```

---

### [2-4] 연습 문제에 힌트/채점 기준 없음 — [섹션 9]

**문제**  
ch01~ch09와 동일.

**보완 지시**  
심화 과제 평가 기준 예시:

```
평가 기준 (코드 검증 보고서):
- 데이터 구조 요약을 실제 컬럼명 기반으로 작성했는가? (20%)
- 실행 전 컬럼 존재 여부를 check_columns()로 확인했는가? (20%)
- 병합 전후 행 수와 집계 총합을 비교했는가? (20%)
- 오류 수정 프롬프트에 코드·오류 메시지·데이터 구조가 모두 포함되었는가? (20%)
- 개인정보 익명화 처리를 적용했는가? (20%)
```

---

### [2-5] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch09와 동일.

**보완 지시**  
섹션 10(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| 정적 검증(Static Validation) | 코드 실행 전 컬럼명·데이터 구조를 확인하는 단계 |
| 동적 검증(Dynamic Validation) | 코드 실행 후 결과(행 수·총합·누락값)를 확인하는 단계 |
| 오류 수정 루프 | 실행 → 오류 확인 → 프롬프트 수정 → 재실행을 반복하는 과정 |
| 익명화(Anonymization) | 개인을 식별할 수 있는 정보를 제거하거나 대체하는 과정 |
| `KeyError` | DataFrame에 존재하지 않는 컬럼명을 접근할 때 발생하는 Python 오류 |
| `errors="coerce"` | `pd.to_datetime()` 등에서 변환 실패 시 오류 대신 NaT/NaN을 반환하는 옵션 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-2] Notebook 파일명 불일치 (ch04·ch06·ch07·ch09에 이어 5번째) | 필수 수정 |
| 🔴 높음 | [1-5] 취소 주문 포함 매출 집계 (ch06~ch10 5장 연속 반복) | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (320분 vs "약 3시간") | 필수 수정 |
| 🟠 중간 | [1-3] `to_csv()` 인코딩 3회 누락 (ch04~ch10 반복) | 필수 수정 |
| 🟠 중간 | [1-7] `groupby(["customer_id", "city"])` 설계 문제 | 필수 수정 |
| 🟡 낮음 | [1-4] `base_dir` 자동 감지 패턴 한계 (ch06~ch10 반복) | 필수 수정 |
| 🟡 낮음 | [1-6] `~~~` 코드 펜스 비표준 사용 (ch09 반복) | 필수 수정 |
| 🟢 권장 | [2-1] `validation_summary` 하드코딩 값 — 학생이 예시를 그대로 제출 위험 | 보완 권장 |
| 🟢 권장 | [2-3] LLM 답변 예시 없음 (ch09 반복) | 보완 권장 |
| 🟢 참고 | [2-2] `check_columns` 함수 매 장 재정의 | 보완 권장 |
| 🟢 참고 | [2-4] 연습 문제 채점 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-5] 핵심 용어 정리 섹션 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 섹션 3.2에서 LLM 코드 생성의 장점과 위험을 동일한 표 형식으로 대비하여 제시한 구성이 균형 잡혀 있다.
- 섹션 3.5에서 실행 전 검증과 실행 후 검증을 별도 표로 분리한 것이 매우 효과적이다. 특히 비전공자가 "코드가 실행됐으니 맞겠지"라는 함정에 빠지는 것을 예방할 수 있다.
- 섹션 5.4의 `check_columns` 함수 도입이 실용적이며 재사용 가능한 코드 패턴을 가르친다.
- 섹션 5.11에서 `debug_prompt`를 f-string으로 동적으로 생성하는 패턴이 ch09보다 진화된 구조다.
- 섹션 5.13의 `validation_summary` DataFrame으로 코드 검증 결과를 정형 데이터로 기록하는 방식이 실무와 유사하다.
- 섹션 6.5에서 "코드 실행 결과 검증 요청" 프롬프트를 별도로 제공한 점이 ch09에 비해 개선된 부분이다.
- 섹션 7에서 각 분석 과제별 "검증 포인트" 목록이 간결하고 핵심을 잘 짚는다.

**전체적 방향 제안**  
ch10은 ch09의 "프롬프트 작성" 단계에서 한 걸음 더 나아가 "생성된 코드 검증"으로 범위를 자연스럽게 확장하는 구성이 좋다. 다만 **[1-7] `groupby(["customer_id", "city"])` 집계 설계 문제**는 학생들이 이 패턴을 정석으로 학습할 수 있으므로 수정이 중요하다. 또한 **[2-1] `validation_summary` 하드코딩 문제**는 미래 장에서도 반복될 수 있는 패턴인데, 학생이 직접 채워야 하는 양식인지 교사 예시인지를 명확히 구분하지 않으면 복사-붙여넣기 제출이 양산된다. **가장 긍정적인 점**은 `check_columns` 함수와 실행 전·후 검증 구분이 비전공자에게 "코드 실행 = 검증 완료"가 아님을 단계별로 체험하게 해주는 구성이라는 것이다.
