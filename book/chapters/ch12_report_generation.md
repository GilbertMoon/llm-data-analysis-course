# 12장. LLM이 만든 분석 코드를 검증하는 방법

LLM은 pandas 집계, 시각화, 머신러닝, 보고서 작성 코드를 빠르게 제안할 수 있습니다. 그러나 실행되는 코드가 있다는 사실과 분석이 올바르다는 사실은 다릅니다. 실제 데이터에 없는 컬럼을 사용하거나, 병합으로 행이 늘어나거나, 취소·환불 주문을 포함한 금액을 매출로 해석하거나, 목표값을 입력값에 넣는 데이터 누수가 발생할 수 있습니다.

생성 코드는 파일을 수정하거나 삭제하고, 외부 서버로 데이터를 전송하거나, 운영체제 명령을 실행할 수도 있습니다. 따라서 LLM이 작성한 코드는 **완성된 답이 아니라 검토되지 않은 초안**으로 취급해야 합니다.

이 장에서는 다음 네 단계를 중심으로 생성 코드를 검증합니다.

1. 실행 전에 데이터 구조와 코드 동작을 읽습니다.
2. 위험한 외부 작업은 실행하지 않고 정적 점검과 사람 검토를 거칩니다.
3. 승인된 코드만 격리된 환경에서 작은 데이터로 실행합니다.
4. 실행 후 행 수, 결측치, 키 관계, 집계 범위와 총합을 다시 확인합니다.

전체 실습은 `notebooks/ch12_report_generation.ipynb`에서 실행할 수 있으며, 공통 함수는 `src/llm_code_validation.py`, 일괄 실행 스크립트는 `scripts/run_llm_code_validation.py`에 정리합니다.

## 이 장에서 생각해 볼 질문

- LLM이 사용한 데이터셋과 컬럼명이 실제 구조와 일치하는가?
- 병합 관계와 고유 키 조건이 코드에 반영되어 있는가?
- 분석 대상에 포함한 주문 상태와 제외 기준이 명확한가?
- 원본 범위와 집계 결과의 총합이 일치하는가?
- 목표값이나 예측 이후 정보가 입력값에 섞이지 않았는가?
- 코드가 파일 삭제, 외부 통신, 명령 실행을 수행하지 않는가?
- 새 패키지 설치가 정말 필요하며 출처를 신뢰할 수 있는가?
- LLM에 개인정보, API 키, 내부 경로를 전달하지 않았는가?
- 오류가 없다는 이유만으로 분석 결과를 신뢰하고 있지 않은가?
- 프롬프트, 수정 내용, 실행 환경과 검증 결과를 기록했는가?

## 1. 생성 코드는 두 가지 관점에서 검증한다

LLM 코드는 **분석 논리**와 **실행 안전**을 함께 검증해야 합니다.

| 관점 | 확인할 내용 | 대표 문제 |
| --- | --- | --- |
| 데이터 구조 | 데이터셋, 컬럼, 타입, 키 | 존재하지 않는 컬럼 사용 |
| 분석 논리 | 집계 범위, 필터, 목표값, 지표 | 취소 주문 포함, 데이터 누수 |
| 재현성 | 경로, 의존성, 버전, 난수 | 다른 환경에서 결과 불일치 |
| 실행 안전 | 파일 변경, 외부 통신, 명령 실행 | 데이터 유출, 파일 삭제 |
| 해석 | 관찰과 원인 가설 구분 | 데이터에 없는 원인 단정 |

코드가 문법적으로 맞고 오류 없이 실행되어도 분석 논리가 틀릴 수 있습니다. 반대로 분석 의도가 타당해 보여도 코드가 외부 통신이나 파일 삭제를 포함한다면 실행해서는 안 됩니다.

## 2. 좋은 요청은 데이터 구조와 검증 조건에서 시작한다

“카테고리별 매출 코드를 작성해 주세요”라고만 요청하면 LLM은 컬럼명과 병합 구조를 추측할 수 있습니다. 다음 정보를 함께 제공하는 편이 안전합니다.

