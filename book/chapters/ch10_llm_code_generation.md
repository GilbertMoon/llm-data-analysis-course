# 10장. 분류 분석으로 주문 취소 여부 예측하기

회귀 분석이 숫자를 예측하는 문제라면, 분류 분석은 여러 범주 중 하나를 예측하는 문제입니다. 이 장에서는 온라인 쇼핑몰 데이터를 사용해 **완료 주문과 취소 주문을 구분하고 주문 취소 여부를 예측하는 이진 분류 모델**을 만들어 봅니다.

이번 장의 목표는 복잡한 모델을 만드는 것이 아닙니다. 다음 흐름을 정확하게 이해하는 것이 핵심입니다.

1. 예측할 범주를 명확하게 정의합니다.
2. 예측 시점에 사용할 수 있는 입력값만 선택합니다.
3. 데이터 누수와 병합 오류를 점검합니다.
4. 데이터를 학습, 검증, 테스트 데이터로 나눕니다.
5. 기준 모델과 Logistic Regression, Random Forest를 비교합니다.
6. 검증 데이터에서 모델과 임계값을 선택합니다.
7. 테스트 데이터는 최종 평가에 한 번만 사용합니다.
8. accuracy, precision, recall, f1-score와 혼동행렬을 함께 해석합니다.

## 1. 분류 분석은 범주를 예측한다

분류 분석은 결과가 몇 개의 범주 중 하나로 나뉘는 문제를 다룹니다.

| 문제 | 예측 대상 | 분류 유형 |
| --- | --- | --- |
| 주문이 취소될 것인가? | 완료 / 취소 | 이진 분류 |
| 고객이 이탈할 것인가? | 유지 / 이탈 | 이진 분류 |
| 이메일은 어떤 유형인가? | 정상 / 스팸 / 프로모션 | 다중 분류 |
| 상품 리뷰 감성은 어떤가? | 긍정 / 중립 / 부정 | 다중 분류 |

이번 실습에서는 다음과 같이 타깃을 정의합니다.

| `order_status` | `is_cancelled` | 분류에 사용 |
| --- | ---: | --- |
| `completed` | 0 | 사용 |
| `cancelled` | 1 | 사용 |
| `refunded` | - | 제외 |
| 기타 상태 | - | 제외 |

`cancelled`가 아니면 모두 0으로 두는 방식은 간단해 보이지만, `refunded`와 같은 다른 상태가 완료 주문에 섞일 수 있습니다. 그러면 0 클래스가 “완료 주문”이라는 설명과 실제 데이터가 달라집니다. 따라서 이번 장에서는 `completed`와 `cancelled`만 사용해 이진 분류 문제를 만듭니다.

## 2. 예측 시점과 입력값을 먼저 정한다

분류 모델에서 중요한 질문은 “언제 예측할 것인가?”입니다. 주문이 생성된 직후 취소 위험을 예측한다고 가정하면, 그 시점에 이미 알 수 있는 정보만 입력값으로 사용할 수 있습니다.

사용 가능한 후보는 다음과 같습니다.

- 고객 나이, 성별, 도시
- 결제수단
- 주문 상품 행 수
- 총 수량
- 주문 금액
- 주문 월과 요일
- 가입 후 경과일

반대로 다음 값은 입력값으로 사용할 수 없습니다.

- `order_status`
- `is_cancelled`
- 취소 완료 후 생성되는 정보
- 취소 사유처럼 예측 결과가 발생한 뒤 알 수 있는 정보

`order_status`는 정답을 만드는 데 사용한 컬럼입니다. 이를 입력값으로 넣으면 모델이 정답을 미리 보는 **데이터 누수(data leakage)** 가 발생합니다.

> 모델의 성능이 지나치게 높게 나오면 먼저 데이터 누수를 의심해야 합니다.

## 3. 실습 환경 준비하기

전체 실습은 `notebooks/ch10_llm_code_generation.ipynb`에서 진행할 수 있습니다. 저장소의 기존 링크 호환성을 위해 파일명은 유지하지만, 실제 주제는 10장 분류 분석입니다.

전처리 파일이 없다면 프로젝트 루트에서 먼저 다음 명령을 실행합니다.

```powershell
python scripts/preprocess_data.py
```

전체 분류 파이프라인은 다음 명령으로 실행할 수 있습니다.

```powershell
python scripts/run_classification_analysis.py
```

Notebook에서는 프로젝트 루트를 자동으로 찾는 방식을 사용합니다.

