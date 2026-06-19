# ch15 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch15_final_project.md`

---

## 검토 지침 (Codex Prompt Format)

**[필수 수정]** = 학습에 직접적 혼란을 야기하는 항목  
**[보완 권장]** = 추가 시 학습 효과가 크게 향상되는 항목

---

## 1. 필수 수정 항목

---

### [1-1] 수업 시간 합계와 본문 불일치 — [수업 시간 구성 표]

**문제**  
수업 시간 구성 표 합계:  
40+50+60+70+60+50+70+50+60 = **510분 = 8시간 30분**  
본문: "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"  
210분(3시간 30분) 격차. ch01~ch15 전 장 반복 문제이며 ch15가 격차 최대.

**수정 지시**  
방법 A: 각 항목 시간을 줄여 합계 300분 이내로 재편성한다.  
방법 B: 본문을 "기본 수업은 약 8~9시간을 기준으로 구성되어 있습니다. 기말 프로젝트 특성상 개인별 수행 시간이 다를 수 있습니다."로 수정한다.

---

### [1-2] `to_csv()` 저장에 인코딩 없음 — [섹션 5.4, 5.6, 5.7, 6.1~6.5, 8.2, 13]

**문제**  
아래 13곳에서 `encoding` 인수 없이 저장한다. 한글 데이터가 포함된 경우 Windows Excel에서 깨진다. ch01~ch14 전 장 반복 문제이며 ch15가 누락 최다.

| 섹션 | 파일 |
|------|------|
| 5.4 | `ch15_dataset_summary.csv` |
| 5.6 | `customers_clean.csv` |
| 5.6 | `products_clean.csv` |
| 5.6 | `orders_clean.csv` |
| 5.6 | `order_items_clean.csv` |
| 5.7 | `ch15_preprocessing_comparison.csv` |
| 6.1 | `ch15_category_sales.csv` |
| 6.2 | `ch15_monthly_sales.csv` |
| 6.3 | `ch15_customer_sales.csv` |
| 6.4 | `ch15_product_sales.csv` |
| 6.5 | `ch15_order_status_summary.csv` |
| 8.2 | `ch15_insight_cards.csv` |
| 13 | `ch15_submission_checklist.csv` |

**수정 지시**  
모든 `to_csv()` 호출에 `encoding="utf-8-sig"` 추가:
```python
# 예시
category_sales.to_csv(report_dir / "ch15_category_sales.csv", index=False, encoding="utf-8-sig")
```

---

### [1-3] `to_markdown()` 사용 — `tabulate` 패키지 의존성 미안내 — [섹션 9, 10.1]

**문제**  
섹션 9와 10.1에서 보고서 생성 시 `df.to_markdown(index=False)`를 사용한다:
```python
{llm_usage_log.to_markdown(index=False)}
{dataset_summary.to_markdown(index=False)}
# ... 등 7회 사용
```
`to_markdown()`은 `tabulate` 패키지가 설치되어 있어야 한다. 설치 없이 실행하면:
```
ImportError: tabulate is required to use DataFrame.to_markdown
```

**수정 지시**  
선택 A — 섹션 5.2 패키지 안내 또는 도입부에 다음 설치 안내 추가:
```bash
pip install tabulate
```

선택 B — `to_markdown()` 대신 직접 포맷 문자열 사용:
```python
# 상위 3행만 텍스트로 포함
top3 = category_sales.head(3)
report_text = top3.to_string(index=False)
```

`requirements.txt`에 `tabulate`가 포함되어 있는지 확인한다.

---

### [1-4] 취소 주문 포함 매출 집계 — [섹션 6.1~6.4]

**문제**  
카테고리별/월별/고객별/상품별 매출 분석(섹션 6.1~6.4)에서 취소 주문 필터링이 없다. `order_sales`를 생성할 때 `orders_clean`과 병합하지만 `order_status != 'cancelled'` 조건이 없다. 취소된 주문도 매출로 집계된다. ch06~ch15 전 장 반복 문제.