| 정보 | 예시 |
| --- | --- |
| 데이터셋 | `products`, `orders`, `order_items` |
| 필요한 컬럼 | `product_id`, `order_id`, `order_status`, `quantity`, `unit_price` |
| 키 관계 | `order_items.product_id` → `products.product_id` |
| 집계 범위 | `order_status == "completed"` |
| 원하는 결과 | 카테고리별 완료 주문 수량과 금액 |
| 검증 조건 | 병합 전후 행 수, 미연결 행, 총합 차이 |
| 금지 조건 | 없는 컬럼 추측, 외부 통신, 파일 삭제, 명령 실행 |

원본 고객명, 이메일, 전화번호, 전체 주문 행을 프롬프트에 넣을 필요는 없습니다. 컬럼 구조와 비식별 요약만 제공하고, 조직의 승인 없이 내부 데이터를 외부 LLM에 입력하지 않습니다.

다음은 요청 예시입니다.

```text
온라인 쇼핑몰 데이터로 카테고리별 완료 주문 금액을 계산하는
pandas 코드를 작성해 주세요.

데이터 구조:
- products: product_id, product_name, category, price
- orders: order_id, order_date, order_status
- order_items: order_id, product_id, quantity, unit_price, line_total

집계 기준:
- order_status가 completed인 주문만 포함
- line_total은 quantity * unit_price와 일치해야 함
- 이 금액을 회계상 순매출이라고 단정하지 않음

검증 조건:
- products.product_id와 orders.order_id의 고유성 확인
- merge에 validate 옵션 사용
- 병합 전후 행 수와 미연결 행 수 출력
- 완료 주문 상세 금액과 카테고리 집계 합계의 차이 출력

금지 조건:
- 위에 없는 컬럼명 추측 금지
- 파일 삭제, 외부 통신, 운영체제 명령 실행 금지
- 패키지 자동 설치 금지
```

## 3. 실행 전 데이터 구조를 확인한다

먼저 전처리 파일을 불러옵니다.

```python
from pathlib import Path

import pandas as pd

project_root = Path.cwd()
if project_root.name == "notebooks":
    project_root = project_root.parent

processed_dir = project_root / "data" / "processed"
report_dir = project_root / "reports"
report_dir.mkdir(parents=True, exist_ok=True)
```

필수 파일이 없으면 원본 데이터로 자동 대체하지 않습니다. 5장의 전처리 기준과 다른 데이터가 사용될 수 있기 때문입니다.

```python
required_files = {
    "customers": processed_dir / "customers_clean.csv",
    "products": processed_dir / "products_clean.csv",
    "orders": processed_dir / "orders_clean.csv",
    "order_items": processed_dir / "order_items_clean.csv",
}

missing_files = [
    path
    for path in required_files.values()
    if not path.exists()
]

if missing_files:
    missing_text = "\n".join(
        f"- {path}" for path in missing_files
    )
    raise FileNotFoundError(
        "전처리 파일이 없습니다. 먼저 "
        "`python scripts/preprocess_data.py`를 실행하세요.\n"
        + missing_text
    )

datasets = {
    name: pd.read_csv(path)
    for name, path in required_files.items()
}
```

실제 컬럼과 데이터 크기를 확인합니다.

```python
inventory = pd.DataFrame(
    [
        {
            "dataset": name,
            "rows": len(df),
            "columns": len(df.columns),
            "column_list": ", ".join(df.columns),
            "missing_values": int(
                df.isna().sum().sum()
            ),
            "duplicated_rows": int(
                df.duplicated().sum()
            ),
        }
        for name, df in datasets.items()
    ]
)

inventory
```

LLM이 제안한 컬럼이 없을 때 다음처럼 조용히 제외하면 안 됩니다.

```python
# 잘못된 방식: 누락 컬럼이 있어도 코드가 계속 실행됨
features = [
    column
    for column in requested_features
    if column in model_data.columns
]
```

필수 컬럼이 없으면 즉시 중단하고 문제 정의나 전처리 과정을 수정해야 합니다.

