# ch12 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch12_report_generation.md`

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
30+35+35+45+50+40+35+30 = **300분 = 5시간**  
본문: "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"  
2시간 격차. ch01~ch12 전 장 반복 문제.

**수정 지시**  
방법 A: 각 항목 시간을 줄여 합계 180분 이내로 재편성한다.  
방법 B: 본문을 "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"로 수정한다.

---

### [1-2] Notebook 파일명 불일치 — [섹션 5 도입부]

**문제**  
강의안 섹션 5에서 Notebook 파일명을 다음과 같이 안내한다:
```
notebooks/ch12_analysis_report_automation.ipynb
```
그러나 실제 workspace에 존재하는 파일명은:
```
notebooks/ch12_report_generation.ipynb
```
ch04, ch06, ch07, ch09, ch10, ch11에 이어 ch12에서 7번째로 반복되는 동일 패턴 오류다.

**수정 지시**  
```
# 수정 전
notebooks/ch12_analysis_report_automation.ipynb

# 수정 후
notebooks/ch12_report_generation.ipynb
```

---

### [1-3] `to_csv()` 저장에 인코딩 없음 — [섹션 5.10, 5.11]

**문제**  
섹션 5.10(`ch12_report_generation_log.csv`), 5.11(`ch12_report_validation_checklist.csv`) 2회 `to_csv()` 호출에 `encoding` 없음. 한글 컬럼이 포함된 CSV를 Windows에서 Excel로 열면 깨진다. ch04~ch12 전 장 반복 문제.

**수정 지시**  
```python
generation_log.to_csv(
    report_dir / "ch12_report_generation_log.csv",
    index=False, encoding="utf-8-sig"
)

report_validation_checklist.to_csv(
    report_dir / "ch12_report_validation_checklist.csv",
    index=False, encoding="utf-8-sig"
)
```

---

### [1-4] `base_dir` 자동 감지 패턴 한계 — [섹션 5.1]

**문제**  
ch06~ch12 모두 동일한 `Path.cwd().name == "notebooks"` 패턴 반복.

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
figure_dir = report_dir / "figures"
report_dir.mkdir(parents=True, exist_ok=True)
figure_dir.mkdir(parents=True, exist_ok=True)
```

---

### [1-5] 핵심 입력 파일 4개에 fallback 없음 — [섹션 5.3]

**문제**  
섹션 5.2에서 `file_check` DataFrame으로 파일 존재 여부를 확인하지만, 섹션 5.3에서 핵심 4개 파일을 확인 결과와 무관하게 바로 `pd.read_csv()`로 로드한다. `insight_cards`와 `interpretation_table`에는 조건부 fallback을 제공하면서 핵심 파일에는 없는 불일치가 있다. 파일이 없으면 `FileNotFoundError`가 발생하고 학생이 어디서 막혔는지 알기 어렵다.

**수정 지시**  
```python
# 핵심 파일 4개의 존재 여부 먼저 확인
core_files = ["dataset_summary", "category_sales", "monthly_sales", "customer_sales"]
missing_core = [k for k in core_files if not input_files[k].exists()]

if missing_core:
    raise FileNotFoundError(
        f"다음 파일이 없습니다: {missing_core}\n"
        "notebooks/ch08_midterm_project.ipynb 을 먼저 실행하세요."
    )

dataset_summary = pd.read_csv(input_files["dataset_summary"])
category_sales  = pd.read_csv(input_files["category_sales"])
monthly_sales   = pd.read_csv(input_files["monthly_sales"])
customer_sales  = pd.read_csv(input_files["customer_sales"])
```

---

### [1-6] 그래프 이미지 경로 존재 여부 미검증 — [섹션 5.6]

**문제**  
섹션 5.6에서 이미지 경로를 단순 문자열로 정의하고 Markdown에 삽입한다. 그러나 `figures/ch08_category_sales.png` 등이 실제로 존재하는지 확인하지 않고, 이미지가 없어도 오류 없이 Markdown 파일이 생성된다. 결과적으로 보고서를 열어봤을 때 이미지 자리에 빨간 X나 깨진 링크가 표시된다.

**수정 지시**  
섹션 5.6에 이미지 파일 존재 확인 코드를 추가한다:

```python
figure_paths = {
    "카테고리별 매출": figure_dir / "ch08_category_sales.png",
    "월별 매출": figure_dir / "ch08_monthly_sales.png",
    "구매 금액 상위 고객": figure_dir / "ch08_top_customers.png"
}

