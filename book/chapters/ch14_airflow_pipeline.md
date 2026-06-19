첨부된 `ch09_llm_prompt_analysis.html`, `ch09_llm_prompt_analysis.md`, `ch09_llm_prompt_analysis_images.md`를 기준으로 Chapter 9 HTML 파일을 최종 검수하고 보완해 주세요.

중요: 현재 `ch09_llm_prompt_analysis.html`은 제목과 일부 표/이미지는 정상이나, 목록 변환, strong 태그 처리, 코드 블록 변환, 중첩 코드펜스 처리에 큰 문제가 있습니다. 단순 부분 수정보다 `ch09_llm_prompt_analysis.md`를 기준으로 HTML 본문을 다시 안정적으로 생성하는 방식이 안전합니다.

작업 대상 파일:

* 수정 대상: `ch09_llm_prompt_analysis.html`
* 원본 기준: `ch09_llm_prompt_analysis.md`
* 이미지 기준: `ch09_llm_prompt_analysis_images.md`

최종 목표:

* 원본 Markdown의 구조와 내용을 누락 없이 HTML로 변환
* 교재/전자책/PDF 출력용 HTML로 안정화
* 코드 블록을 학습자가 그대로 복사해서 실행할 수 있게 보존
* raw Markdown 문법이 HTML 본문에 노출되지 않게 수정
* Chapter 9 이미지 5개가 정상 삽입되었는지 검증

반드시 수정할 핵심 문제:

1. 제목 구조 확인
   현재 `<title>`과 `<h1>`은 정상으로 보입니다. 그래도 최종 검증해 주세요.

정상 상태:

```html
<title>9장 LLM 프롬프트 기반 분석 보조</title>
```

```html
<h1>9장 LLM 프롬프트 기반 분석 보조</h1>
```

최종 HTML에는 `<h1>`이 정확히 1개만 있어야 합니다.

2. strong 태그 이스케이프 문제 수정
   현재 HTML 본문에 다음처럼 strong 태그가 문자로 노출되어 있습니다.

```html
&lt;strong&gt;LLM을 분석 보조 도구로 활용하고 사람이 최종 검증하는 능력&lt;/strong&gt;
```

이것은 잘못된 변환입니다. 다음처럼 실제 HTML 태그로 처리해 주세요.

```html
<strong>LLM을 분석 보조 도구로 활용하고 사람이 최종 검증하는 능력</strong>
```

단, 코드 블록 내부의 `<`, `>`는 안전하게 이스케이프되어도 됩니다. 본문 문장에 있는 `<strong>`만 실제 태그로 렌더링되게 처리해 주세요.

최종 HTML에 다음 패턴이 남아 있으면 안 됩니다.

```text
&lt;strong&gt;
&lt;/strong&gt;
```

3. Markdown 목록 변환 오류 수정
   현재 원본 Markdown의 `* 항목` 목록이 HTML에서 다음처럼 문단으로 남아 있습니다.

```html
<p>* 데이터 분석에서 LLM이 도와줄 수 있는 작업과 한계를 설명할 수 있습니다.</p>
<p>* 원본 데이터를 직접 입력하지 않고 안전한 요약 정보를 만들 수 있습니다.</p>
```

이것은 잘못된 변환입니다. 반드시 다음처럼 `<ul><li>` 구조로 변환해 주세요.

```html
<ul>
  <li>데이터 분석에서 LLM이 도와줄 수 있는 작업과 한계를 설명할 수 있습니다.</li>
  <li>원본 데이터를 직접 입력하지 않고 안전한 요약 정보를 만들 수 있습니다.</li>
</ul>
```

다음 섹션의 모든 bullet 목록을 확인해 주세요.

* 1. 학습 목표
* 2. 이번 장에서 만들 결과물
* 6. LLM 활용 프롬프트 내부의 일반 설명 목록
* 7. 결과 해석
* 8. 실무 적용 포인트
* 9. 연습 문제
* 10. 정리
* 코드 블록이 아닌 본문 영역에 있는 모든 `* 항목`

최종 HTML에 다음 패턴이 남아 있으면 안 됩니다.

```text
<p>* 
```

4. 코드 블록 누락 문제 복구
   현재 HTML의 코드 블록은 원본 Markdown 대비 첫 줄 또는 앞부분이 많이 누락되어 있습니다. 이 문제는 매우 중요합니다.

원본 Markdown 기준으로 다음 핵심 코드가 HTML에 반드시 포함되어야 합니다.

```python
from pathlib import Path
import pandas as pd
```

