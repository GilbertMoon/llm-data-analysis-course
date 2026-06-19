# ch07 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch07_visualization.md`

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
30+35+40+40+35+45+30+30 = **285분 = 4시간 45분**  
본문에 "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"라고 적혀 있다.  
1시간 45분 격차로, ch01~ch07 전체에서 반복되는 구조적 오류다.

**수정 지시**  
방법 A: 표 항목을 재조정해 합계를 180분(3시간) 이내로 맞춘다.  
방법 B: 본문을 "기본 수업은 약 4~5시간을 기준으로 구성되어 있습니다"로 수정한다.

---

### [1-2] Notebook 파일명 불일치 — [섹션 5, 강의안 도입부]

**문제**  
강의안 섹션 5에서 Notebook 파일명을 다음과 같이 안내한다:
```
notebooks/ch07_data_visualization.ipynb
```
그러나 실제 workspace에 존재하는 파일명은:
```
notebooks/ch07_visualization.ipynb
```
ch04(`ch04_pandas_basic_analysis` vs `ch04_pandas_basic`), ch06(`ch06_eda_analysis_questions` vs `ch06_eda_questions`)에 이어 ch07에서도 동일 패턴 오류가 반복된다.

**수정 지시**  
```
# 수정 전
notebooks/ch07_data_visualization.ipynb

# 수정 후
notebooks/ch07_visualization.ipynb
```
전체 장(ch01~ch15)의 Notebook 파일명을 실제 파일과 일괄 검토·수정이 필요하다.

---

### [1-3] 그래프 코드가 show 버전과 save 버전으로 중복 제시 — [섹션 5.4~5.9 전체]

**문제**  
섹션 5.4, 5.5, 5.6, 5.7, 5.8, 5.9에서 각 그래프를 두 번씩 코드 블록으로 제시한다:
- 첫 번째: `plt.show()` 만 있는 버전
- 두 번째: `plt.savefig()` + `plt.show()`를 추가한 버전

두 블록이 거의 동일해 코드 양이 불필요하게 두 배가 된다. 학생은 "어느 것을 실행해야 하나요?"라는 혼란을 겪게 된다.

**수정 지시**  
두 블록을 항상 저장하는 단일 블록으로 합친다. `plt.savefig()`가 있어도 `plt.show()`가 뒤에 있으면 Notebook에서 정상 출력된다:

```python
# 수정 예시 (섹션 5.4)
plt.figure(figsize=(10, 5))

plt.bar(
    category_sales["category"],
    category_sales["total_sales"]
)

plt.title("카테고리별 매출")
plt.xlabel("카테고리")
plt.ylabel("총매출")
plt.xticks(rotation=45, ha="right")  # ha="right" 추가 권장
plt.tight_layout()

plt.savefig(figure_dir / "ch07_category_sales_bar.png", dpi=150)
plt.show()
```

섹션 5.4~5.9 전체에 동일하게 적용한다.

---

### [1-4] `plt.show()` 호출 순서와 `plt.savefig()` 관계 미설명 — [섹션 5.4]

**문제**  
중복 코드 블록이 있기 때문에 학생이 첫 번째(show only) 블록을 실행한 뒤 두 번째(save 포함) 블록을 실행하면, 첫 번째 `plt.show()` 이후 Jupyter는 figure를 정리한다. 두 번째 블록에서 새 `plt.figure()`를 생성하므로 저장은 정상 작동하지만, 이 동작 방식을 설명하지 않아 학생이 불필요한 시행착오를 겪는다.

**수정 지시**  
[1-3] 수정과 함께 다음 설명을 섹션 5.4 도입부에 추가한다:

```
⚠️ 저장과 출력 순서 주의

plt.savefig()는 반드시 plt.show() 보다 먼저 호출해야 합니다.
plt.show()를 먼저 호출하면 figure가 초기화되어 빈 이미지가 저장됩니다.

올바른 순서:
1. plt.figure()
2. 그래프 코드
3. plt.savefig()   ← 저장 먼저
4. plt.show()      ← 출력은 나중
```

---

### [1-5] 한글 폰트 설정이 Windows에만 작동하는 하드코딩 — [섹션 5.1]

**문제**  
섹션 5.1에서 `plt.rcParams["font.family"] = "Malgun Gothic"` 하나만 제공한다. "수업 환경이 Windows라면 Malgun Gothic을 기준으로 설명하면 됩니다"라고 적혀 있지만, Mac이나 Linux 학생은 섹션 5.1을 그대로 실행하면 오류 없이 실행되어도 한글이 □□□로 표시된다.

