# Chapter 10 답안 양식. 분류 분석으로 주문 취소 여부 예측하기

> 이 내용을 `chapter10.ipynb`의 Markdown 셀로 작성합니다. 실제 실행 결과를 근거로 작성하고, 예측 패턴을 원인처럼 단정하지 않습니다.

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:

## 1. 분류 문제 정의
- 타깃:
- 0의 의미:
- 1의 의미:
- 제외한 상태:
- 예측 단위:
- 예측 시점:
- 예측 시점에 사용할 수 있는 정보:
- 예측 이후에만 알 수 있어 제외한 정보:

### 나의 해석과 판단
왜 이 타깃 범위와 예측 시점을 사용했는지 작성하세요.

---

## 2. Feature Contract와 Leakage Audit

### 사용한 숫자형 Feature

### 사용한 범주형 Feature

### 금지 Feature

```text
order_status
is_cancelled
order_id
customer_id
product_id
취소 이후 정보
```

### 나의 해석과 판단
파일에 컬럼이 존재하는 것과 예측 시점에 사용할 수 있는 것이 왜 다른지 작성하세요.

---

## 3. 주문 단위 특징과 병합 검증

### 계산 관계 확인

```text
line_total = quantity × unit_price
```

- 계산 불일치 건수:
- 주문 특징 `order_id` 중복 건수:

### 병합 검증

| 병합 | 관계 | 병합 전 행 수 | 병합 후 행 수 | 미매칭 | 판정 |
| --- | --- | ---: | ---: | ---: | --- |
| 주문 ↔ 주문 특징 | one_to_one | | | | |
| 주문 ↔ 고객 | many_to_one | | | | |

### 결과 관찰

### 나의 해석과 판단
미매칭을 원인 확인 없이 0으로 채우면 안 되는 이유를 작성하세요.

---

## 4. 클래스 비율

| 클래스 | 의미 | 개수 | 비율 |
| ---: | --- | ---: | ---: |
| 0 | completed | | |
| 1 | cancelled | | |

![클래스 비율](images/step02_class_ratio.png)

### 결과 관찰

### 나의 해석과 판단
클래스 불균형이 accuracy 해석에 어떤 영향을 주는지 작성하세요.

---

## 5. Dummy Baseline과 Validation 모델 비교

| 모델 | Accuracy | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Dummy Most Frequent | | | | |
| Logistic Regression | | | | |
| Random Forest | | | | |

![Baseline 비교](images/step03_baseline.png)

- Validation에서 선택한 모델:

### 결과 관찰

### 나의 해석과 판단
선택한 모델이 Dummy baseline보다 어떤 점에서 나아졌는지 작성하세요.

### 한계와 추가 확인 사항

---

## 6. Train / Validation / Test 역할

| Split | 역할 | 클래스 0 건수 | 클래스 1 건수 |
| --- | --- | ---: | ---: |
| Train | 모델 학습 | | |
| Validation | 모델·Threshold 선택 | | |
| Test | 선택 이후 최종 평가 | | |

### 나의 해석과 판단
왜 Test를 모델 또는 Threshold 선택에 사용하면 안 되는지 작성하세요.

### 교육용 random split의 한계
실제 미래 주문 예측 운영 전에 추가해야 할 평가를 작성하세요.

---

## 7. Validation 성능과 우선 지표

- Accuracy:
- Precision:
- Recall:
- F1:

### 내가 가장 중요하게 본 지표

### 그 이유

> 실제 FP/FN 비용 정보가 없다면 가정임을 명시하세요.

---

## 8. Threshold 비교

| Threshold | Precision | Recall | F1 | 예상 특징 |
| ---: | ---: | ---: | ---: | --- |
| | | | | |
| | | | | |
| | | | | |

![Threshold 비교](images/step05_threshold.png)

### 내가 선택한 Threshold

### 선택 이유

### 나의 해석과 판단
Threshold를 Final Test가 아니라 Validation에서 정해야 하는 이유를 작성하세요.

---

## 9. FP/FN 해석