```python
from pathlib import Path


def find_project_root(start_path):
    start_path = Path(start_path).resolve()

    for candidate in [start_path, *start_path.parents]:
        if (
            (candidate / "requirements.txt").exists()
            and (candidate / "scripts").exists()
        ):
            return candidate

    raise FileNotFoundError(
        "프로젝트 루트 폴더를 찾을 수 없습니다."
    )


PROJECT_ROOT = find_project_root(Path.cwd())
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
```

## 4. 원본 상태와 타깃 범위를 확인한다

전처리된 데이터를 불러옵니다.

```python
import pandas as pd

customers = pd.read_csv(
    PROCESSED_DIR / "customers_clean.csv"
)
orders = pd.read_csv(
    PROCESSED_DIR / "orders_clean.csv"
)
order_items = pd.read_csv(
    PROCESSED_DIR / "order_items_clean.csv"
)
```

모델을 만들기 전에 주문 상태 분포를 확인합니다.

```python
orders["order_status"].value_counts(dropna=False)
```

이 단계에서 다음을 확인합니다.

- 완료 주문과 취소 주문이 모두 존재하는가?
- 환불 주문이나 다른 상태가 있는가?
- 상태값 표기가 `completed`, `cancelled`, `refunded`로 통일되어 있는가?
- 결측 상태값은 없는가?

분류 데이터 생성은 공통 함수를 사용합니다.

```python
from src.classification import (
    build_classification_dataset,
    target_distribution,
)

(
    model_data,
    numeric_features,
    categorical_features,
    merge_checks,
    data_quality_checks,
) = build_classification_dataset(
    customers=customers,
    orders=orders,
    order_items=order_items,
)

target_dist = target_distribution(model_data)
target_dist
```

이 함수는 다음 작업을 수행합니다.

- `completed`와 `cancelled` 주문만 남깁니다.
- `cancelled`를 1, `completed`를 0으로 변환합니다.
- 주문 상세 데이터를 주문 단위로 집계합니다.
- 고객 정보와 주문 특징을 안전하게 병합합니다.
- 병합 전후 행 수와 미매칭 건수를 기록합니다.
- 가입일보다 주문일이 앞선 비정상 날짜를 결측치로 처리합니다.
- 고객 이름처럼 모델에 필요하지 않은 정보는 병합 대상에서 제외합니다.

## 5. 주문 단위 특징을 만든다

주문 상세 데이터는 한 주문에 여러 행이 있을 수 있습니다. 따라서 주문 단위 모델을 만들려면 먼저 `order_id` 기준으로 집계해야 합니다.

```python
order_item_features = (
    order_items
    .groupby("order_id", as_index=False)
    .agg(
        item_count=("product_id", "count"),
        total_quantity=("quantity", "sum"),
        order_amount=("line_total", "sum"),
    )
)
```

각 특징은 다음 의미를 가집니다.

| 특징 | 의미 |
| --- | --- |
| `item_count` | 주문 상세 행 수 |
| `total_quantity` | 주문의 전체 상품 수량 |
| `order_amount` | 주문 상세 금액 합계 |
| `order_month` | 주문 월 |
| `order_dayofweek` | 주문 요일 번호 |
| `days_since_signup` | 가입일부터 주문일까지의 경과일 |

`days_since_signup`이 음수라면 주문일이 가입일보다 빠르다는 뜻입니다. 이는 시간 순서가 맞지 않는 데이터이므로 그대로 학습시키지 않고 결측치로 바꾼 뒤 파이프라인에서 처리합니다.

## 6. 병합은 행 수와 관계를 검증한다

`left merge`라고 해서 왼쪽 행 수가 항상 유지되는 것은 아닙니다. 오른쪽 키가 중복되면 왼쪽 한 행이 여러 행으로 늘어날 수 있습니다.

```python
model_data = orders.merge(
    order_item_features,
    on="order_id",
    how="left",
    validate="one_to_one",
    indicator=True,
)
```

`validate="one_to_one"`은 양쪽의 `order_id`가 한 번씩만 나타나야 한다는 뜻입니다. 관계가 예상과 다르면 오류를 발생시켜 잘못된 병합을 조기에 발견할 수 있습니다.

병합 후에는 다음을 확인합니다.

```python
model_data["_merge"].value_counts()
```

검증 항목은 다음과 같습니다.