```python
processed_dir = Path("data/processed")
report_dir = Path("reports")
report_dir.mkdir(parents=True, exist_ok=True)
```

```python
processed_dir = Path("../data/processed")
report_dir = Path("../reports")
report_dir.mkdir(parents=True, exist_ok=True)
```

```python
customers = pd.read_csv(processed_dir / "customers_clean.csv")
products = pd.read_csv(processed_dir / "products_clean.csv")
orders = pd.read_csv(processed_dir / "orders_clean.csv")
order_items = pd.read_csv(processed_dir / "order_items_clean.csv")
```

```python
datasets = {
    "customers": customers,
    "products": products,
    "orders": orders,
    "order_items": order_items
}
```

```python
dataset_summary = []

for name, df in datasets.items():
    dataset_summary.append({
        "dataset": name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_list": ", ".join(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicated_rows": int(df.duplicated().sum())
    })

dataset_summary = pd.DataFrame(dataset_summary)
dataset_summary
```

```python
dataset_summary.to_csv(report_dir / "ch09_dataset_summary_for_llm.csv", index=False)
```

```python
column_summary_rows = []

for name, df in datasets.items():
    for col in df.columns:
        column_summary_rows.append({
            "dataset": name,
            "column": col,
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isna().sum()),
            "unique_count": int(df[col].nunique())
        })

column_summary = pd.DataFrame(column_summary_rows)
column_summary
```

```python
column_summary.to_csv(report_dir / "ch09_column_summary_for_llm.csv", index=False)
```

```python
code_prompt_template = """
당신은 Python 데이터 분석 강사입니다.

분석 목적:
{analysis_goal}

데이터 구조:
{data_structure}

요청 작업:
{task}

제약 조건:
- 실제 데이터에 없는 컬럼명을 만들지 마세요.
- pandas 코드로 작성해 주세요.
- 초보자가 이해할 수 있도록 주석을 포함해 주세요.
- 병합이 필요한 경우 병합 전후 행 수 확인 코드를 포함해 주세요.
- 날짜 변환이 필요한 경우 변환 실패 건수 확인 코드를 포함해 주세요.

출력 형식:
1. 코드
2. 코드 설명
3. 실행 후 확인해야 할 사항
"""
```

```python
data_structure_text = """
order_items:
- order_id
- product_id
- quantity
- unit_price
- line_total

products:
- product_id
- product_name
- category
- price
"""
```

```python
prompt_category_sales = code_prompt_template.format(
    analysis_goal="온라인 쇼핑몰 데이터에서 카테고리별 매출을 계산하려고 합니다.",
    data_structure=data_structure_text,
    task="""
1. order_items와 products를 product_id 기준으로 병합
2. category별 line_total 합계 계산
3. total_sales 기준 내림차순 정렬
4. sales_ratio 컬럼 생성
"""
)

print(prompt_category_sales)
```

```python
error_prompt_template = """
당신은 Python pandas 오류 해결 도우미입니다.

다음 코드에서 오류가 발생했습니다.

코드:
{code}

오류 메시지:
{error_message}

데이터 구조:
{data_structure}

요청:
1. 오류 원인을 설명해 주세요.
2. 수정 코드를 작성해 주세요.
3. 비슷한 오류를 예방하는 방법을 알려 주세요.

주의:
- 실제 데이터에 없는 컬럼명을 새로 만들지 마세요.
- 답변은 초보자도 이해할 수 있게 작성해 주세요.
"""
```

```python
sample_error_prompt = error_prompt_template.format(
    code='category_sales = order_items.groupby("category")["line_total"].sum()',
    error_message="KeyError: 'category'",
    data_structure=data_structure_text
)

print(sample_error_prompt)
```

```python
sales_items = order_items.merge(
    products,
    on="product_id",
    how="left"
)
```

```python
category_sales_text = category_sales.to_csv(index=False)
print(category_sales_text)
```

```python
interpretation_prompt = f"""
당신은 데이터 분석 보고서 작성 도우미입니다.

다음은 온라인 쇼핑몰 카테고리별 매출 분석 결과입니다.

{category_sales_text}

요청:
1. 결과를 초보자도 이해할 수 있게 해석해 주세요.
2. 데이터로 확인한 관찰 내용과 원인 가설을 구분해 주세요.
3. 데이터에 없는 원인을 단정하지 마세요.
4. 추가로 확인해야 할 분석 질문 3개를 제안해 주세요.
5. 보고서에 넣을 수 있는 문장으로 작성해 주세요.
"""

print(interpretation_prompt)
```