for name, path in figure_paths.items():
    status = "✅ 존재" if path.exists() else "❌ 없음 — ch08 Notebook을 먼저 실행하세요."
    print(f"{name}: {status}")
```

---

### [1-7] 보고서 저장 시 `encoding="utf-8"` — BOM 없음 — [섹션 5.9]

**문제**  
섹션 5.9에서 보고서를 저장할 때:
```python
report_path.write_text(report_text, encoding="utf-8")
```
BOM 없는 UTF-8 파일은 Mac/Linux에서는 문제없지만 Windows에서 메모장이나 일부 Markdown 뷰어로 열면 한글이 깨지거나 BOM 표시가 없어 이상하게 보일 수 있다. 또한 `to_csv()` 등 다른 저장에서는 `utf-8-sig`를 권고했는데, 이 파일만 `utf-8`을 쓰면 일관성이 없다.

**수정 지시**  
```python
# 수정 전
report_path.write_text(report_text, encoding="utf-8")

# 수정 후
report_path.write_text(report_text, encoding="utf-8-sig")
```
`ch12_llm_report_prompt.md` 저장도 동일하게 적용한다.

---

## 2. 보완 권장 항목

---

### [2-1] `top_customers_for_report`에서 `avg_order_value` 컬럼 존재 가정 — [섹션 5.4]

**문제**  
섹션 5.4에서:
```python
top_customers_for_report = top_customers[
    ["customer_label", "city", "order_count", "total_sales", "avg_order_value"]
]
```
`avg_order_value`가 `ch08_customer_sales.csv`에 없을 경우 `KeyError`가 발생한다. ch11 리뷰 [2-3]과 동일한 패턴으로, 이전 장 저장 파일의 컬럼 구조를 보장하지 않는다.

**보완 지시**  
```python
if "avg_order_value" not in top_customers.columns:
    if "order_count" in top_customers.columns and top_customers["order_count"].gt(0).all():
        top_customers["avg_order_value"] = (
            top_customers["total_sales"] / top_customers["order_count"]
        ).round(0)
    else:
        top_customers["avg_order_value"] = None
