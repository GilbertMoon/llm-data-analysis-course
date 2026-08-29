# 9장 실습. 회귀 분석으로 숫자 예측하기

> 목표는 모델을 한 번 실행하는 것이 아니라 **예측 시점에 사용할 수 있는 정보만 사용하고, 누수를 막고, baseline과 비교해 모델의 실제 가치를 판단하는 것**입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter09/templates/chapter09_assignment.md`
- 주 제출물: `chapter09/chapter09.ipynb`

현재 회귀 실습 Notebook:

```text
notebooks/ch09_regression_analysis.ipynb
```

> `notebooks/ch09_llm_prompt_analysis.ipynb`는 과거 파일명/보조 자산일 수 있으므로 이번 장의 회귀 실습 기준 파일로 사용하지 않습니다.

보조 스크립트:

```text
scripts/run_regression_analysis.py
```

## STEP 0. 제출용 Notebook 준비
공식 회귀 Notebook을 복사해 `chapter09/chapter09.ipynb`로 사용합니다.

## STEP 1. 예측 문제 정의
다음을 먼저 작성합니다.

```text
무엇을 예측하는가?
예측 단위는 무엇인가?
언제 예측하는가?
그 시점에 실제로 알 수 있는 정보는 무엇인가?
```

타깃을 계산하는 데 사용한 정보를 feature로 다시 넣지 않습니다.

## STEP 2. 데이터 누수 점검
각 feature에 대해 다음 표를 만듭니다.

| feature | 예측 시점에 알 수 있는가? | 타깃 계산 재료인가? | 사용 여부 |
| --- | --- | --- | --- |
|  |  |  |  |

누수 의심 feature는 제거하고 이유를 기록합니다.

## STEP 3. 데이터 분할 확인
시간 정보가 있는 문제라면 미래 데이터가 학습 데이터에 섞이지 않도록 시간 순서를 고려합니다.

제출 답안에 반드시 기록:
- train 기간/범위
- validation 기간/범위
- final test 기간/범위
- 왜 이 분할을 선택했는가

최종 test는 모델/하이퍼파라미터/기준 선택에 반복 사용하지 않습니다.

## STEP 4. baseline 만들기
복잡한 모델보다 먼저 단순 기준을 계산합니다.

예:
- 평균 예측
- 중앙값 예측
- 단순 회귀 기준

모델이 baseline보다 실제로 나아졌는지 비교합니다.

## STEP 5. 회귀 모델 학습과 평가
Notebook을 순서대로 실행하고 MAE, RMSE, R² 등 제공된 평가 지표를 기록합니다.

점수만 복사하지 말고 다음을 작성합니다.

```text
이 오차 크기가 실제 목표값 규모와 비교해 어느 정도인가?
baseline보다 얼마나 나아졌는가?
특정 구간에서 오차가 더 큰가?
```

## STEP 6. 예측 오차 관찰
실제값과 예측값, 잔차/오차가 제공되는 경우 함께 확인합니다.

대표 오류 사례를 2~3개 선택해:
- 어떤 조건에서 틀렸는가
- 왜 그런 패턴이 생겼을 가능성이 있는가
- 추가로 필요한 feature/데이터는 무엇인가
를 작성합니다.

## STEP 7. 최종 test 평가
validation에서 모든 선택을 끝낸 뒤 final test를 마지막 검증으로 사용합니다.

최종 test 성능이 validation과 다르면 차이를 숨기지 않고 이유 후보를 작성합니다.

## STEP 8. 스크립트 재실행
가능하면 실행합니다.

```powershell
python scripts/run_regression_analysis.py
```

Notebook과 스크립트가 같은 타깃/범위/분할 원칙을 사용하는지 확인합니다.

## STEP 9. 모델 사용 가능성 판단
다음 중 하나로 판단하고 근거를 씁니다.

```text
현재 수준에서 참고용으로 사용 가능
추가 검증 후 사용 가능
현재 데이터로는 사용 보류
```

판단에는 최소 다음을 포함합니다.
- baseline 대비 성능
- 오차 크기
- 누수 점검 결과
- 데이터 범위
- 업무적 위험

## 최종 제출

```text
chapter09/
├─ chapter09.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter09/chapter09.ipynb
```

## 완료 체크
- [ ] 타깃/예측 시점 정의
- [ ] feature leakage 점검
- [ ] train/validation/final test 구분
- [ ] baseline 비교
- [ ] 지표를 목표값 규모와 함께 해석
- [ ] 대표 오류 사례 분석
- [ ] 모델 사용 가능성 판단
- [ ] 한계 작성
- [ ] 최종 Notebook URL 제출