```python
llm_review_checklist = pd.DataFrame({
    "check_item": [
        "실제 컬럼명과 일치하는가?",
        "존재하지 않는 데이터를 가정하지 않았는가?",
        "병합 기준이 올바른가?",
        "날짜 변환이 필요한 경우 처리했는가?",
        "결측치나 변환 실패를 확인했는가?",
        "코드가 실제로 실행 가능한가?",
        "해석에서 원인을 단정하지 않았는가?",
        "데이터에 없는 내용을 추측하지 않았는가?",
        "개인정보나 원본 데이터를 노출하지 않았는가?",
        "추가 검증이 필요한 부분을 명시했는가?"
    ],
    "result": ["□"] * 10,
    "memo": [""] * 10
})

llm_review_checklist
```

```python
llm_review_checklist.to_csv(report_dir / "ch09_llm_review_checklist.csv", index=False)
```

```python
llm_usage_log = pd.DataFrame({
    "step": [
        "데이터 구조 설명",
        "pandas 코드 생성",
        "오류 해결",
        "결과 해석",
        "보고서 문장 개선"
    ],
    "purpose": [
        "데이터셋 구조를 설명하고 분석 전 확인 사항 정리",
        "카테고리별 매출 분석 코드 초안 생성",
        "KeyError 원인 파악과 수정 코드 작성",
        "카테고리별 매출 결과 해석",
        "보고서 문장 자연스럽게 개선"
    ],
    "input_type": [
        "컬럼명, shape, 결측치 요약",
        "데이터 구조와 분석 목적",
        "오류 메시지와 코드",
        "집계 결과표",
        "보고서 초안 문장"
    ],
    "validation_point": [
        "데이터에 없는 분석을 제안했는지 확인",
        "컬럼명과 병합 기준 확인",
        "수정 코드 실행 여부 확인",
        "원인 단정 여부 확인",
        "과장 표현과 추측 확인"
    ]
})

llm_usage_log
```

```python
llm_usage_log.to_csv(report_dir / "ch09_llm_usage_log.csv", index=False)
```

5. 빈 코드 블록 제거 또는 복구
   현재 HTML에는 빈 코드 블록이 여러 개 있습니다.

예:

```html
<pre><code class="language-text"></code></pre>
```

이런 빈 코드 블록은 원본 내용으로 복구하거나, 원본에 실제 코드가 없다면 제거해 주세요.

특히 다음 코드 블록은 반드시 복구되어야 합니다.

```text
notebooks/ch09_llm_prompt_analysis_assistant.ipynb
```

다음 CSV 저장 코드들도 빈 코드 블록으로 남아 있으면 안 됩니다.

```python
dataset_summary.to_csv(report_dir / "ch09_dataset_summary_for_llm.csv", index=False)
```

```python
column_summary.to_csv(report_dir / "ch09_column_summary_for_llm.csv", index=False)
```

```python
llm_review_checklist.to_csv(report_dir / "ch09_llm_review_checklist.csv", index=False)
```

```python
llm_usage_log.to_csv(report_dir / "ch09_llm_usage_log.csv", index=False)
```

6. 중첩 코드펜스가 포함된 5.10 섹션 재작성
   현재 `5.10 LLM 프롬프트 로그 저장하기` 부분이 HTML에서 심하게 깨져 있습니다.

문제 예시:

* `class="language-\`python"` 같은 비정상 class 발생
* 하나의 Python 코드가 여러 코드 블록으로 쪼개짐
* Markdown 보고서 안에 들어가야 할 ```text 코드펜스가 HTML 코드 블록 구조를 깨뜨림

이 섹션은 원본 Markdown을 그대로 변환하지 말고, HTML 변환이 깨지지 않도록 Python 문자열 내부의 코드펜스를 안전하게 구성해 주세요.

권장 수정 코드:

```python
prompt_log = f"""
# Chapter 9 LLM 프롬프트 로그

## 1. 카테고리별 매출 분석 코드 요청 프롬프트

~~~text
{prompt_category_sales}
~~~

## 2. 오류 해결 요청 프롬프트

~~~text
{sample_error_prompt}
~~~

## 3. 분석 결과 해석 요청 프롬프트

~~~text
{interpretation_prompt}
~~~

## 4. 사용 시 주의사항

- 원본 고객명, 이메일, 주문 상세 전체 데이터를 LLM에 입력하지 않았습니다.
- 컬럼명과 집계 결과 중심으로 질문했습니다.
- LLM 답변은 실제 코드 실행과 결과 비교를 통해 검증해야 합니다.
"""