```python
missing_features = (
    set(requested_features)
    - set(model_data.columns)
)

if missing_features:
    raise KeyError(
        "필요한 입력 컬럼이 없습니다: "
        f"{sorted(missing_features)}"
    )
```

## 4. 고유 키와 파일 간 관계를 확인한다

CSV 파일은 데이터베이스처럼 기본 키와 외래 키 제약조건을 자동으로 검사하지 않습니다. 병합 전에 부모 데이터의 키가 고유한지 확인해야 합니다.

```python
primary_keys = {
    "customers": "customer_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "order_item_id",
}

for dataset_name, key in primary_keys.items():
    df = datasets[dataset_name]

    if key not in df.columns:
        raise KeyError(
            f"{dataset_name}.{key}가 없습니다."
        )

    print(
        dataset_name,
        "키 결측:",
        int(df[key].isna().sum()),
        "키 중복:",
        int(
            df.loc[df[key].notna(), key]
            .duplicated()
            .sum()
        ),
    )
```

다음 관계도 확인합니다.

```text
order_items.product_id → products.product_id
order_items.order_id   → orders.order_id
orders.customer_id     → customers.customer_id
```

부모 키가 중복된 상태에서 병합하면 주문 상세 행이 여러 배로 늘어날 수 있습니다. `validate` 옵션을 사용하면 예상한 관계와 다를 때 즉시 오류가 발생합니다.

```python
sales_items = order_items.merge(
    products[
        ["product_id", "category"]
    ],
    on="product_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)
```

`many_to_one`은 여러 주문 상세 행이 하나의 상품 행에 연결되는 구조를 검사합니다. `indicator=True`는 연결되지 않은 행을 찾는 데 사용합니다.

```python
unlinked_count = int(
    sales_items["_merge"].ne("both").sum()
)

if unlinked_count:
    raise ValueError(
        "products에 연결되지 않는 주문 상세 행이 "
        f"{unlinked_count}개 있습니다."
    )
```

## 5. 집계 범위와 금액의 의미를 명확히 한다

`line_total`은 수량과 단가를 곱한 주문 상세 금액입니다. 전체 합계를 곧바로 매출이나 순매출이라고 부르면 안 됩니다. 취소·환불, 할인, 배송비, 세금, 부분 환불 정보가 반영되지 않을 수 있습니다.

먼저 숫자 변환과 계산 일치 여부를 확인합니다.

```python
order_items = order_items.copy()

order_items["quantity"] = pd.to_numeric(
    order_items["quantity"],
    errors="coerce",
)
order_items["unit_price"] = pd.to_numeric(
    order_items["unit_price"],
    errors="coerce",
)

if "line_total" not in order_items.columns:
    order_items["line_total"] = (
        order_items["quantity"]
        * order_items["unit_price"]
    )
else:
    order_items["line_total"] = pd.to_numeric(
        order_items["line_total"],
        errors="coerce",
    )
```

변환 실패와 계산 불일치를 확인합니다.

```python
invalid_numeric = order_items[
    ["quantity", "unit_price", "line_total"]
].isna().any(axis=1)

if invalid_numeric.any():
    raise ValueError(
        "금액 계산 컬럼의 숫자 변환에 실패한 행이 "
        f"{int(invalid_numeric.sum())}개 있습니다."
    )

expected_total = (
    order_items["quantity"]
    * order_items["unit_price"]
)

mismatch = ~order_items[
    "line_total"
].round(6).eq(expected_total.round(6))

if mismatch.any():
    raise ValueError(
        "line_total 계산이 일치하지 않는 행이 "
        f"{int(mismatch.sum())}개 있습니다."
    )
```

주문 상태를 연결하고 완료 주문만 선택합니다.

```python
order_sales = order_items.merge(
    orders[
        [
            "order_id",
            "order_date",
            "order_status",
        ]
    ],
    on="order_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)

if order_sales["_merge"].ne("both").any():
    raise ValueError(
        "orders에 연결되지 않는 주문 상세가 있습니다."
    )

order_sales = order_sales.drop(
    columns="_merge"
)

completed_items = order_sales.loc[
    order_sales["order_status"]
    .astype("string")
    .str.strip()
    .str.lower()
    .eq("completed")
].copy()
```