- FP 의미:
- FN 의미:
- 현재 목적에서 더 부담스러울 수 있는 오류:
- 그 판단에 추가로 필요한 업무 정보:

![Confusion Matrix](images/step06_confusion_matrix.png)

### 업무·분석적 의미

### 한계와 추가 확인 사항

---

## 10. Final Test

- 고정한 모델:
- 고정한 Threshold:
- Accuracy:
- Precision:
- Recall:
- F1:
- Validation 대비 변화:

### 결과 관찰

### 나의 해석과 판단
Final Test 결과를 보고 모델의 일반화 가능성을 어떻게 판단했는지 작성하세요.

### 선택 보호 확인
- [ ] Test 결과를 보기 전에 모델을 고정했습니다.
- [ ] Test 결과를 보기 전에 Threshold를 고정했습니다.
- [ ] Test 결과를 본 뒤 같은 Test를 이용해 선택을 바꾸지 않았습니다.

---

## 11. Internal / Public 결과 구분

### 공개 Prediction 컬럼

```text
record_id
actual_is_cancelled
predicted_is_cancelled
cancel_probability
model
threshold
```

### 공개 결과에 없어야 할 컬럼

```text
source_index
order_id
customer_id
product_id
```

### 결과 관찰

### 나의 해석과 판단
모델 오류 분석용 내부 자료와 공개 결과를 왜 분리해야 하는지 작성하세요.

---

## 12. Validation Evidence

다음 Evidence 중 확인한 항목에 체크합니다.

- [ ] `ch10_target_distribution.csv`
- [ ] `ch10_feature_audit.csv`
- [ ] `ch10_merge_checks.csv`
- [ ] `ch10_data_quality_checks.csv`
- [ ] `ch10_split_summary.csv`
- [ ] `ch10_validation_model_comparison.csv`
- [ ] `ch10_validation_threshold_metrics.csv`
- [ ] `ch10_test_metrics.csv`
- [ ] `ch10_confusion_matrix.csv`
- [ ] `ch10_classification_validation.csv`

### 자동 Validation 결과

### 자동 PASS가 의미하지 않는 것
운영 적합성, 공정성, 시간에 따른 성능 변화 등 자동 검증만으로 판단할 수 없는 내용을 작성하세요.

---

## 13. 최종 사용 판단

- [ ] 참고용 사용 가능
- [ ] 추가 검증 후 사용 가능
- [ ] 현재 사용 보류

### 판단 근거
1.
2.
3.

### 현재 모델의 가장 큰 위험

### 다음 개선 우선순위
1.
2.
3.

### 예측과 인과 구분
현재 모델에서 확인한 것은 어떤 **예측 패턴**이며, 어떤 **원인 주장**은 아직 할 수 없는지 작성하세요.

---

## 최종 체크

- [ ] `completed=0`, `cancelled=1` 타깃 범위를 정의했습니다.
- [ ] `refunded`와 기타 상태를 제외했습니다.
- [ ] 예측 시점과 Feature Contract를 정의했습니다.
- [ ] target, ID, 사후 정보를 feature에서 제외했습니다.
- [ ] `line_total = quantity × unit_price`를 검증했습니다.
- [ ] 주문 단위 특징과 병합 관계를 검증했습니다.
- [ ] 클래스 비율을 확인했습니다.
- [ ] Dummy baseline과 비교했습니다.
- [ ] Train / Validation / Test 역할을 구분했습니다.
- [ ] 모델을 Validation에서 선택했습니다.
- [ ] Threshold를 Validation에서 선택했습니다.
- [ ] Final Test 전에 선택을 고정했습니다.
- [ ] Precision / Recall / F1을 해석했습니다.
- [ ] FP/FN의 의미를 설명했습니다.
- [ ] Public prediction에서 식별자를 제거했습니다.
- [ ] Validation Evidence를 확인했습니다.
- [ ] random split의 한계를 기록했습니다.
- [ ] 예측 패턴을 원인처럼 단정하지 않았습니다.
- [ ] 최종 Notebook URL을 제출합니다.