```

---

### [2-2] `ch08_dataset_summary.csv` 파일명 실제 존재 여부 불명확 — [섹션 3.4, 5.2]

**문제**  
섹션 3.4 입력 파일 목록과 섹션 5.2 코드에서 `reports/ch08_dataset_summary.csv`를 참조한다. 그러나 ch08 강의안에서 이 이름으로 파일을 저장하는지 확인이 필요하다. ch08에서 저장하는 파일명이 다르면 섹션 5.2의 `file_check`에서 `exists = False`가 되고 이후 로드에서 오류가 발생한다.

**보완 지시**  
ch08 강의안의 `to_csv()` 호출 목록과 ch12에서 참조하는 파일명을 일괄 대조하는 검수 작업이 필요하다. 불일치가 확인되면 ch12 입력 파일 목록을 실제 ch08 저장 파일명에 맞게 수정한다.

---

### [2-3] 취소 주문 포함 여부 체크리스트 미포함 — [섹션 5.11, 8]

**문제**  
섹션 5.11의 보고서 검증 체크리스트 13개 항목에 "취소 주문 처리 기준을 명시했는가?"가 없다. ch06~ch12까지 매 장에서 언급된 핵심 이슈인데 체크리스트에서 빠져 있다.

**보완 지시**  
검증 체크리스트 항목에 다음을 추가한다:
```python
"취소 주문(order_status='cancelled') 처리 기준이 보고서에 명시되었는가?",
"매출 집계에 포함·제외된 주문 상태를 보고서에 기록했는가?",
```

---

### [2-4] 연습 문제에 힌트/채점 기준 없음 — [섹션 9]

**문제**  
ch01~ch11과 동일.

**보완 지시**  
심화 과제 평가 기준 예시:

```
평가 기준 (자동 보고서):
- 분석 목적이 명확히 작성되었는가? (20%)
- 표와 그래프가 올바르게 삽입되었는가? (20%)
- 해석 문장에서 원인 단정이 없는가? (20%)
- 한계점과 다음 단계가 포함되었는가? (20%)
- 검증 체크리스트를 사용해 최종 점검을 완료했는가? (20%)
```

---

### [2-5] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch11과 동일.

**보완 지시**  
섹션 10(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| 보고서 자동 작성 | 분석 결과를 코드로 조립해 문서를 생성하는 과정 |
| 보고서 템플릿 | 섹션 구조가 미리 정의된 문서 양식 |
| `to_markdown()` | pandas DataFrame을 Markdown 표로 변환하는 메서드 |
| `Path.write_text()` | 파일에 텍스트를 저장하는 pathlib 메서드 |
| 보고서 검증 체크리스트 | 보고서 제출 전 품질을 점검하는 항목 목록 |
| 생성 로그 | 보고서 작성에 사용한 파일과 생성 결과를 기록하는 문서 |
| 한계점(Limitations) | 현재 데이터나 분석으로는 판단할 수 없는 사항 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-2] Notebook 파일명 불일치 (ch04~ch12까지 7번째) | 필수 수정 |
| 🔴 높음 | [1-5] 핵심 입력 파일 4개에 fallback 없음 | 필수 수정 |
| 🔴 높음 | [1-6] 그래프 이미지 경로 존재 여부 미검증 | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (300분 vs "약 3시간") | 필수 수정 |
| 🟠 중간 | [1-3] `to_csv()` 인코딩 2회 누락 | 필수 수정 |
| 🟠 중간 | [1-7] 보고서 저장 시 `encoding="utf-8"` (BOM 없음, 일관성 문제) | 필수 수정 |
| 🟡 낮음 | [1-4] `base_dir` 자동 감지 패턴 한계 (ch06~ch12 반복) | 필수 수정 |
| 🟢 권장 | [2-1] `avg_order_value` 컬럼 존재 가정 | 보완 권장 |
| 🟢 권장 | [2-2] `ch08_dataset_summary.csv` 파일명 실제 존재 불명확 | 보완 권장 |
| 🟢 권장 | [2-3] 취소 주문 처리 기준 체크리스트 미포함 | 보완 권장 |
| 🟢 참고 | [2-4] 연습 문제 채점 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-5] 핵심 용어 정리 섹션 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 섹션 5.2에서 보고서 입력 파일 목록을 Dictionary로 관리하고 파일 존재 여부를 `file_check` DataFrame으로 한번에 확인하는 패턴이 매우 실용적이다.
- `insight_cards`와 `interpretation_table`에 fallback 빈 DataFrame을 제공한 구조는 좋다. 다만 핵심 파일에도 같은 수준의 검증이 필요하다.
- 섹션 5.8에서 보고서 전체를 하나의 f-string으로 조립하는 방식이 직관적이며, 학생이 보고서 자동화의 핵심 아이디어를 한 코드 블록에서 파악할 수 있다.
- 섹션 5.10의 보고서 생성 로그 DataFrame이 실무 파이프라인 문서화 습관을 자연스럽게 교육한다.
- 섹션 3.2의 보고서 구조 표(10개 섹션)가 교재 전체 보고서 작성의 기준이 될 수 있다.
- 섹션 6(LLM 활용 프롬프트)에서 "보고서 구조 검토 요청" 프롬프트(6.2)와 "한계점 작성 요청" 프롬프트(6.4)가 ch09~ch11보다 더 실무 지향적으로 구체화되었다.

**전체적 방향 제안**  
ch12는 앞 장들의 결과물을 하나의 문서로 통합하는 "취합의 장"으로 교재 전체에서 중요한 위치를 차지한다. 가장 시급한 수정 사항은 세 가지다: **(1) Notebook 파일명 불일치** (7번째 반복), **(2) 핵심 입력 파일 fallback 부재** — ch12는 ch08, ch11 결과 파일에 의존하므로 파일이 없을 때 명확한 오류 메시지가 필수적이다, **(3) 그래프 이미지 경로 존재 미검증** — 보고서를 생성해도 그래프가 보이지 않으면 비전공자가 "보고서가 망가진 것 같다"고 느끼기 쉽다. 이 세 가지를 수정하면 ch12의 실습 경험이 크게 향상된다. 한편 `write_text(encoding="utf-8-sig")` 통일은 교재 전체 저장 인코딩 정책으로 확정해 ch01~ch15에 일괄 적용하는 것이 권장된다.