카테고리 집계를 만듭니다.

```python
completed_items = completed_items.merge(
    products[
        ["product_id", "category"]
    ],
    on="product_id",
    how="left",
    validate="many_to_one",
)

if completed_items["category"].isna().any():
    raise ValueError(
        "category에 연결되지 않는 완료 주문 상세가 있습니다."
    )

category_sales = (
    completed_items
    .groupby(
        "category",
        as_index=False,
        dropna=False,
    )
    .agg(
        total_quantity=("quantity", "sum"),
        total_sales=("line_total", "sum"),
    )
    .sort_values(
        "total_sales",
        ascending=False,
    )
)
```

총합을 대조합니다.

```python
source_total = completed_items[
    "line_total"
].sum()

grouped_total = category_sales[
    "total_sales"
].sum()

total_difference = source_total - grouped_total

print("완료 주문 상세 금액:", source_total)
print("카테고리 집계 금액:", grouped_total)
print("차이:", total_difference)
```

차이가 0이 아니면 결측 범주, 필터 조건, 병합 누락, 숫자 변환 문제를 다시 확인합니다.

## 6. 실행 전에 위험한 코드 동작을 찾는다

생성 코드에 다음 동작이 포함되면 실행 전에 목적과 범위를 반드시 확인합니다.

- `eval()`, `exec()`와 같은 동적 코드 실행
- `os.system()`과 `subprocess`를 통한 명령 실행
- `requests`, `urllib`, `socket`을 통한 외부 통신
- 쓰기 모드의 `open()`과 파일 덮어쓰기
- `unlink()`, `rmtree()`와 같은 삭제 작업
- 코드에 직접 작성된 API 키, 토큰, 비밀번호
- LLM이 제안한 임의의 `pip install` 명령

`src/llm_code_validation.py`의 `scan_generated_code()`는 Python의 추상 구문 트리(AST)를 사용해 일부 위험 후보를 찾습니다.

```python
from src.llm_code_validation import (
    scan_generated_code,
)

generated_code = """
import requests

response = requests.get(
    "https://example.com/data.csv"
)
open(
    "download.csv",
    "wb",
).write(response.content)
"""

static_scan = scan_generated_code(
    generated_code
)

static_scan
```

이 점검은 위험한 패턴을 빠르게 찾는 보조 도구입니다. 결과가 비어 있어도 코드가 안전하다는 뜻은 아닙니다. 문자열을 조합해 명령을 실행하거나, 설치된 라이브러리 내부에서 외부 통신을 수행하는 코드는 단순 정적 점검으로 모두 찾을 수 없습니다.

승인되지 않은 외부 통신, 파일 변경, 명령 실행은 실행하지 않습니다. 검토가 끝난 코드도 다음 조건에서 먼저 시험합니다.

- 실제 운영 데이터가 없는 별도 가상환경
- 최소 권한의 사용자 계정
- API 키와 클라우드 자격증명이 없는 환경
- 복사한 소량 샘플 데이터
- Git으로 변경 전 상태를 기록한 작업 폴더
- 네트워크 접근이 필요하지 않다면 차단된 환경

## 7. 새 패키지 설치 요청도 검증한다

LLM은 오류를 해결하기 위해 패키지 설치를 제안할 수 있습니다. 다음과 같은 명령을 이유 없이 실행하지 않습니다.

```text
pip install some-unknown-package
```

설치 전에는 다음을 확인합니다.

- 공식 문서와 공식 패키지 저장소에 존재하는가?
- 패키지 이름이 유명 패키지와 비슷한 오타 유도 이름은 아닌가?
- 현재 프로젝트의 `requirements.txt`에 이미 대체 패키지가 있는가?
- 필요한 버전과 Python 호환 범위는 무엇인가?
- 설치 과정에서 추가 스크립트가 실행되는가?
- 조직의 승인된 패키지 정책을 충족하는가?

의존성을 추가했다면 `requirements.txt` 또는 별도의 환경 파일에 버전을 기록하고, 깨끗한 환경에서 다시 설치해 재현성을 확인합니다.