prompt_log_path = report_dir / "ch09_llm_prompt_log.md"
prompt_log_path.write_text(prompt_log, encoding="utf-8")
```

위처럼 Markdown 내부 코드펜스를 백틱 3개가 아니라 `~~~text`로 바꾸면 HTML 변환기가 중첩 코드펜스를 오해할 가능성이 줄어듭니다.

최종 HTML에는 다음 패턴이 남아 있으면 안 됩니다.

```text
class="language-`python"
class="language-`"
```

7. 5.11 LLM 검증 요약 보고서 코드 복구
   현재 HTML에서는 `review_summary = f"""`가 빠지고, Markdown 보고서 본문이 Python 코드처럼 잘못 들어간 부분이 있습니다.

다음 형태로 복구해 주세요.

```python
review_summary = f"""
# Chapter 9 LLM 답변 검증 요약

## 1. 검증 목적

LLM이 생성한 데이터 분석 코드와 해석 문장이 실제 데이터 구조와 일치하는지 확인합니다.

## 2. 데이터 구조 요약

{dataset_summary.to_markdown(index=False)}

## 3. LLM 활용 기록

{llm_usage_log.to_markdown(index=False)}

## 4. 검증 체크리스트

{llm_review_checklist.to_markdown(index=False)}

## 5. 주요 검증 포인트

- LLM이 실제 데이터에 없는 컬럼명을 사용하지 않았는지 확인합니다.
- 병합 기준이 실제 키 관계와 맞는지 확인합니다.
- 날짜 변환과 결측치 확인 코드가 포함되어 있는지 확인합니다.
- 결과 해석에서 데이터에 없는 원인을 단정하지 않았는지 확인합니다.
- 개인정보나 원본 데이터를 LLM에 입력하지 않았는지 확인합니다.

## 6. 결론

