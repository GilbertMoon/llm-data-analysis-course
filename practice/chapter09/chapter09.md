# 9장 실습. 회귀 분석으로 숫자 예측하기

> 목표는 모델을 한 번 실행하는 것이 아니라 **예측 시점에 사용할 수 있는 정보만 사용하고, 누수를 막고, Train 기간에서 모델 선택을 끝낸 뒤 Final Test로 마지막 평가를 수행하는 것**입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter09/templates/chapter09_assignment.md`
- 주 제출물: `chapter09/chapter09.ipynb`

공식 회귀 Notebook:

```text
notebooks/ch09_regression_analysis.ipynb
```

보조 실행 스크립트:

```text
scripts/run_regression_analysis.py
```

> `notebooks/ch09_llm_prompt_analysis.ipynb`는 과거 파일명과의 호환용 안내 자산이며 현재 Chapter09 회귀 실습의 기준 Notebook이 아닙니다.

---

## STEP 0. 제출용 Notebook 준비

공식 Notebook을 복사해 개인 저장소의 다음 파일로 사용합니다.

```text
chapter09/chapter09.ipynb
```

실습 시작 전 processed 파일을 확인합니다.

```text
data/processed/customers_clean.csv
data/processed/orders_clean.csv
data/processed/order_items_clean.csv
```

없다면 Public 프로젝트 루트에서 먼저 실행합니다.

```powershell
python scripts/preprocess_data.py
```

---

## STEP 1. 예측 문제와 시점을 먼저 정의

다음을 Notebook Markdown 셀에 먼저 작성합니다.

```text
무엇을 예측하는가?
예측 단위는 무엇인가?
언제 예측하는가?
그 시점에 실제로 알 수 있는 정보는 무엇인가?
```

이번 교육용 문제의 기준은 다음과 같습니다.

```text
Target = order_total
예측 단위 = 주문 1건
order_total = 같은 order_id의 line_total 합계
line_total = quantity × unit_price
```

중요한 것은 `quantity`, `unit_price`, `line_total`을 Target 생성에는 사용하지만 feature에는 넣지 않는 것입니다.

---

## STEP 2. Feature Leakage Audit

각 feature에 대해 다음 질문을 합니다.

| feature | 예측 시점에 사용 가능 | Target 계산 재료 | 사후 정보/ID | 최종 사용 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

이번 실습의 허용 feature:

```text
order_month
order_dayofweek
age
payment_method
gender
city
```

대표 금지 feature:

```text
order_total
line_total
quantity
unit_price
item_count
total_quantity
avg_unit_price
order_status
order_id
customer_id
product_id
```

자동 Evidence:

```text
reports/ch09_regression_feature_audit.csv
```

누수 위험 feature를 조용히 삭제해서 넘어가는 것이 아니라 **왜 사용할 수 없는지 설명할 수 있어야 합니다.**

---

## STEP 3. Target 생성과 관계 검증

공식 Notebook은 다음을 확인합니다.

```text
line_total = quantity × unit_price
order_total = order_id별 line_total 합계
```

그리고 다음 관계에서 조용한 행 손실을 허용하지 않습니다.

```text
orders ↔ order_total     one_to_one
orders → customers       many_to_one
```

주문에 상세가 없거나 상세가 부모 주문에 연결되지 않는 경우 정상 모델링으로 처리하지 않습니다.

---

## STEP 4. Train / Final Test 시간 분할

이번 장에서는 랜덤 분할보다 시간 순서를 사용합니다.

```text
과거 주문
→ Train

