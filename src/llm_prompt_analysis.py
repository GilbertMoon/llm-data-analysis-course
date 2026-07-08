"""Chapter 11 LLM 프롬프트 기반 분석 보조 함수 모음.

원본 데이터를 LLM에 직접 넣지 않고, 데이터 구조 요약과 검증 가능한 프롬프트 템플릿을 만드는 함수들을 제공합니다.
분석 질문 생성, 전처리, 시각화, 회귀/분류, 결과 해석 프롬프트와 검토 체크리스트, 프롬프트 사용 로그를 생성합니다.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


DATASET_DESCRIPTIONS = {
    "customers": "고객 정보",
    "products": "상품 정보",
    "orders": "주문 정보",
    "order_items": "주문 상세 정보",
}


def load_available_sales_data(
    processed_dir: str | Path = "data/processed",
    raw_dir: str | Path = "data/raw",
) -> dict[str, pd.DataFrame]:
    """전처리 데이터가 있으면 우선 사용하고, 없으면 원본 데이터를 불러옵니다."""
    processed_path = Path(processed_dir)
    raw_path = Path(raw_dir)

    processed_files = {
        "customers": processed_path / "customers_clean.csv",
        "products": processed_path / "products_clean.csv",
        "orders": processed_path / "orders_clean.csv",
        "order_items": processed_path / "order_items_clean.csv",
    }
    raw_files = {
        "customers": raw_path / "customers.csv",
        "products": raw_path / "products.csv",
        "orders": raw_path / "orders.csv",
        "order_items": raw_path / "order_items.csv",
    }

    if all(path.exists() for path in processed_files.values()):
        files = processed_files
    elif all(path.exists() for path in raw_files.values()):
        files = raw_files
    else:
        missing = [str(path) for path in processed_files.values() if not path.exists()]
        raise FileNotFoundError(
            "사용 가능한 판매 데이터 파일을 찾을 수 없습니다. "
            "먼저 python scripts/preprocess_data.py 또는 python scripts/generate_sample_data.py 를 실행하세요.\n"
            + "\n".join(missing)
        )

    return {name: pd.read_csv(path) for name, path in files.items()}


def build_dataset_summary(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """LLM 입력용 데이터셋 구조 요약표를 생성합니다."""
    rows = []
    for name, df in datasets.items():
        rows.append(
            {
                "dataset": name,
                "description": DATASET_DESCRIPTIONS.get(name, ""),
                "rows": df.shape[0],
                "columns": df.shape[1],
                "column_list": ", ".join(df.columns),
                "missing_values": int(df.isna().sum().sum()),
                "duplicated_rows": int(df.duplicated().sum()),
            }
        )
    return pd.DataFrame(rows)


def build_column_summary(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """LLM 입력용 컬럼별 타입, 결측치, 고유값 수 요약표를 생성합니다."""
    rows = []
    for name, df in datasets.items():
        for col in df.columns:
            rows.append(
                {
                    "dataset": name,
                    "column": col,
                    "dtype": str(df[col].dtype),
                    "missing_count": int(df[col].isna().sum()),
                    "unique_count": int(df[col].nunique(dropna=True)),
                    "example_values": ", ".join(
                        map(str, df[col].dropna().astype(str).unique()[:3])
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_safe_context_text(
    dataset_summary: pd.DataFrame,
    column_summary: pd.DataFrame,
) -> str:
    """LLM에 붙여 넣을 수 있는 안전한 데이터 구조 설명 텍스트를 생성합니다."""
    dataset_lines = []
    for _, row in dataset_summary.iterrows():
        dataset_lines.append(
            f"- {row['dataset']} ({row['description']}): "
            f"{row['rows']}행, {row['columns']}열, 컬럼: {row['column_list']}"
        )

    column_lines = []
    for dataset_name, group in column_summary.groupby("dataset"):
        column_parts = [
            f"{row['column']}({row['dtype']}, 결측 {row['missing_count']})"
            for _, row in group.iterrows()
        ]
        column_lines.append(f"- {dataset_name}: " + ", ".join(column_parts))

    return "\n".join(
        [
            "# LLM 입력용 데이터 구조 요약",
            "",
            "## 데이터셋 개요",
            *dataset_lines,
            "",
            "## 컬럼 요약",
            *column_lines,
            "",
            "## 주의",
            "- 원본 고객명, 이메일, 전화번호, 주소, 개별 거래 상세는 입력하지 않습니다.",
            "- 아래 정보는 데이터의 구조와 분석 목적을 설명하기 위한 요약 정보입니다.",
        ]
    )


def build_prompt_templates() -> pd.DataFrame:
    """분석 단계별 LLM 프롬프트 템플릿을 반환합니다."""
    templates = [
        {
            "step": "분석 질문 생성",
            "purpose": "현재 데이터로 가능한 분석 질문을 만들기",
            "prompt": """온라인 쇼핑몰 데이터로 EDA를 수행하려고 합니다.