**수정 지시**  
섹션 5.8 병합 코드 직후 또는 섹션 6.1 분석 시작 전에 다음 처리를 추가한다:

```python
# 매출 분석용 주문: 취소 주문 제외
completed_orders = orders_clean[
    orders_clean["order_status"] != "cancelled"
]
print(f"전체 주문: {len(orders_clean)}, 완료 주문: {len(completed_orders)}")
print(f"제외된 취소 주문: {len(orders_clean) - len(completed_orders)}")

# 이후 order_sales 생성 시 completed_orders 사용
order_sales = order_items_clean.merge(
    completed_orders,
    on="order_id",
    how="inner"  # inner join으로 취소 주문 자동 제외
)
```

또는 섹션 6.5 주문 상태 분석이 "취소 주문 포함 전체"를, 섹션 6.1~6.4는 "완료 주문만" 집계한다는 분석 기준을 명시한다.

---

### [1-5] `groupby(["customer_id", "city"])` 설계 문제 — [섹션 6.3]

**문제**  
섹션 6.3에서:
```python
customer_sales = (
    customer_sales_base
    .groupby(["customer_id", "city"], as_index=False)
    .agg(order_count=("order_id", "nunique"), total_sales=("line_total", "sum"))
)
```
동일한 `customer_id`에 여러 `city` 값이 있거나 `city`가 `NaN`인 경우 한 고객이 여러 행으로 분리된다. ch10 [1-7]과 동일한 문제.

**수정 지시**  
고객별 집계는 `customer_id`만으로 수행하고, `city`는 병합으로 추가한다:
```python
customer_sales = (
    customer_sales_base
    .groupby("customer_id", as_index=False)
    .agg(order_count=("order_id", "nunique"), total_sales=("line_total", "sum"))
    .sort_values("total_sales", ascending=False)
)

# city는 customers_clean에서 가져옴
customer_sales = customer_sales.merge(
    customers_clean[["customer_id", "city"]].drop_duplicates(subset="customer_id"),
    on="customer_id",
    how="left"
)
```

---

### [1-6] `write_text(encoding="utf-8")` — BOM 없음 — [섹션 9, 10.1, 11]

**문제**  
섹션 9, 10.1, 11에서:
```python
llm_usage_path.write_text(llm_usage_text, encoding="utf-8")
final_report_path.write_text(final_report, encoding="utf-8")
automation_plan_path.write_text(automation_plan, encoding="utf-8")
```
ch12~ch14와 동일한 문제. Markdown 파일이지만 Windows 메모장에서 한글이 깨질 수 있다.

**수정 지시**  
```python
llm_usage_path.write_text(llm_usage_text, encoding="utf-8-sig")
final_report_path.write_text(final_report, encoding="utf-8-sig")
automation_plan_path.write_text(automation_plan, encoding="utf-8-sig")
```

---

## 2. 보완 권장 항목

---

### [2-1] `Malgun Gothic` 폰트 하드코딩 — [섹션 5.2]

**문제**  
```python
plt.rcParams["font.family"] = "Malgun Gothic"
```
ch07, ch08 등에서 반복 지적된 Windows 전용 폰트. macOS/Linux에서 깨진다.

**보완 지시**  
기말 프로젝트인 ch15에서는 해결 방법을 학생에게 직접 제시할 기회이다:
```python
import platform
import matplotlib.pyplot as plt

system = platform.system()
if system == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif system == "Darwin":  # macOS
    plt.rcParams["font.family"] = "AppleGothic"
else:  # Linux
    plt.rcParams["font.family"] = "NanumGothic"  # 설치 필요

plt.rcParams["axes.unicode_minus"] = False
```

---

### [2-2] `<strong>` HTML 태그 직접 사용 — [도입부]