| 검증 항목 | 확인 내용 |
| --- | --- |
| 키 중복 | 주문 또는 고객 키가 예상대로 고유한가? |
| 행 수 | 병합 전후 행 수가 같은가? |
| 미매칭 | `_merge == "left_only"`인 행이 있는가? |
| 중복 컬럼 | `_x`, `_y` 컬럼이 불필요하게 생기지 않았는가? |
| 누락 특징 | 주문 상세가 없어 0으로 채운 주문이 있는가? |

공통 함수가 만든 검증표는 다음처럼 확인합니다.

```python
display(merge_checks)
display(data_quality_checks)
```

## 7. 학습, 검증, 테스트 데이터를 분리한다

모델 학습과 최종 평가를 같은 데이터로 수행하면 성능이 낙관적으로 보입니다. 모델 종류와 임계값을 테스트 데이터에서 고르면 테스트 데이터가 사실상 검증 데이터로 사용됩니다.

이번 장에서는 데이터를 세 부분으로 나눕니다.

| 데이터 | 역할 | 사용 시점 |
| --- | --- | --- |
| train | 모델 학습 | 모델 파라미터 학습 |
| validation | 모델과 임계값 선택 | 여러 모델과 기준 비교 |
| test | 최종 성능 확인 | 선택이 끝난 뒤 한 번 평가 |

```python
from src.classification import (
    split_train_validation_test,
    build_split_summary,
)

(
    X_train,
    X_valid,
    X_test,
    y_train,
    y_valid,
    y_test,
    features,
) = split_train_validation_test(
    model_data=model_data,
    numeric_features=numeric_features,
    categorical_features=categorical_features,
    random_state=42,
)

split_summary = build_split_summary(
    y_train,
    y_valid,
    y_test,
)
split_summary
```

각 분할에는 완료와 취소 클래스가 모두 포함되어야 합니다. 함수 내부에서는 `stratify`를 사용해 클래스 비율이 크게 달라지지 않도록 합니다.

## 8. 전처리는 Pipeline 안에서 수행한다

숫자형 컬럼과 범주형 컬럼은 처리 방법이 다릅니다.

| 유형 | 처리 |
| --- | --- |
| 숫자형 | 중앙값 대체, 표준화 |
| 범주형 | 최빈값 대체, 원-핫 인코딩 |

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)

numeric_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]
)

categorical_transformer = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "onehot",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            numeric_transformer,
            numeric_features,
        ),
        (
            "cat",
            categorical_transformer,
            categorical_features,
        ),
    ]
)
```

전처리를 데이터 분할 전에 전체 데이터에 적용하면 검증·테스트 정보가 학습 과정에 섞일 수 있습니다. `Pipeline`을 사용하면 학습 데이터에서만 결측치 대체 기준과 인코딩 기준을 학습할 수 있습니다.

## 9. 기준 모델과 비교한다

복잡한 모델이 실제로 의미가 있는지 확인하려면 단순한 기준 모델이 필요합니다.

이번 장에서는 다음 세 모델을 비교합니다.

| 모델 | 역할 |
| --- | --- |
| Dummy Most Frequent | 가장 많은 클래스만 예측하는 기준 모델 |
| Logistic Regression | 선형 관계 기반의 기준 학습 모델 |
| Random Forest | 비선형 패턴을 학습하는 비교 모델 |

```python
from src.classification import (
    train_and_compare_on_validation,
)

(
    models,
    validation_comparison,
    validation_predictions,
    validation_probabilities,
) = train_and_compare_on_validation(
    X_train=X_train,
    X_valid=X_valid,
    y_train=y_train,
    y_valid=y_valid,
    numeric_features=numeric_features,
    categorical_features=categorical_features,
    random_state=42,
)

validation_comparison
```

학습 모델이 Dummy 기준 모델보다 나은지 먼저 확인해야 합니다. Dummy 모델과 큰 차이가 없다면 현재 특징으로 취소 여부를 예측하기 어렵거나 데이터에 예측 신호가 부족할 수 있습니다.

## 10. 분류 모델은 여러 지표로 평가한다

취소 주문처럼 비율이 낮은 대상을 예측할 때 accuracy만 보면 위험합니다.

| 지표 | 의미 | 중요해지는 상황 |
| --- | --- | --- |
| accuracy | 전체 예측 중 맞춘 비율 | 클래스가 비교적 균형적인 경우 |
| precision | 취소라고 예측한 것 중 실제 취소 비율 | 잘못된 경고 비용이 큰 경우 |
| recall | 실제 취소 중 찾아낸 비율 | 취소 주문을 놓치는 비용이 큰 경우 |
| f1-score | precision과 recall의 조화 평균 | 두 오류를 함께 고려할 경우 |

예를 들어 취소 주문이 10%라면 모든 주문을 완료라고 예측해도 accuracy는 90%입니다. 하지만 이 모델의 recall은 0입니다.

이번 실습에서는 검증 데이터의 f1-score를 우선 기준으로 모델을 선택하고, 동률이면 recall과 precision을 함께 확인합니다. 실제 프로젝트에서는 업무 비용에 따라 선택 기준을 바꿔야 합니다.

## 11. 임계값은 검증 데이터에서 선택한다

분류 모델은 보통 취소 확률을 출력합니다. 기본 임계값은 0.5이지만, 업무 목적에 따라 조정할 수 있습니다.

```python
from src.classification import (
    threshold_metrics,
    choose_threshold,
)