데이터셋 구조:
- customers: customer_id, gender, age, city, signup_date
- products: product_id, product_name, category, price
- orders: order_id, customer_id, order_date, payment_method, order_status
- order_items: order_id, product_id, quantity, unit_price, line_total

요청:
1. 현재 데이터로 분석 가능한 질문 10개를 제안해 주세요.
2. 각 질문에 필요한 데이터셋과 컬럼을 함께 적어 주세요.
3. 집계, 시각화, 회귀, 분류 중 어떤 방식으로 접근할 수 있는지 표시해 주세요.
4. 현재 데이터로 답할 수 없는 질문은 제외하거나 추가 데이터가 필요하다고 표시해 주세요.

주의:
- 실제 데이터에 없는 컬럼을 만들지 마세요.
- 고객 선호도, 광고 효과, 프로모션 효과처럼 현재 데이터에 없는 원인을 단정하지 마세요.""",
            "validation_point": "현재 데이터로 답할 수 있는 질문인지 확인",
        },
        {
            "step": "전처리 계획",
            "purpose": "결측치, 중복, 타입 문제를 확인하는 계획 만들기",
            "prompt": """다음 온라인 쇼핑몰 데이터의 전처리 계획을 세우려고 합니다.

데이터 구조:
- customers: customer_id, gender, age, city, signup_date
- products: product_id, product_name, category, price
- orders: order_id, customer_id, order_date, payment_method, order_status
- order_items: order_id, product_id, quantity, unit_price, line_total

요청:
1. 각 데이터셋에서 확인해야 할 결측치, 중복, 데이터 타입 문제를 정리해 주세요.
2. order_date와 signup_date를 날짜형으로 변환할 때 확인할 사항을 알려 주세요.
3. 문자열 범주값의 표기 차이를 확인하는 코드를 제안해 주세요.
4. 전처리 후 저장할 파일명을 제안해 주세요.

주의:
- 결측치나 이상값을 무조건 삭제하지 마세요.
- 삭제, 대체, 유지 중 어떤 선택지가 있는지 비교해 주세요.
- 실제 데이터에 없는 컬럼명을 만들지 마세요.""",
            "validation_point": "무조건 삭제나 대체를 제안하지 않았는지 확인",
        },
        {
            "step": "시각화",
            "purpose": "분석 질문에 맞는 그래프 선택과 코드 초안 만들기",
            "prompt": """온라인 쇼핑몰 데이터 분석 결과를 시각화하려고 합니다.

분석 질문:
1. 카테고리별 매출은 어떻게 다른가?
2. 월별 매출은 어떻게 변하는가?
3. 상품 가격은 어떤 구간에 몰려 있는가?
4. 상품 가격과 판매 수량은 관계가 있는가?
5. 구매 금액 상위 고객은 누구인가?

요청:
1. 각 질문에 적합한 그래프 종류를 추천해 주세요.
2. 그래프를 선택한 이유를 설명해 주세요.
3. matplotlib 코드 작성 시 필요한 x축, y축 컬럼을 정리해 주세요.
4. 그래프 해석 시 주의할 점을 알려 주세요.

주의:
- 월별 매출을 파이 차트로 추천하지 마세요.
- 상품 가격 분포는 선 그래프가 아니라 히스토그램으로 검토해 주세요.
- 고객명이 포함되는 그래프는 익명화 필요성을 언급해 주세요.""",
            "validation_point": "그래프 종류가 분석 질문과 맞는지 확인",
        },
        {
            "step": "회귀 모델링",
            "purpose": "주문별 총금액 예측 코드 초안 만들기",
            "prompt": """온라인 쇼핑몰 주문 데이터를 사용해 주문별 총금액을 예측하는 회귀 모델을 만들려고 합니다.

데이터 구조:
- order_items: order_id, product_id, quantity, unit_price, line_total
- orders: order_id, customer_id, order_date, payment_method, order_status
- customers: customer_id, gender, age, city

예측 대상:
- order_total: 주문별 line_total 합계

요청:
1. 주문별 모델링 데이터셋을 만드는 pandas 코드를 작성해 주세요.
2. train/test split을 적용해 주세요.
3. LinearRegression과 RandomForestRegressor를 비교해 주세요.
4. MAE, RMSE, R2를 계산해 주세요.
5. 데이터 누수가 발생할 수 있는 부분을 설명해 주세요.