**수정 지시**  
OS 자동 감지 코드로 교체한다:

```python
import platform
import matplotlib.pyplot as plt

system = platform.system()

if system == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif system == "Darwin":  # macOS
    plt.rcParams["font.family"] = "AppleGothic"
else:  # Linux
    plt.rcParams["font.family"] = "NanumGothic"

plt.rcParams["axes.unicode_minus"] = False

# 설정 결과 확인
print(f"OS: {system}, 폰트: {plt.rcParams['font.family']}")
```

또는 최소한 핵심 개념 3.4의 OS별 설정 예시를 실습 코드 5.1에서도 명시적으로 안내하고, 학생이 본인 환경에 맞게 선택하도록 지시한다.

---

### [1-6] `plt.xticks(rotation=45)` 레이블이 잘릴 수 있음 — [섹션 5.4]

**문제**  
`plt.xticks(rotation=45)` 기본 설정에서 회전된 레이블이 막대 중앙 위에 배치되어 막대그래프를 가리거나 잘릴 수 있다. `ha="right"`(수평 정렬을 오른쪽으로) 설정이 없으면 텍스트가 비대칭으로 배치된다.

**수정 지시**  
모든 `xticks(rotation=45)` 호출에 `ha="right"` 추가:

```python
plt.xticks(rotation=45, ha="right")
```

섹션 5.4, 5.5, 5.9에 동일하게 적용한다.

---

### [1-7] `base_dir` 자동 감지 패턴 한계 — [섹션 5.1]

**문제**  
ch06과 동일한 `Path.cwd().name == "notebooks"` 패턴이 ch07에서도 반복된다. ch06 리뷰 [1-8]에서 지적한 VS Code 실행 환경에서의 한계가 동일하게 존재한다.

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
        "Chapter 5 전처리를 먼저 완료하고 CSV 파일을 저장하세요."
    )

root = find_project_root()
processed_dir = root / "data" / "processed"
report_dir = root / "reports"
figure_dir = report_dir / "figures"
figure_dir.mkdir(parents=True, exist_ok=True)
```

---

### [1-8] `customers` 테이블의 `name` 컬럼 존재 미확인 — [섹션 5.3]

**문제**  
섹션 5.3에서 `groupby(["customer_id", "name", "city"])`를 사용하는데, `customers_clean.csv`에 실제로 `name` 컬럼이 있는지 확인 없이 사용한다. `name`이 없으면 `KeyError`가 발생한다. ch06 리뷰 [2-4]에서도 동일하게 지적했다.

**수정 지시**  
병합 전에 컬럼 존재를 확인하는 코드를 추가한다:

```python
# customers_clean.csv에 있는 컬럼 확인
print("customers 컬럼:", customers.columns.tolist())

# name 컬럼이 없을 때를 대비한 방어 코드
group_cols = ["customer_id"]
if "name" in customers.columns:
    group_cols.append("name")
if "city" in customers.columns:
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

## 2. 보완 권장 항목

---

### [2-1] `figsize` 단위(인치)와 `dpi` 의미 미설명 — [섹션 3.3, 5.4]

**문제**  
`figsize=(10, 5)`에서 단위가 인치라는 것과, `dpi=150`이 해상도(1인치당 픽셀 수)라는 것을 설명하지 않는다. 비전공자는 왜 숫자를 바꾸면 그래프 크기가 달라지는지 이해하기 어렵다.

**보완 지시**  
섹션 3.3 또는 5.4 도입부에 다음 설명을 추가한다:

```
figsize와 dpi 이해하기

figsize=(10, 5): 그래프 크기를 가로 10인치, 세로 5인치로 설정합니다.
dpi=150: 1인치당 150픽셀(해상도). 높을수록 고화질이지만 파일 크기도 커집니다.

최종 이미지 크기 = figsize × dpi
→ (10 × 150, 5 × 150) = (1500 × 750 픽셀)

보고서용 저장 파일은 dpi=150~200이 적절합니다.
Notebook 화면 표시는 dpi 설정에 관계없이 자동으로 조정됩니다.
```

---

### [2-2] `bins=20`이 임의적임을 미설명 — [섹션 5.6]

**문제**  
히스토그램의 `bins=20`이 왜 20인지 설명이 없다. 데이터 개수와 분포에 따라 `bins` 값을 조정해야 하는데, 임의 숫자로 제시되면 학생이 변경하기 어렵다.