selected_model_name = (
    validation_comparison
    .query("model != 'Dummy Most Frequent'")
    .iloc[0]["model"]
)

selected_model = models[selected_model_name]
validation_proba = validation_probabilities[
    selected_model_name
]

threshold_df = threshold_metrics(
    y_valid,
    validation_proba,
)

selected_threshold = choose_threshold(threshold_df)
```

임계값을 낮추면 취소 주문을 더 많이 잡아 recall이 올라갈 수 있지만, 정상 주문을 취소 위험으로 잘못 분류해 precision이 낮아질 수 있습니다.

중요한 점은 임계값을 **테스트 데이터에서 고르지 않는 것**입니다. 모델과 임계값 선택은 검증 데이터에서 끝내고, 테스트 데이터는 최종 평가에만 사용합니다.

## 12. 테스트 데이터는 마지막에 한 번 평가한다

```python
from src.classification import (
    final_test_evaluation,
    confusion_matrix_dataframe,
)

(
    y_pred_test,
    y_proba_test,
    test_metrics,
) = final_test_evaluation(
    selected_model,
    X_test,
    y_test,
    threshold=selected_threshold,
)

confusion_df = confusion_matrix_dataframe(
    y_test,
    y_pred_test,
)

display(test_metrics)
display(confusion_df)
```

혼동행렬은 다음처럼 읽습니다.

| 구분 | 의미 |
| --- | --- |
| True Negative | 실제 완료 주문을 완료로 예측 |
| False Positive | 실제 완료 주문을 취소로 잘못 예측 |
| False Negative | 실제 취소 주문을 완료로 잘못 예측 |
| True Positive | 실제 취소 주문을 취소로 예측 |

어떤 오류가 더 중요한지는 업무 목적에 따라 달라집니다. 취소 방지 상담을 제공하려면 False Negative를 줄이는 것이 중요할 수 있습니다. 반면 잘못된 경고가 고객 경험을 해친다면 False Positive도 중요합니다.

## 13. 결과 저장 시 개인정보를 최소화한다

예측 결과를 저장할 때 고객명, 이메일, 주소처럼 모델 평가에 필요하지 않은 정보를 포함하지 않습니다.

```python
from src.classification import create_prediction_result

prediction_result = create_prediction_result(
    source_index=X_test.index,
    y_test=y_test,
    y_pred=y_pred_test,
    y_proba=y_proba_test,
    model_name=selected_model_name,
    threshold=selected_threshold,
)

prediction_result.head()
```

결과표에는 익명화된 레코드 ID, 실제값, 예측값, 예측 확률, 모델명, 임계값만 포함됩니다.

## 14. LLM이 만든 분류 코드를 검토한다

LLM은 모델링 코드 초안과 오류 설명에 도움을 줄 수 있습니다. 하지만 실행되는 코드가 올바른 분석 코드는 아닐 수 있습니다.

다음처럼 요청할 수 있습니다.

```text
온라인 쇼핑몰 주문 데이터로 완료 주문과 취소 주문을 구분하는
이진 분류 모델을 작성해 주세요.

타깃 기준:
- completed는 0
- cancelled는 1
- refunded와 기타 상태는 학습 대상에서 제외

검증 요구사항:
1. order_status와 is_cancelled를 feature에서 제외
2. 주문·주문상세·고객 병합에 validate와 indicator 사용
3. train/validation/test를 stratify로 분리
4. DummyClassifier, LogisticRegression, RandomForestClassifier 비교
5. 모델과 임계값은 validation에서 선택
6. test는 최종 평가에 한 번만 사용
7. accuracy, precision, recall, f1, confusion matrix 출력
8. 예측 결과에는 고객명과 개인정보를 포함하지 않음