주의:
- order_total을 입력값으로 사용하지 마세요.
- 실제 데이터에 없는 컬럼명을 만들지 마세요.
- 범주형 컬럼은 OneHotEncoder를 사용해 주세요.
- 테스트 데이터 기준으로 평가해 주세요.""",
            "validation_point": "예측 대상이 입력값에 섞이지 않았는지 확인",
        },
        {
            "step": "분류 모델링",
            "purpose": "주문 취소 여부 예측 코드 초안 만들기",
            "prompt": """온라인 쇼핑몰 주문 데이터를 사용해 주문 취소 여부를 예측하는 분류 모델을 만들려고 합니다.

데이터 구조:
- orders: order_id, customer_id, order_date, payment_method, order_status
- order_items: order_id, product_id, quantity, unit_price, line_total
- customers: customer_id, gender, age, city

예측 대상:
- is_cancelled: order_status가 cancelled이면 1, 아니면 0

요청:
1. 주문별 분류 데이터셋을 만드는 pandas 코드를 작성해 주세요.
2. train/test split을 적용해 주세요.
3. LogisticRegression과 RandomForestClassifier를 비교해 주세요.
4. accuracy, precision, recall, confusion matrix를 계산해 주세요.
5. 클래스 불균형이 있는지 확인하는 코드를 포함해 주세요.

주의:
- order_status 원본 컬럼을 입력값으로 사용하지 마세요.
- is_cancelled를 만든 뒤에는 정답 정보가 입력값에 섞이지 않도록 해 주세요.
- 실제 데이터에 없는 컬럼명을 만들지 마세요.""",
            "validation_point": "order_status가 입력값에 포함되지 않았는지 확인",
        },
        {
            "step": "결과 해석",
            "purpose": "분석 결과를 관찰, 가설, 추가 질문으로 정리하기",
            "prompt": """다음은 카테고리별 매출 분석 결과입니다.

category,total_quantity,total_sales,sales_ratio
전자기기,320,12500000,42.5
생활용품,510,7800000,26.5
패션,260,6200000,21.1
식품,430,2900000,9.9

요청:
1. 데이터로 확인 가능한 관찰 내용을 작성해 주세요.
2. 가능한 원인 가설을 조심스럽게 작성해 주세요.
3. 추가로 확인해야 할 분석 질문을 제안해 주세요.
4. 보고서에 넣을 수 있는 문장으로 정리해 주세요.

조건:
- 고객 선호, 프로모션 효과 같은 원인을 단정하지 마세요.
- 데이터에 없는 내용을 추측하지 마세요.
- 관찰과 가설을 구분해 주세요.""",
            "validation_point": "원인 단정과 과장 표현 확인",
        },
    ]
    return pd.DataFrame(templates)


def build_llm_review_checklist() -> pd.DataFrame:
    """LLM 답변 검증 체크리스트를 반환합니다."""
    return pd.DataFrame(
        {
            "check_item": [
                "원본 개인정보나 거래 상세를 입력하지 않았는가?",
                "데이터 구조 요약만 입력했는가?",
                "분석 목적을 명확히 작성했는가?",
                "원하는 출력 형식을 지정했는가?",
                "실제 데이터에 없는 컬럼명을 만들지 말라고 요청했는가?",
                "LLM이 만든 코드가 실제로 실행되는가?",
                "컬럼명과 데이터 타입이 실제 데이터와 일치하는가?",
                "병합 기준이 올바른가?",
                "날짜 변환과 결측치 확인 코드가 포함되었는가?",
                "머신러닝 코드에서 데이터 누수가 없는가?",
                "평가 지표가 문제 유형에 맞는가?",
                "해석 문장에서 원인을 단정하지 않았는가?",
                "데이터에 없는 내용을 추측하지 않았는가?",
                "LLM 답변을 수정한 내용을 기록했는가?",
            ],
            "result": ["□"] * 14,
            "memo": [""] * 14,
        }
    )


def build_llm_usage_log_template() -> pd.DataFrame:
    """프롬프트 사용 로그 템플릿을 반환합니다."""
    return pd.DataFrame(
        {
            "step": [
                "데이터 구조 설명",
                "분석 질문 생성",
                "전처리 계획",
                "시각화 코드 초안",
                "회귀 모델링 코드 초안",
                "분류 모델링 코드 초안",
                "결과 해석 문장 작성",
            ],
            "purpose": [
                "데이터셋 구조를 설명하고 분석 전 확인 사항 정리",
                "현재 데이터로 가능한 분석 질문 생성",
                "결측치, 중복, 날짜 처리 계획 수립",
                "분석 질문에 맞는 그래프와 matplotlib 코드 초안 생성",
                "주문별 총금액 예측 모델 코드 초안 생성",
                "주문 취소 여부 예측 모델 코드 초안 생성",
                "집계 결과를 보고서 문장으로 정리",
            ],
            "input_summary": ["데이터 구조 요약"] * 7,
            "llm_answer_summary": [""] * 7,
            "validation_point": [
                "실제 컬럼명과 데이터 타입 확인",
                "현재 데이터로 답할 수 있는 질문인지 확인",
                "무조건 삭제나 대체를 제안하지 않았는지 확인",
                "그래프 종류가 분석 질문과 맞는지 확인",
                "데이터 누수와 평가 지표 확인",
                "정답 컬럼이 입력값에 섞이지 않았는지 확인",
                "원인 단정과 과장 표현 확인",
            ],
            "revision_note": [""] * 7,
            "final_use": ["부분 사용"] * 7,
        }
    )


def build_prompt_log_markdown(
    usage_log: pd.DataFrame,
    checklist: pd.DataFrame,
) -> str:
    """프롬프트 로그 Markdown 문자열을 생성합니다."""
    return f"""# Chapter 11 LLM 프롬프트 로그

