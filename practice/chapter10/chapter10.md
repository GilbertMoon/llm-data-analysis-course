# 10장 실습. 분류 분석으로 주문 취소 여부 예측하기

> 목표는 accuracy 하나만 보고 모델을 선택하는 것이 아니라 **타깃 정의, 예측 시점, 데이터 누수, 클래스 비율, baseline, precision·recall·F1, threshold, FP/FN, Final Test 독립성, 공개 결과의 식별자 제거**까지 함께 검증하는 것입니다.

## 공통 제출 기준

- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter10/templates/chapter10_assignment.md`
- 주 제출물: `chapter10/chapter10.ipynb`

공식 Notebook 파일명은 프로젝트 초기 명칭을 유지합니다.

```text
notebooks/ch10_llm_code_generation.ipynb
```

현재 Chapter 10의 실제 주제는 **주문 취소 여부 분류 분석**입니다.

공통 실행 파일:

```text
scripts/prepare_ch10_data.py
scripts/run_classification_analysis.py
src/classification.py
```

Chapter10은 Chapter05 오류 탐지용 전용 Raw를 사용하지 않습니다.

```text
사용하지 않음
practice/chapter05/data/raw
```

공통 프로젝트 데이터인 `data/raw/`를 사용합니다.

---

## STEP 0. 제출용 Notebook과 입력 준비

공식 Notebook을 개인 저장소의 `chapter10/chapter10.ipynb`로 복사합니다.

Public 저장소 루트에서 먼저 실행합니다.

```powershell
python -m pip install -r requirements.txt
python scripts/prepare_ch10_data.py
```

입력 준비 흐름:

```text
data/raw
→ 공통 전처리
→ FK 관계 검증
→ data/processed 저장
```

`data/processed/`에 최소 다음 파일이 있어야 합니다.

```text
customers_clean.csv
orders_clean.csv
order_items_clean.csv
```

---

## STEP 1. Target Contract와 예측 시점 정의

이번 이진 분류는 다음 범위만 사용합니다.

```text
completed = 0
cancelled = 1
refunded / 기타 상태 = 제외
```

답안에 다음을 작성합니다.

```text
분류 타깃은 무엇인가?
0과 1은 각각 무엇을 의미하는가?
예측 단위는 무엇인가?
언제 예측하는가?
그 시점에 알 수 있는 정보는 무엇인가?
예측 이후에만 알 수 있어 제외한 정보는 무엇인가?
```

금지 feature 예시:

```text
order_status
is_cancelled
order_id
customer_id
product_id
cancel_reason
cancelled_at
취소 이후 생성되는 정보
```

`refunded`를 자동으로 0으로 만들지 않습니다.

---

## STEP 2. 주문 단위 특징과 데이터 품질 검증

예측 단위는 주문 1건입니다. `order_items`는 주문 단위로 집계합니다.

```text
item_count
total_quantity
order_amount
```

집계 전에 다음 관계를 확인합니다.

```text
line_total = quantity × unit_price
```

계산 불일치나 필수값 문제를 모델링 단계에서 숨기지 않습니다.

---

## STEP 3. 병합 관계와 Feature Audit

기대 관계:

```text
orders 1 ↔ 1 order_item_features
orders many → one customers
```

확인할 항목:

```text
validate 관계
병합 전후 행 수
unmatched_count
필수 feature 결측
```

미매칭을 원인 확인 없이 `fillna(0)`으로 바꾸지 않습니다.

Feature Audit에서는 target, ID, 사후 정보가 입력에 들어가지 않았는지 확인합니다.

---

## STEP 4. 클래스 비율과 Dummy Baseline

타깃 클래스의 개수와 비율을 확인합니다.

```text
0 = completed
1 = cancelled
```

불균형 데이터에서는 모든 주문을 다수 클래스로 예측해도 accuracy가 높아질 수 있습니다.

따라서 `Dummy Most Frequent`를 반드시 기준선으로 포함합니다.

비교 지표:

- Accuracy
- Precision
- Recall
- F1

실제 모델이 Dummy보다 어떤 점에서 개선되었는지 작성합니다.

---

## STEP 5. Train / Validation / Test 역할 구분

이번 교육용 실습은 클래스 비율을 유지하는 stratified random split을 사용합니다.

```text
Train
= 모델 파라미터 학습

Validation
= 모델 선택 + threshold 선택

Test
= 모든 선택이 끝난 뒤 마지막 평가
```

각 split에 두 클래스가 모두 존재하는지 확인합니다.

> random split은 교육용 설계입니다. 실제 미래 주문 예측 운영 전에는 시간 순서 평가와 out-of-time 검증이 추가로 필요합니다.

---

## STEP 6. Pipeline 전처리

숫자형:

```text
median imputation
→ StandardScaler
```

범주형:

```text
most_frequent imputation
→ OneHotEncoder(handle_unknown="ignore")
```

전처리는 전체 데이터에서 미리 fit하지 않고 Pipeline 안에서 **Train으로만 학습**합니다.

---

## STEP 7. Validation에서 후보 모델 선택

후보:

```text
Dummy Most Frequent
Logistic Regression
Random Forest
```

Validation에서 다음을 비교합니다.

```text
Accuracy
Precision
Recall
F1
```

Test 결과를 보기 전에 `selected_model_name`을 기록합니다.

---

## STEP 8. Validation에서 Threshold 선택

선택 모델의 Validation probability를 여러 threshold에서 비교합니다.

```text
threshold 낮춤
→ Recall 증가 가능
→ FP 증가 가능