**보완 지시**  
섹션 5.6에 다음 설명을 추가한다:

```python
# bins: 구간(막대)의 개수
# 데이터 수가 적으면 bins를 줄이고, 많으면 늘립니다.
plt.hist(products["price"], bins=20)

# 데이터가 몇 개인지 확인하고 bins를 조정할 수 있습니다.
# products["price"].count() # 데이터 수 확인
# 경험 법칙: bins = sqrt(데이터 수) 또는 10~30 범위에서 시각적으로 판단
```

---

### [2-3] `alpha=0.6` 의미 미설명 — [섹션 5.7]

**문제**  
산점도에서 `alpha=0.6`이 투명도(0=완전 투명, 1=불투명)를 의미한다는 설명이 없다. 겹치는 점이 많을 때 투명도를 조정하면 밀도를 파악할 수 있다는 목적도 설명되지 않는다.

**보완 지시**  
섹션 5.7 코드에 주석을 추가한다:

```python
plt.scatter(
    product_sales["price"],
    product_sales["total_quantity"],
    alpha=0.6   # 투명도: 0(완전 투명) ~ 1(불투명)
                # 점이 겹치는 부분에서 밀도를 시각적으로 파악할 수 있습니다
)
```

---

### [2-4] `plt.close()` 호출 없음 — [섹션 5.4~5.9]

**문제**  
각 그래프 저장 후 `plt.close()`를 호출하지 않는다. Jupyter Notebook에서는 `plt.show()`가 figure를 닫아주지만, 스크립트로 실행하거나 여러 그래프를 연속으로 그릴 때 이전 figure가 메모리에 누적될 수 있다.

**보완 지시**  
실습 코드 마지막에 다음 안내를 추가한다:

```python
# 모든 그래프를 그린 후 메모리를 정리합니다.
# Notebook에서는 plt.show()가 자동으로 figure를 닫아주므로 보통 생략해도 됩니다.
# 스크립트로 실행할 때는 plt.close("all")을 추가하는 것이 좋습니다.
plt.close("all")
```

---

### [2-5] 취소 주문 포함 매출 집계 문제 반복 — [섹션 5.3]

**문제**  
ch06 리뷰 [1-6]에서 지적한 문제와 동일하다. 섹션 5.3의 `category_sales`, `monthly_sales`, `customer_sales` 집계에서 `order_status` 필터링이 없어 취소 주문이 매출에 포함된다.

**보완 지시**  
ch06에서 이 주의사항을 추가했다면 ch07에서도 동일한 안내 한 줄을 추가한다:

```python
# ⚠️ 이 집계에는 취소(cancelled) 주문도 포함됩니다.
# 완료 주문만 포함하려면:
# completed_order_ids = orders[orders["order_status"] == "completed"]["order_id"]
# order_items_completed = order_items[order_items["order_id"].isin(completed_order_ids)]
```

---

### [2-6] seaborn 미언급 — [핵심 개념 3.3, 실습 5]

**문제**  
시각화 라이브러리로 `matplotlib`만 소개하고, 실무에서 자주 사용하는 `seaborn`을 언급하지 않는다. 비전공자가 이후에 seaborn을 처음 접하면 "왜 다른 라이브러리를?"이라는 혼란을 겪을 수 있다.

**보완 지시**  
섹션 3.3 또는 실습 5.1 도입에서 간단히 언급한다:

```
이 교재에서는 matplotlib를 사용합니다. pandas의 기본 시각화도 matplotlib를 기반으로 합니다.
실무에서는 matplotlib를 더 편리하게 사용할 수 있도록 설계된 seaborn 라이브러리도 많이 사용합니다.
seaborn은 Chapter 7 심화 과제나 Chapter 15 최종 프로젝트에서 탐색해볼 수 있습니다.
```

---

### [2-7] 연습 문제에 힌트/채점 기준 없음 — [섹션 9]

**문제**  
ch01~ch06과 동일.

**보완 지시**  
심화 과제 평가 기준 예시:

```
평가 기준 (시각화 보고서):
- 분석 질문에 적합한 그래프 종류를 선택했는가? (20%)
- 그래프 제목, 축 이름, 단위가 명확한가? (15%)
- 한글 폰트 설정이 적용되었는가? (10%)
- 그래프 파일이 올바른 경로에 저장되었는가? (15%)
- 각 그래프에 대한 해석 문장을 작성했는가? (20%)
- 관찰 결과와 원인 가설을 구분했는가? (20%)
```