## 1. 사용 목적

LLM을 활용해 데이터 구조 설명, 분석 질문 생성, 전처리 계획, 시각화 코드, 머신러닝 코드, 결과 해석 문장의 초안을 만들고 검증했습니다.

## 2. 사용 원칙

- 원본 개인정보와 거래 상세 데이터는 입력하지 않았습니다.
- 컬럼명, 데이터 구조, 집계 결과 중심으로 질문했습니다.
- LLM 답변은 실제 코드 실행과 결과 비교를 통해 검증했습니다.
- 데이터에 없는 원인을 단정하는 문장은 수정했습니다.

## 3. 사용 로그 템플릿

```text
{usage_log.to_string(index=False)}
```

## 4. 검증 체크리스트

```text
{checklist.to_string(index=False)}
```

## 5. 검증 기준

- 실제 컬럼명과 일치하는가?
- 병합 기준이 올바른가?
- 날짜 변환과 결측치 확인이 포함되었는가?
- 머신러닝 코드에서 데이터 누수가 없는가?
- 해석 문장이 데이터에 근거하는가?
"""


def save_llm_prompt_outputs(
    dataset_summary: pd.DataFrame,
    column_summary: pd.DataFrame,
    safe_context_text: str,
    prompt_templates: pd.DataFrame,
    checklist: pd.DataFrame,
    usage_log: pd.DataFrame,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """11장 LLM 프롬프트 분석 결과물을 저장합니다."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "dataset_summary": output_dir / "ch11_dataset_summary_for_llm.csv",
        "column_summary": output_dir / "ch11_column_summary_for_llm.csv",
        "safe_context": output_dir / "ch11_safe_llm_context.md",
        "prompt_templates": output_dir / "ch11_prompt_templates.csv",
        "checklist": output_dir / "ch11_llm_review_checklist.csv",
        "usage_log": output_dir / "ch11_llm_usage_log.csv",
        "prompt_log": output_dir / "ch11_llm_prompt_log.md",
    }

    dataset_summary.to_csv(paths["dataset_summary"], index=False, encoding="utf-8-sig")
    column_summary.to_csv(paths["column_summary"], index=False, encoding="utf-8-sig")
    paths["safe_context"].write_text(safe_context_text, encoding="utf-8")
    prompt_templates.to_csv(paths["prompt_templates"], index=False, encoding="utf-8-sig")
    checklist.to_csv(paths["checklist"], index=False, encoding="utf-8-sig")
    usage_log.to_csv(paths["usage_log"], index=False, encoding="utf-8-sig")
    paths["prompt_log"].write_text(
        build_prompt_log_markdown(usage_log, checklist), encoding="utf-8"
    )

    return paths


def run_llm_prompt_analysis(
    processed_dir: str | Path = "data/processed",
    raw_dir: str | Path = "data/raw",
    report_dir: str | Path = "reports",
) -> dict[str, object]:
    """11장 LLM 프롬프트 분석 보조 자료 생성 파이프라인을 실행합니다."""
    datasets = load_available_sales_data(processed_dir=processed_dir, raw_dir=raw_dir)
    dataset_summary = build_dataset_summary(datasets)
    column_summary = build_column_summary(datasets)
    safe_context_text = build_safe_context_text(dataset_summary, column_summary)
    prompt_templates = build_prompt_templates()
    checklist = build_llm_review_checklist()
    usage_log = build_llm_usage_log_template()
    output_paths = save_llm_prompt_outputs(
        dataset_summary=dataset_summary,
        column_summary=column_summary,
        safe_context_text=safe_context_text,
        prompt_templates=prompt_templates,
        checklist=checklist,
        usage_log=usage_log,
        report_dir=report_dir,
    )

    return {
        "datasets": datasets,
        "dataset_summary": dataset_summary,
        "column_summary": column_summary,
        "safe_context_text": safe_context_text,
        "prompt_templates": prompt_templates,
        "checklist": checklist,
        "usage_log": usage_log,
        "output_paths": output_paths,
    }
