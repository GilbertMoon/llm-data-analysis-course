# Chapter 09 답안 양식. 회귀 분석으로 숫자 예측하기

> 이 내용을 `chapter09.ipynb`의 Markdown 셀로 작성합니다.

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:

## 1. 예측 문제 정의
- Target:
- 예측 단위:
- 예측 시점:
- 예측 시점에 알 수 있는 정보:
- 예측 시점에 알 수 없는 정보:

### 나의 해석과 판단
왜 이 예측 시점을 선택했는지 작성하세요.

---

## 2. Feature Leakage Audit

| feature | 예측 시점 사용 가능 | Target 계산 재료 | 사후 정보/ID | 최종 사용 | 판단 이유 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

- 금지 feature overlap 개수:
- 가장 위험하다고 판단한 feature:
- 이유:

![Leakage 점검](images/step02_leakage.png)

---

## 3. Target 생성과 관계 검증

### 계산 기준

```text
line_total =
order_total =
```

- line_total 검증 결과:
- orders ↔ target 관계 검증 결과:
- orders → customers 관계 검증 결과:

### 나의 해석과 판단
관계 검증 없이 병합만 수행하면 어떤 문제가 생길 수 있는지 작성하세요.

---

## 4. Train / Final Test 분할

- Train 시작일:
- Train 종료일:
- Train 행 수:
- Final Test 시작일:
- Final Test 종료일:
- Final Test 행 수:
- 같은 달력 날짜 중복 여부:

### 분할 판단
왜 이번 문제에서 시간 순서 분할을 사용하는지 작성하세요.

![시간 분할](images/step04_split.png)

---

## 5. Train TimeSeriesSplit 후보 비교

| 모델 | CV MAE 평균 | CV MAE 표준편차 | CV R² 평균 | 비고 |
| --- | ---: | ---: | ---: | --- |
| Baseline Mean | | | | |
| Linear Regression | | | | |
| Random Forest | | | | |

### Train CV로 선택한 비베이스라인 모델
- Selected Model:
- 선택 기준:
- Final Test 결과를 보기 전에 선택했는가: 예 / 아니오

### 나의 해석과 판단
CV 평균뿐 아니라 표준편차도 함께 봐야 하는 이유를 작성하세요.

---

## 6. Final Test: Baseline vs Frozen Model

| 모델 | selection role | Train MAE | Test MAE | Test RMSE | Test R² | Baseline 대비 MAE 개선율 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Baseline Mean | baseline | | | | | |
| Frozen Selected Model | selected_by_train_cv | | | | | |

![최종 회귀 평가](images/step06_final_metrics.png)

### 결과 관찰

### 나의 해석과 판단
- Frozen Model이 baseline보다 실제로 개선되었는가?
- MAE와 RMSE 차이에서 무엇을 볼 수 있는가?
- R²는 어떻게 해석할 수 있는가?

### 업무·분석적 의미
현재 오차 수준이 실제 사용에서 어떤 의미인지 작성하세요.

---

## 7. 대표 오차 사례

### 사례 1
- 실제값:
- 예측값:
- residual:
- absolute error:
- 관찰:
- 가능한 이유 후보:
- 추가 확인:

### 사례 2
- 실제값:
- 예측값:
- residual:
- absolute error:
- 관찰:
- 가능한 이유 후보:
- 추가 확인:

> 원인을 데이터가 직접 보여 주지 않는다면 사실처럼 단정하지 않습니다.

---

## 8. Validation Evidence

`reports/ch09_regression_validation.csv` 기준으로 작성하세요.

| check | value | status |
| --- | --- | --- |
| forbidden_feature_overlap | | |
| strict_train_before_test | | |
| selected_model_exists_in_train_cv | | |
| final_test_contains_baseline | | |
| final_test_contains_frozen_selected_model | | |
| test_rows_for_r2 | | |

### FAIL 항목
- 없음 / 있음:
- 있다면 원인과 수정 내용:

---

## 9. Evidence와 공개 범위

### 생성된 Evidence
- [ ] `ch09_regression_split_summary.csv`
- [ ] `ch09_regression_feature_audit.csv`
- [ ] `ch09_regression_cv_summary.csv`
- [ ] `ch09_regression_model_comparison.csv`
- [ ] `ch09_regression_validation.csv`
- [ ] `ch09_regression_checklist.csv`

### Internal 파일
- [ ] `ch09_regression_model_data_internal.csv`
- [ ] `ch09_regression_predictions_internal.csv`

### 공개 결과
- [ ] `ch09_regression_report.md`
- [ ] `ch09_actual_vs_predicted.png`
- [ ] `ch09_residual_histogram.png`

### 공개 범위 판단
왜 `order_id`가 포함된 예측 결과를 Internal로 구분해야 하는지 작성하세요.

---

## 10. 최종 사용 판단

- [ ] 현재 수준에서 참고용 사용 가능
- [ ] 추가 검증 후 사용 가능
- [ ] 현재 데이터로는 사용 보류

### 판단 근거
1.
2.
3.

### 업무적 위험

### 현재 데이터의 한계

### 다음 개선 우선순위
1.
2.
3.

---

## 11. 전체 재실행 확인

실행 명령:

```powershell
python scripts/run_regression_analysis.py
```

- 실행 성공 여부:
- Train CV Selected Model:
- Final Validation 전체 PASS 여부:
- Notebook 결과와 스크립트 결과의 일관성:

---

## 최종 체크

- [ ] Target과 예측 시점을 정의했습니다.
- [ ] Leakage Audit을 수행했습니다.
- [ ] Target 계산과 관계 검증을 확인했습니다.
- [ ] Train과 Final Test가 시간 순서로 엄격히 분리되었습니다.
- [ ] 전처리가 Pipeline 내부에서 학습됩니다.
- [ ] Train TimeSeriesSplit으로 후보를 비교했습니다.
- [ ] Final Test 전에 Selected Model을 고정했습니다.
- [ ] Final Test에서는 Baseline과 Frozen Model만 비교했습니다.
- [ ] MAE, RMSE, R²를 함께 해석했습니다.
- [ ] 대표 오차 사례를 관찰과 가설로 구분했습니다.
- [ ] Validation Evidence가 모두 PASS입니다.
- [ ] Internal 결과와 공개 결과를 구분했습니다.
- [ ] 낮은 성능도 숨기지 않았습니다.
- [ ] 전체 스크립트를 재실행했습니다.
- [ ] 최종 Notebook URL을 제출합니다.