LLM은 코드 초안 작성과 해석 문장 작성에 유용하지만, 최종 분석 결과는 반드시 사람이 검증해야 합니다.
"""

review_summary_path = report_dir / "ch09_llm_review_summary.md"
review_summary_path.write_text(review_summary, encoding="utf-8")
```

8. 경로 설정 코드 개선
   현재 원본에는 프로젝트 루트 실행용 경로와 notebooks 폴더 실행용 경로가 따로 있습니다. 초보자가 두 코드를 모두 실행하지 않도록, 가능하면 다음 자동 경로 설정 코드로 대체해 주세요.

```python
from pathlib import Path
import pandas as pd

current_dir = Path.cwd()

if current_dir.name == "notebooks":
    base_dir = current_dir.parent
else:
    base_dir = current_dir

processed_dir = base_dir / "data" / "processed"
report_dir = base_dir / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

print("processed_dir:", processed_dir)
print("report_dir:", report_dir)
```

이 코드를 사용하면 노트북을 프로젝트 루트에서 실행하든 `notebooks` 폴더 안에서 실행하든 같은 방식으로 동작합니다.

9. `to_markdown()` 사용 안내 추가
   보고서 생성 코드에서 다음 함수들이 사용됩니다.

```python
dataset_summary.to_markdown(index=False)
llm_usage_log.to_markdown(index=False)
llm_review_checklist.to_markdown(index=False)
```

환경에 따라 `tabulate` 패키지가 필요할 수 있으므로 `5.11 LLM 검증 요약 보고서 작성하기` 앞이나 `5.1 기본 패키지 불러오기` 근처에 다음 안내를 추가해 주세요.

```text
to_markdown()을 사용하려면 환경에 따라 tabulate 패키지가 필요할 수 있습니다. 오류가 발생하면 터미널 또는 노트북에서 pip install tabulate를 실행하세요.
```

필요하면 다음 코드 블록도 추가해 주세요.

```text
pip install tabulate
```

10. 이미지 figure 확인
    Chapter 9 이미지 생성 프롬프트 기준으로 본문 삽입용 이미지는 다음 5개입니다.

```text
ch09_llm_analysis_assistant_flow.png
ch09_prompt_structure.png
ch09_llm_answer_validation_flow.png
ch09_llm_practice_workflow.png
ch09_llm_usage_deliverables.png
```

각 이미지에는 다음 구조가 있어야 합니다.

```html
<figure class="figure">
  <img src="../assets/images/ch09/파일명.png" alt="적절한 대체 텍스트">
  <figcaption>그림 9-x. 캡션</figcaption>
</figure>
```

캡션은 다음과 일치해야 합니다.

```text
그림 9-1. LLM 기반 데이터 분석 보조 흐름도
그림 9-2. 데이터 분석 프롬프트 구조
그림 9-3. LLM 답변 검증 흐름도
그림 9-4. LLM 활용 분석 보조 실습 흐름도
그림 9-5. LLM 활용 산출물 구성
```

이미지 경로는 HTML 파일 위치에 따라 통일해 주세요.

기준:

* HTML이 `book/chapters/ch09_llm_prompt_analysis.html`에 위치한다면 `../assets/images/ch09/...` 유지
* HTML이 `book/ch09_llm_prompt_analysis.html`에 위치한다면 `assets/images/ch09/...`로 수정
* 한 파일 안에서 `../assets`, `./assets`, `/assets`가 섞이면 안 됩니다.

11. 목차 추가 여부 확인
    현재 CSS에는 `.toc` 스타일이 들어가 있으나, 실제 목차 HTML이 없을 수 있습니다. 교재용 HTML이라면 `<h1>` 아래에 목차를 추가해 주세요.

포함할 목차:

* 수업 시간 구성
* 1. 학습 목표
* 2. 이번 장에서 만들 결과물
* 3. 핵심 개념
* 4. 실습 시나리오
* 5. 실습 코드
* 6. LLM 활용 프롬프트
* 7. 결과 해석
* 8. 실무 적용 포인트
* 9. 연습 문제
* 10. 정리

각 heading에는 id를 부여하고 목차 링크가 정상 동작하도록 해 주세요.

12. CSS 유지 및 최종 점검
    현재 CSS는 대체로 양호합니다. 다음 항목은 유지해 주세요.

```css
@media print {
  thead {
    display: table-header-group;
  }

  tr {
    page-break-inside: avoid;
    break-inside: avoid;
  }

  p,
  li {
    orphans: 2;
    widows: 2;
  }
}

@media (max-width: 640px) {
  body {
    padding: 28px 18px 56px;
    font-size: 15px;
  }

  table {
    font-size: 0.9rem;
  }

  th,
  td {
    padding: 8px 10px;
  }
}
```

13. 최종 검증 기준
    수정 후 반드시 다음을 확인해 주세요.

* `<title>`이 `9장 LLM 프롬프트 기반 분석 보조`인지
* `<h1>`이 정확히 1개인지
* 본문에 `&lt;strong&gt;`가 노출되지 않는지
* `<p>* ` 형태의 목록 변환 실패가 남아 있지 않은지
* raw Markdown 표 문법이 문단으로 남아 있지 않은지
* 원본 Markdown의 코드 블록 38개가 HTML에서도 38개 수준으로 유지되는지
* 빈 코드 블록이 없는지
* `from pathlib import Path`가 포함되어 있는지
* `customers = pd.read_csv(processed_dir / "customers_clean.csv")`가 포함되어 있는지
* `datasets = {`가 포함되어 있는지
* `dataset_summary = []`가 포함되어 있는지
* `code_prompt_template = """`가 포함되어 있는지
* `error_prompt_template = """`가 포함되어 있는지
* `prompt_log = f"""`가 포함되어 있는지
* `review_summary = f"""`가 포함되어 있는지
* `class="language-\`python"`또는`class="language-`"` 패턴이 남아 있지 않은지
* figure가 총 5개인지
* Chapter 9 이미지 5개 파일명이 모두 포함되어 있는지
* 파일 끝이 `</main>`, `</body>`, `</html>` 구조로 정상 종료되는지

권장 작업 방식:
현재 HTML은 부분 패치보다 `ch09_llm_prompt_analysis.md`를 기준으로 본문을 다시 생성하는 편이 안전합니다. 특히 5.10 섹션의 중첩 코드펜스 때문에 기존 변환기가 코드를 쪼개고 있으므로, 해당 섹션은 `~~~text`를 사용하는 방식으로 원본 내용을 안전하게 재작성해 주세요.

수정 결과는 `ch09_llm_prompt_analysis.html`에 반영하고, 마지막에 다음 형식으로 변경 요약을 작성해 주세요.

```text
수정 요약:
- strong 태그 이스케이프 문제 수정
- 목록 변환 오류 수정
- 빈 코드 블록 복구
- 코드 블록 누락 복구
- 5.10 중첩 코드펜스 문제 수정
- 5.11 review_summary 코드 복구
- 이미지 figure 5개 검증
- 경로 설정 코드 개선
- to_markdown/tabulate 안내 추가
- 최종 HTML 구조 검증 완료
```