**문제**  
도입부에서:
```markdown
이번 장의 핵심은 <strong>데이터 분석 전 과정을 실무 프로젝트 산출물로 완성하는 능력</strong>입니다.
```
다른 장은 `**굵게**` Markdown 문법을 사용하고, ch15만 HTML 태그를 직접 사용했다. HTML 렌더링 환경에서는 정상이지만, Markdown 편집기에서는 태그가 그대로 노출된다.

**보완 지시**  
```markdown
이번 장의 핵심은 **데이터 분석 전 과정을 실무 프로젝트 산출물로 완성하는 능력**입니다.
```

---

### [2-3] 두 가지 경로 버전 — 혼란 가능성 — [섹션 5.2]

**문제**  
섹션 5.2에서 프로젝트 루트에서 실행하는 버전과 `notebooks/` 폴더에서 실행하는 두 가지 버전을 나란히 제시한다. 어느 버전을 사용할지 명확히 안내하지 않는다.

**보완 지시**  
두 버전 앞에 다음 안내를 추가한다:
```markdown
> **어떤 경로를 사용할지 확인하세요**  
> - VS Code에서 **프로젝트 루트(`llm-data-analysis-course/`)에서 Notebook을 열고 실행한 경우**: 첫 번째 버전 사용  
> - `notebooks/` 폴더를 작업 디렉토리로 설정한 경우: 두 번째 버전 사용  
> Kernel → Restart & Run All 전에 현재 작업 디렉토리를 `Path.cwd()`로 확인하는 것이 좋습니다.
```

---

### [2-4] 전처리 함수 재사용 설명 없음 — [섹션 5.5]

**문제**  
섹션 5.5에서 `strip_string_columns()`와 `to_number()` 함수를 새로 정의하는데, ch05에서 이미 유사한 전처리 함수를 배웠다. ch15가 종합 프로젝트인 만큼 이전 장에서 작성한 코드를 재사용하거나 `src/preprocessing.py`를 활용하는 방법을 안내하면 학습 연결성이 높아진다.

**보완 지시**  
섹션 5.5 앞에 다음 안내 추가:
```markdown
이 함수들은 Chapter 5에서 배운 전처리 패턴을 기말 프로젝트용으로 정리한 것입니다. 
이미 `src/preprocessing.py`에 유사한 함수가 있다면 직접 가져와도 됩니다.
```

---

### [2-5] 제출 Notebook 실행 환경 검증 방법 없음 — [섹션 13]

**문제**  
제출 체크리스트(섹션 13)에서 "Notebook을 작성했는가?"는 있지만, "Kernel → Restart & Run All로 처음부터 끝까지 오류 없이 실행되는가?"가 없다. 학생이 오류 없는 상태로 제출했는지 확인할 기준이 부족하다.

**보완 지시**  
제출 체크리스트에 다음 항목 추가:
```python
"Notebook을 Restart & Run All로 처음부터 끝까지 오류 없이 실행했는가?",
"모든 결과 파일이 reports/ 폴더에 생성되었는가?",
"그래프 파일이 reports/figures/ 폴더에 저장되어 있는가?",
```

---

### [2-6] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch15 전 장 동일 문제. ch15는 기말 프로젝트이므로 교재 전체에서 등장한 주요 용어를 한 번에 정리하는 "전체 핵심 용어 참조표"로 확장하면 학습자에게 유용한 레퍼런스가 된다.

**보완 지시**  
섹션 15(정리) 이후에 "이 교재에서 다룬 주요 개념 정리" 표를 추가한다:

| 장 | 핵심 개념 |
|----|---------|
| ch03~04 | DataFrame, Series, read_csv, groupby, merge |
| ch05 | dropna, fillna, to_datetime, strip, to_numeric |
| ch06 | EDA, 분석 질문, value_counts, 상관관계 |
| ch07 | 막대/선/산점도, savefig, Malgun Gothic, 인사이트 연결 |
| ch08 | 중간 프로젝트 구조, 전처리 기준, 보고서 초안 |
| ch09 | LLM 프롬프트, 역할 분리, 검증, 컬럼명 확인 |
| ch10 | 코드 생성 검증, KeyError, 원인 단정 주의 |
| ch11 | 인사이트 4단계, 관찰/가설/인사이트/다음단계 |
| ch12 | 보고서 자동 작성, write_text, pathlib |
| ch13 | Make, Scenario, 보고서 발송, Gmail 연계 |
| ch14 | Airflow, DAG, Task, Operator, Dependency, Schedule |
| ch15 | 종합 프로젝트, 전 과정 통합, 자동화 설계 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-2] `to_csv()` 인코딩 13회 누락 (전 장 최다) | 필수 수정 |
| 🔴 높음 | [1-3] `to_markdown()` tabulate 패키지 의존성 미안내 → `ImportError` | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (510분 vs "약 5시간") | 필수 수정 |
| 🟠 중간 | [1-4] 취소 주문 포함 매출 집계 (ch06~ch15 반복) | 필수 수정 |
| 🟠 중간 | [1-5] `groupby(["customer_id","city"])` 설계 문제 (ch10 반복) | 필수 수정 |
| 🟡 낮음 | [1-6] `write_text(encoding="utf-8")` BOM 없음 (ch12~ch15 반복) | 필수 수정 |
| 🔴 높음 | [2-2] `<strong>` HTML 태그 직접 사용 (Markdown 비표준) | 보완 권장 |
| 🟢 권장 | [2-1] Malgun Gothic 폰트 하드코딩 (ch07~ch15 반복) | 보완 권장 |
| 🟢 권장 | [2-3] 두 가지 경로 버전 혼란 (어느 것 사용할지 미명시) | 보완 권장 |
| 🟢 권장 | [2-5] 제출 Notebook Restart & Run All 검증 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-4] 전처리 함수 재사용 안내 없음 | 보완 권장 |
| 🟢 참고 | [2-6] 전체 핵심 용어 정리 참조표 없음 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 기말 프로젝트 구조가 ch03~ch14의 모든 핵심 기술(pandas, 전처리, EDA, 시각화, LLM, 보고서, Make, Airflow)을 자연스럽게 통합한 설계가 우수하다.
- 섹션 4.3 "프로젝트 품질을 결정하는 기준" 목록이 비전공자 학생에게 좋은 체크리스트를 제공한다.
- 섹션 5.5~5.6에서 전처리 함수를 모듈화하고, `if "컬럼명" in df.columns:` 방어 코드를 사용한 것이 이전 장들보다 크게 개선되었다.
- 섹션 8의 인사이트 카드 구조(observation, caution, next_step)가 ch11에서 배운 인사이트 4단계를 실제 프로젝트에 적용하도록 안내한 것이 훌륭하다.
- 섹션 12의 평가 기준 표(배점 포함)가 학생에게 프로젝트 완성 방향을 명확히 제시한다.
- 섹션 14에서 분석 질문 검토, 보고서 검토, 발표 요약 3가지 LLM 프롬프트를 제시한 것이 실용적이다.
- 섹션 13 최종 제출 체크리스트(16개 항목)가 학생이 제출 전 자가 점검할 수 있는 구조로 잘 구성되어 있다.

**전체적 방향 제안**  
ch15는 교재 전체의 마무리이며 품질이 학생의 최종 인상을 결정한다. 가장 시급한 두 가지 이슈는 **(1) `to_markdown()` tabulate 의존성** — 실행 즉시 `ImportError`가 발생해 보고서 생성이 불가능해진다 **(2) `to_csv()` 인코딩 13회 누락** — 기말 보고서 CSV 파일을 Excel로 열 때 한글이 깨진다. 이 두 가지를 수정하면 학생이 기말 프로젝트를 오류 없이 완성할 가능성이 크게 높아진다. ch09~ch15 전 장에 공통 반복되는 `to_csv()` 인코딩 문제와 취소 주문 필터링 문제는 ch03~ch04 기초 실습 코드부터 일관되게 수정하면 교재 전체의 완성도가 향상된다.