threshold 높임
→ Precision 증가 가능
→ FN 증가 가능
```

선택한 threshold와 이유를 답안에 작성합니다.

**Final Test를 보며 threshold를 고르지 않습니다.**

---

## STEP 9. Final Test 1회 평가

Validation에서 모델과 threshold를 모두 고정한 뒤 Final Test를 확인합니다.

평가 항목:

```text
Accuracy
Precision
Recall
F1
Confusion Matrix
FP / FN
```

Final Test가 기대보다 낮아도 같은 Test를 보며 모델이나 threshold를 다시 고르지 않습니다.

---

## STEP 10. FP/FN 업무적 의미 해석

```text
FP
= 완료 주문을 취소 위험으로 예측

FN
= 취소 주문을 완료로 예측
```

답안에 다음을 작성합니다.

```text
FP는 어떤 비용을 만들 수 있는가?
FN은 어떤 비용을 만들 수 있는가?
현재 목적에서는 어느 오류가 더 부담스러울 수 있는가?
그 판단을 확정하려면 어떤 업무 정보가 필요한가?
```

수업 데이터만으로 실제 업무 비용을 확정하지 않습니다.

---

## STEP 11. Internal / Public 결과 구분

내부 오류 분석에는 source index나 식별자가 필요할 수 있습니다.

공개 prediction에는 다음과 같은 최소 결과만 둡니다.

```text
record_id
actual_is_cancelled
predicted_is_cancelled
cancel_probability
model
threshold
```

공개 결과에 다음 컬럼이 없어야 합니다.

```text
source_index
order_id
customer_id
product_id
```

---

## STEP 12. Validation Evidence 확인

대표 Evidence:

```text
reports/ch10_target_distribution.csv
reports/ch10_feature_audit.csv
reports/ch10_merge_checks.csv
reports/ch10_data_quality_checks.csv
reports/ch10_split_summary.csv
reports/ch10_validation_model_comparison.csv
reports/ch10_validation_threshold_metrics.csv
reports/ch10_test_metrics.csv
reports/ch10_classification_predictions.csv
reports/ch10_confusion_matrix.csv
reports/ch10_classification_validation.csv
reports/ch10_classification_summary.md
```

자동 Validation PASS는 현재 코드 계약 검증입니다. 운영 적합성, 공정성, 시간에 따른 성능 변화까지 자동으로 보장하지 않습니다.

---

## STEP 13. 전체 스크립트 재실행

```powershell
python scripts/prepare_ch10_data.py
python scripts/run_classification_analysis.py
```

Notebook과 Script에서 타깃, feature, split, 모델 선택, threshold 선택, Final Test 규칙이 같은지 확인합니다.

---

## STEP 14. 실제 사용 가능성 판단

다음 중 하나를 선택합니다.

```text
참고용 사용 가능
추가 검증 후 사용 가능
현재 사용 보류
```

근거에는 최소 다음을 포함합니다.

- 클래스 비율
- Dummy baseline 대비 개선
- Precision / Recall / F1
- FP/FN 비용에 대한 가정
- Threshold 선택 이유
- Final Test 결과
- random split 한계
- 공개 결과의 식별자 제거 여부

예측 패턴을 취소 원인으로 단정하지 않습니다.

---

## 최종 제출

```text
chapter10/
├─ chapter10.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter10/chapter10.ipynb
```

## 완료 체크

- [ ] `completed=0`, `cancelled=1` 타깃 범위를 정의했습니다.
- [ ] `refunded`와 기타 상태를 제외했습니다.
- [ ] 예측 시점과 Feature Contract를 작성했습니다.
- [ ] target, ID, 사후 정보를 feature에서 제외했습니다.
- [ ] `line_total = quantity × unit_price`를 검증했습니다.
- [ ] 주문 단위 특징과 병합 관계를 검증했습니다.
- [ ] 클래스 비율을 확인했습니다.
- [ ] Dummy baseline과 비교했습니다.
- [ ] Train / Validation / Test 역할을 구분했습니다.
- [ ] Pipeline 전처리를 Train으로 학습했습니다.
- [ ] 모델을 Validation에서 선택했습니다.
- [ ] Threshold를 Validation에서 선택했습니다.
- [ ] Final Test 전에 모델과 Threshold를 고정했습니다.
- [ ] Precision / Recall / F1과 FP/FN을 해석했습니다.
- [ ] Public prediction에서 식별자를 제거했습니다.
- [ ] Validation Evidence를 확인했습니다.
- [ ] random split의 교육용 한계를 기록했습니다.
- [ ] 최종 사용 판단과 한계를 작성했습니다.
- [ ] 최종 Notebook URL을 제출합니다.