미래에 가까운 마지막 기간
→ Final Test
```

같은 달력 날짜가 양쪽에 동시에 포함되지 않아야 합니다.

```text
train max date
<
final test min date
```

자동 Evidence:

```text
reports/ch09_regression_split_summary.csv
```

Final Test는 이 시점부터 **보호 구간**으로 생각합니다. 모델과 feature를 선택하는 데 반복 사용하지 않습니다.

---

## STEP 5. 전처리는 Pipeline 내부에서 수행

숫자형 feature:

```text
median imputation
→ StandardScaler
```

범주형 feature:

```text
most_frequent imputation
→ OneHotEncoder(handle_unknown="ignore")
```

이 처리를 전체 데이터에 미리 `fit`하지 않습니다.

```text
Pipeline
→ 각 Train Fold에서 fit
→ Validation / Final Test에는 transform만 적용
```

---

## STEP 6. 후보 모델과 Baseline 준비

후보는 다음 세 가지입니다.

```text
Baseline Mean = DummyRegressor(strategy="mean")
Linear Regression
Random Forest
```

Baseline은 단순한 참고용 장식이 아닙니다.

```text
복잡한 모델
vs
훈련 기간 평균만 예측하는 단순 모델
```

을 비교해 현재 feature가 실제로 유용한 신호를 제공하는지 판단합니다.

---

## STEP 7. Train 기간 TimeSeriesSplit으로 후보 비교

**이 단계에서는 Final Test 성능을 보지 않습니다.**

공식 흐름:

```text
Train
→ TimeSeriesSplit
→ 각 후보의 cv_MAE_mean / cv_MAE_std / cv_R2_mean 확인
```

자동 Evidence:

```text
reports/ch09_regression_cv_summary.csv
```

비베이스라인 후보인 `Linear Regression`, `Random Forest` 중 `cv_MAE_mean`이 더 낮은 모델을 선택합니다.

---

## STEP 8. Selected Model을 고정

다음 순서가 중요합니다.

```text
Train CV 결과 확인
→ Selected Model 결정
→ 선택 고정
```

그 뒤에야 Final Test를 사용합니다.

```text
테스트 MAE 확인
→ 모델 선택
```

순서로 진행하면 안 됩니다.

Notebook에 선택된 모델 이름을 기록하고 왜 선택되었는지 Train CV 결과로 설명합니다.

---

## STEP 9. Final Test에서 Baseline과 Frozen Model만 평가

최종 비교 대상은 두 개입니다.

```text
Baseline Mean
vs
Frozen Selected Model
```

확인 지표:

```text
train_MAE
test_MAE
test_RMSE
test_R2
MAE_improvement_vs_baseline_pct
```

자동 Evidence:

```text
reports/ch09_regression_model_comparison.csv
```

Final Test 결과가 기대보다 낮더라도 같은 Test를 보고 다른 후보로 교체하지 않습니다.

---

## STEP 10. MAE, RMSE, R² 해석

점수만 복사하지 말고 다음 질문에 답합니다.

```text
MAE는 평균적으로 얼마만큼 틀린다는 뜻인가?
RMSE가 MAE보다 많이 크다면 일부 큰 오차가 있는가?
R²가 0 또는 음수라면 평균 예측과 비교해 어떤 의미인가?
Baseline 대비 MAE가 실제로 개선되었는가?
```

R²가 음수라고 해서 코드가 반드시 틀린 것은 아닙니다.

현재 feature만으로 예측 신호가 약할 수 있습니다.

---

## STEP 11. 예측 오차 진단

고정 모델의 Final Test 결과에서 다음을 확인합니다.

```text
actual_order_total
predicted_order_total
residual
abs_error
```

대표 큰 오차 사례 2~3개를 골라 다음을 작성합니다.

```text
무엇을 관찰했는가?
어떤 이유가 가능해 보이는가?
현재 데이터로 원인을 확정할 수 있는가?
추가로 어떤 정보가 필요한가?
```

내부 진단 파일:

```text
reports/ch09_regression_predictions_internal.csv
```

이 파일은 `order_id`를 포함할 수 있으므로 공개 보고서와 구분합니다.

---

## STEP 12. 자동 Validation 확인

다음 파일을 확인합니다.

```text
reports/ch09_regression_validation.csv
```

핵심 검사:

```text
forbidden_feature_overlap = 0
strict_train_before_test = PASS
selected_model_exists_in_train_cv = PASS
final_test_contains_baseline = PASS
final_test_contains_frozen_selected_model = PASS
test_rows_for_r2 = PASS
```

하나라도 FAIL이면 Chapter09 모델링을 완료 상태로 처리하지 않습니다.

---

## STEP 13. 전체 스크립트 재실행

프로젝트 루트에서 실행합니다.

```powershell
python scripts/run_regression_analysis.py
```

다음 출력 순서를 확인합니다.

```text
시간 순서 분할
→ Feature Audit
→ Train TimeSeriesSplit 후보 비교
→ Train CV로 고정한 모델
→ Final Test: Baseline vs Frozen Model
→ 자동 Validation
→ 내부 예측 오차
→ 저장 결과
```

Notebook의 중간 메모리 상태가 아니라 새 실행에서도 같은 절차가 재현되어야 합니다.

---

## STEP 14. 모델 사용 가능성 판단

다음 중 하나를 선택하고 근거를 작성합니다.

```text
현재 수준에서 참고용으로 사용 가능
추가 검증 후 사용 가능
현재 데이터로는 사용 보류
```

최소 다음을 근거로 사용합니다.

```text
Train CV 안정성
Baseline 대비 Final Test 성능
MAE / RMSE / R²
누수 검증
시간 분할
대표 오류 패턴
현재 데이터의 한계
```

낮은 성능도 숨기지 않습니다. 누수 feature를 넣어 점수를 높이는 것은 개선이 아닙니다.

---

## STEP 15. 주요 산출물 확인

모델링 Evidence:

```text
reports/ch09_regression_split_summary.csv
reports/ch09_regression_feature_audit.csv
reports/ch09_regression_cv_summary.csv
reports/ch09_regression_model_comparison.csv
reports/ch09_regression_validation.csv
reports/ch09_regression_checklist.csv
```

내부 진단:

```text
reports/ch09_regression_model_data_internal.csv
reports/ch09_regression_predictions_internal.csv
```

공개 보고서와 그래프:

```text
reports/ch09_regression_report.md
reports/figures/ch09_actual_vs_predicted.png
reports/figures/ch09_residual_histogram.png
```

---

## 최종 제출

```text
chapter09/
├─ chapter09.ipynb
└─ images/
```

제출 URL 예시:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter09/chapter09.ipynb
```

## 완료 체크

- [ ] Target과 예측 시점을 정의했습니다.
- [ ] Feature Leakage Audit을 수행했습니다.
- [ ] Target 계산 관계와 병합 관계를 확인했습니다.
- [ ] 같은 날짜가 Train과 Final Test에 동시에 들어가지 않습니다.
- [ ] 전처리가 Pipeline 내부에서 Train으로만 학습됩니다.
- [ ] Dummy Baseline을 포함했습니다.
- [ ] Train TimeSeriesSplit으로 후보를 비교했습니다.
- [ ] Final Test 전에 Selected Model을 고정했습니다.
- [ ] Final Test에서는 Baseline과 Frozen Model만 평가했습니다.
- [ ] MAE, RMSE, R²를 함께 해석했습니다.
- [ ] 대표 오차 사례를 확인했습니다.
- [ ] `ch09_regression_validation.csv`가 모두 PASS입니다.
- [ ] 낮은 성능을 숨기거나 누수 feature로 보완하지 않았습니다.
- [ ] 내부 식별자 결과와 공개 결과를 구분했습니다.
- [ ] 전체 스크립트를 새 실행으로 재현했습니다.
- [ ] 최종 Notebook URL을 제출합니다.