---

### [2-8] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch06과 동일. ch07 신규 용어: `plt.figure()`, `figsize`, `plt.bar()`, `plt.plot()`, `plt.hist()`, `plt.scatter()`, `plt.barh()`, `bins`, `alpha`, `dpi`, `marker`, `tight_layout()`, `savefig()`, `xticks(rotation)`, 가로 막대그래프(`barh`).

**보완 지시**  
섹션 10(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어/함수 | 설명 |
|-----------|------|
| `plt.figure(figsize=)` | 그래프 크기 설정. 단위는 인치 |
| `plt.bar()` | 세로 막대그래프 |
| `plt.barh()` | 가로 막대그래프. 항목 이름이 길 때 유용 |
| `plt.plot()` | 선 그래프 |
| `plt.hist(bins=)` | 히스토그램. bins는 구간 수 |
| `plt.scatter(alpha=)` | 산점도. alpha는 투명도(0~1) |
| `plt.tight_layout()` | 요소가 겹치지 않도록 자동 여백 조정 |
| `plt.savefig(dpi=)` | 그래프를 이미지 파일로 저장. dpi는 해상도 |
| `marker="o"` | 선 그래프에서 데이터 포인트 표시 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-2] Notebook 파일명 불일치 (ch04·ch06 반복) | 필수 수정 |
| 🔴 높음 | [1-3] 그래프 코드 중복 (show/save 버전 혼재) | 필수 수정 |
| 🔴 높음 | [1-4] savefig → show 순서 미설명 | 필수 수정 |
| 🔴 높음 | [1-5] 한글 폰트 하드코딩 (Mac/Linux 깨짐) | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (285분 vs "약 3시간") | 필수 수정 |
| 🟠 중간 | [1-6] `xticks(rotation=45)` `ha="right"` 누락 | 필수 수정 |
| 🟠 중간 | [1-8] `name` 컬럼 존재 미확인 | 필수 수정 |
| 🟡 낮음 | [1-7] `base_dir` 자동 감지 패턴 한계 (ch06 반복) | 필수 수정 |
| 🟢 권장 | [2-1] `figsize` 단위와 `dpi` 의미 미설명 | 보완 권장 |
| 🟢 권장 | [2-2] `bins=20` 임의 설정 미설명 | 보완 권장 |
| 🟢 권장 | [2-3] `alpha=0.6` 의미 미설명 | 보완 권장 |
| 🟢 참고 | [2-4] `plt.close()` 호출 없음 | 보완 권장 |
| 🟢 참고 | [2-5] 취소 주문 포함 매출 집계 (ch06 반복) | 보완 권장 |
| 🟢 참고 | [2-6] seaborn 미언급 | 보완 권장 |
| 🟢 참고 | [2-7] 연습 문제 채점 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-8] 핵심 용어 정리 섹션 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 그래프 선택 기준 표(섹션 3.2)가 분석 목적 × 적합한 그래프 × 예시 질문으로 체계적으로 정리되어 있다.
- 파이 차트의 한계를 명시하고 막대그래프를 권장한 실무 지침이 매우 좋다.
- 고객명을 익명화 라벨로 교체하는 코드(섹션 5.8)가 포함된 점이 개인정보 보호 관점에서 우수하다.
- 각 그래프마다 "해석 예시"를 포함하고 관찰과 원인을 구분하도록 유도한 점이 학습에 매우 효과적이다.
- LLM 프롬프트 섹션 6.4("잘못된 그래프 선택 검토")가 비판적 사고를 기르는 데 좋다.
- 시각화 체크리스트(섹션 8)가 실무 적용 관점에서 완성도가 높다.
- `tabulate` 설치 안내를 5.1에서 명시한 점이 좋다.

**전체적 방향 제안**  
ch07의 가장 큰 구조적 문제는 **코드 중복(show/save 두 버전)**으로, 이로 인해 Notebook 셀 수가 불필요하게 늘어나고 학습 집중도가 떨어진다. 각 그래프를 단일 블록으로 통합하면 코드량이 절반 이하로 줄어들고 저장 순서에 대한 혼란도 해소된다. **한글 폰트 OS 자동 감지**는 Mac을 사용하는 학생이 한 명이라도 있으면 첫 번째 그래프 출력부터 오류를 만나게 되므로 즉시 수정이 필요하다. Notebook 파일명 불일치 문제는 ch04 이후 반복되고 있으므로 전체 장 일괄 확인이 권장된다.