## 8. 머신러닝 코드는 예측 시점부터 검증한다

머신러닝 코드에서는 목표값 자체뿐 아니라 목표값의 계산 재료와 예측 이후 정보도 누수가 될 수 있습니다.

| 문제 | 위험한 입력값 예시 | 검증 방향 |
| --- | --- | --- |
| 주문 취소 분류 | `order_status`, 취소 확정 이후 정보 | 예측 시점 이전 정보만 사용 |
| 주문 금액 회귀 | `line_total`, 수량·단가 및 같은 주문 집계값 | 주문 상세 확인 전 정보만 사용 |
| 미래 구매 금액 | 예측 기간의 실제 구매 금액 | 기준일 이전 행동 지표만 사용 |
| 미래 판매량 | 예측 기간의 판매량 | 예측 시작일 이전 이력만 사용 |

입력값 목록에서 위험한 컬럼을 조용히 제거하는 대신 오류를 발생시킵니다.

```python
forbidden_features = {
    "order_total",
    "line_total",
    "quantity",
    "unit_price",
    "order_status",
    "is_cancelled",
    "order_id",
    "customer_id",
}

leaked_features = (
    set(feature_columns)
    & forbidden_features
)

if leaked_features:
    raise ValueError(
        "누수 위험 입력값이 있습니다: "
        f"{sorted(leaked_features)}"
    )
```

평가에서는 문제 유형에 맞는 분할과 지표를 사용합니다.

- 시간 흐름이 있는 문제는 날짜 순서 분할을 우선 검토합니다.
- 전처리 규칙은 Pipeline 안에서 훈련 데이터에만 맞춥니다.
- 회귀는 베이스라인, MAE, RMSE, R²를 함께 봅니다.
- 분류는 클래스 비율, 정밀도, 재현율, F1 점수, 혼동행렬을 함께 봅니다.
- 테스트 결과를 반복적으로 보며 모델을 조정하지 않습니다.
- 낮은 성능이나 음수 R²도 숨기지 않습니다.

## 9. 오류 메시지는 최소한의 맥락과 함께 전달한다

오류 메시지만 LLM에 붙여 넣으면 데이터 구조를 다시 추측할 수 있습니다. 다음 내용을 함께 제공합니다.

~~~text
분석 목적:
- [계산하거나 예측하려는 내용을 작성]

실제 데이터 구조:
- [필요한 데이터셋과 컬럼만 작성]
- 원본 행, 개인정보, API 키, 내부 경로는 제공하지 않음

실행한 최소 코드:
```python
[오류를 재현하는 최소 코드]
```

오류 또는 검증 결과:
```text
[오류 메시지, 행 수, 결측치, 총합 차이]
```

요청:
1. 오류 원인과 분석 논리 문제를 구분해 설명해 주세요.
2. 실제 컬럼명만 사용한 최소 수정안을 제안해 주세요.
3. 병합 validate, 행 수, 미연결 행, 총합 대조를 포함해 주세요.
4. 파일 삭제, 외부 통신, 명령 실행, 패키지 설치 코드는 추가하지 마세요.
5. 데이터에 없는 원인을 추측하지 마세요.
~~~

오류 메시지에도 사용자명, 내부 경로, 서버 주소, 토큰이 포함될 수 있습니다. 외부 LLM에 전달하기 전에 민감정보를 제거합니다.

## 10. 검증 결과를 증거로 남긴다

검증 과정은 코드 리뷰 체크리스트와 요약 보고서로 남깁니다.

```python
from src.llm_code_validation import (
    build_code_review_checklist,
)

code_review_checklist = (
    build_code_review_checklist()
)

code_review_checklist.to_csv(
    report_dir
    / "ch12_llm_code_review_checklist.csv",
    index=False,
    encoding="utf-8-sig",
)
```

기록할 내용은 다음과 같습니다.