데이터에 없는 컬럼은 만들지 말고,
각 단계의 검증 코드와 초보자용 설명을 함께 작성해 주세요.
```

LLM 코드 검토 기준은 다음과 같습니다.

| 검토 기준 | 확인할 질문 |
| --- | --- |
| 타깃 범위 | 완료와 취소만 비교하는가? |
| 상태 혼합 | 환불 주문이 0 클래스에 섞이지 않았는가? |
| 데이터 누수 | 정답 또는 사후 정보를 입력값으로 사용하지 않았는가? |
| 예측 시점 | feature가 실제 예측 시점에 존재하는가? |
| 병합 관계 | 키 중복과 미매칭을 확인했는가? |
| 데이터 분할 | train, validation, test를 구분했는가? |
| 모델 선택 | validation 성능으로 선택했는가? |
| 임계값 | validation에서 결정했는가? |
| 최종 평가 | test를 반복해서 확인하지 않았는가? |
| 기준 모델 | Dummy 모델보다 나은가? |
| 평가 지표 | accuracy 외 지표를 함께 보았는가? |
| 개인정보 | 불필요한 식별정보를 저장하지 않았는가? |
| 해석 | 예측 패턴을 취소 원인으로 단정하지 않았는가? |

## 15. 결과 해석에서 지켜야 할 선

다음 표현은 가능합니다.

```text
검증 데이터에서 Logistic Regression과 Random Forest를 비교했고,
선택한 모델과 임계값을 테스트 데이터에서 최종 평가했습니다.
취소 주문 탐지 성능을 확인하기 위해 accuracy뿐 아니라
precision, recall, f1-score와 혼동행렬을 함께 확인했습니다.
```

다음 표현은 피해야 합니다.

```text
이 모델은 고객이 주문을 취소하는 원인을 설명한다.
이 모델은 앞으로 모든 취소 주문을 정확하게 예측한다.
높은 성능이 나왔으므로 실제 서비스에 바로 적용할 수 있다.
```

현재 모델은 샘플 데이터 안의 패턴을 학습한 것입니다. 실제 서비스에 적용하려면 다음 검토가 추가로 필요합니다.

- 시간 순서를 고려한 데이터 분할
- 오탐과 미탐의 업무 비용
- 데이터 분포 변화
- 정기적인 재학습
- 개인정보와 접근 권한
- 특정 고객 집단에 대한 성능 편차
- 운영 중 성능 모니터링

## 16. 생성되는 산출물

전체 스크립트를 실행하면 다음 파일이 생성됩니다.

- `reports/ch10_classification_model_data.csv`
- `reports/ch10_target_distribution.csv`
- `reports/ch10_merge_checks.csv`
- `reports/ch10_data_quality_checks.csv`
- `reports/ch10_split_summary.csv`
- `reports/ch10_validation_model_comparison.csv`
- `reports/ch10_validation_threshold_metrics.csv`
- `reports/ch10_test_metrics.csv`
- `reports/ch10_classification_predictions.csv`
- `reports/ch10_confusion_matrix.csv`
- `reports/ch10_classification_report.csv`
- `reports/ch10_classification_checklist.csv`
- `reports/ch10_classification_summary.md`

결과 파일은 다음 기준을 만족해야 합니다.

| 점검 항목 | 확인 기준 |
| --- | --- |
| 타깃 정의 | completed=0, cancelled=1 |
| 제외 상태 | refunded 등은 학습 대상에서 제외 |
| 병합 | 행 수와 미매칭 검증표 존재 |
| 분할 | train/validation/test 비율 기록 |
| 모델 선택 | validation 결과표 존재 |
| 임계값 선택 | validation 임계값 비교표 존재 |
| 최종 성능 | test 성능표와 혼동행렬 존재 |
| 개인정보 | 예측 결과에 고객명 미포함 |
| 재현성 | 스크립트 재실행 시 동일 흐름으로 생성 |

## 17. 다음 장으로 이어지는 흐름

이번 장에서는 주문 취소 여부를 예측하는 분류 분석을 통해 타깃 정의, 데이터 누수, 병합 검증, 클래스 불균형, 기준 모델, 검증 데이터, 임계값, 최종 테스트 평가를 살펴보았습니다.

다음 장에서는 LLM을 데이터 분석 과정에 더 본격적으로 연결합니다. LLM은 분석 질문을 구체화하고 코드 초안을 만드는 데 도움이 되지만, 이번 장에서 확인한 것처럼 타깃 정의, 데이터 분할, 평가 기준, 개인정보 보호는 사람이 직접 검증해야 합니다.