- 사용한 프롬프트와 제공한 데이터 구조
- LLM이 제안한 원본 코드
- 사람이 수정한 내용과 수정 이유
- 실행 환경과 주요 패키지 버전
- 필수 컬럼·고유 키·관계 검증 결과
- 병합 전후 행 수와 미연결 행 수
- 집계 대상 주문 상태와 제외 기준
- 원본 범위와 집계 결과의 총합 차이
- 머신러닝의 예측 시점, 입력값, 분할과 지표
- 외부 통신·파일 변경·명령 실행 검토 결과
- 최종 승인자와 검토 일자

## 11. 공통 모듈과 실행 스크립트 사용하기

전체 검증 파이프라인은 다음처럼 실행합니다.

```python
from src.llm_code_validation import (
    run_llm_code_validation,
)

result = run_llm_code_validation(
    processed_dir=processed_dir,
    report_dir=report_dir,
)

result["outputs"][
    "category_validation"
]
```

터미널에서는 프로젝트 루트와 관계없이 다음 스크립트를 실행할 수 있습니다.

```text
python scripts/run_llm_code_validation.py
```

생성되는 주요 파일은 다음과 같습니다.

```text
reports/ch12_dataset_inventory.csv
reports/ch12_required_column_check.csv
reports/ch12_primary_key_check.csv
reports/ch12_relationship_key_check.csv
reports/ch12_category_sales_validated.csv
reports/ch12_category_sales_validation.csv
reports/ch12_monthly_sales_validated.csv
reports/ch12_monthly_sales_validation.csv
reports/ch12_ml_leakage_review.csv
reports/ch12_generated_code_static_scan.csv
reports/ch12_llm_code_review_checklist.csv
reports/ch12_error_fix_prompt_template.md
reports/ch12_code_validation_summary.md
```

## 12. 최종 검토 체크리스트

| 검토 항목 | 확인 |
| --- | --- |
| 실제 데이터셋과 컬럼명만 사용했는가? | □ |
| 필수 컬럼이 없을 때 실행을 중단하는가? | □ |
| 고유 키의 결측치와 중복을 확인했는가? | □ |
| 병합 관계와 `validate` 조건이 맞는가? | □ |
| 병합 전후 행 수와 미연결 행을 확인했는가? | □ |
| 포함한 주문 상태와 제외 기준을 기록했는가? | □ |
| 원본 범위와 집계 결과의 총합을 대조했는가? | □ |
| 날짜와 숫자 변환 실패를 확인했는가? | □ |
| 예측 시점과 목표값을 명확히 정의했는가? | □ |
| 목표값 계산 재료와 사후 정보를 제외했는가? | □ |
| 문제에 맞는 분할과 평가 지표를 사용했는가? | □ |
| 외부 통신·파일 변경·명령 실행을 검토했는가? | □ |
| 패키지 설치의 필요성과 출처를 확인했는가? | □ |
| 개인정보·API 키·내부 정보를 제거했는가? | □ |
| 관찰 결과와 원인 가설을 구분했는가? | □ |
| 프롬프트·수정 내용·검증 결과를 기록했는가? | □ |

## 13. 다음 장으로 이어지는 흐름

이번 장에서는 LLM이 만든 분석 코드를 실행 전에 읽고, 승인된 코드만 제한된 환경에서 실행한 뒤, 데이터 구조와 결과를 다시 검증하는 과정을 살펴보았습니다.

핵심은 다음과 같습니다.

- 생성 코드는 검토되지 않은 초안입니다.
- 오류 없이 실행되는 것만으로는 충분하지 않습니다.
- 집계 기준과 총합, 키 관계와 데이터 누수를 확인해야 합니다.
- 코드의 분석 논리뿐 아니라 외부 통신과 파일 변경 같은 실행 안전도 검토해야 합니다.
- 낮은 성능이나 검증 실패도 숨기지 않고 기록해야 합니다.
- 최종 분석 결과와 코드 사용 책임은 사람에게 있습니다.

다음 장에서는 공공데이터, API, 크롤링을 통해 외부 데이터를 수집하고 기존 분석 데이터와 연결하는 방법을 다룹니다. 외부 데이터를 사용할 때도 출처, 이용약관, 개인정보, 요청량 제한과 데이터 품질을 먼저 확인해야 합니다.
