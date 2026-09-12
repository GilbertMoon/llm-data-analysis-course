# AI와 함께 타이타닉 데이터 분석 한 사이클 완주하기

## 학습 목표

이 실습의 목표는 코드를 많이 작성하는 것이 아니라 **데이터 분석의 전체 흐름을 직접 실행하고, 실제 결과를 보고 다음 행동을 판단하는 경험**을 만드는 것입니다.

```text
데이터 확보
→ 데이터 이해
→ 전처리 판단
→ 시각화
→ EDA
→ Feature 설계
→ train/test 분리
→ Baseline 분류
→ 오류 분석
→ 추가 모델 선택
→ 최종 모델 선정
→ 모델 저장
→ 새로운 입력 예측
→ Streamlit 서비스
```

## 매 STEP의 공통 진행 방식

각 단계는 반드시 다음 순서로 진행합니다.

```text
1. 실행 계획 작성
2. AI에게 현재 STEP에 필요한 코드만 요청
3. 코드를 직접 실행
4. 실행 결과 요약
5. 실행 결과 분석
6. 추가 분석 후보가 필요하면 AI에게 후보 요청
7. 학생이 진행 여부를 판단
```

AI에게 Notebook 전체를 한 번에 완성시키거나 실제 실행하지 않은 결과를 작성하게 하지 않습니다.

## 결과 작성 기준

학생의 Markdown에는 다음을 구분합니다.

```text
관찰   = 실제 출력이나 그래프에서 직접 확인한 사실
해석   = 그 사실이 의미할 수 있는 판단
가설   = 아직 검증되지 않은 가능한 설명
한계   = 현재 결과만으로 알 수 없는 것
```

`차이가 보인다`와 `원인이다`는 다릅니다. 그룹별 차이나 상관을 바로 인과관계로 표현하지 않습니다.

## STEP 00~10: 탐색과 판단

STEP 00~04에서 전체 지도, 환경, 데이터 구조, 분석 문제와 `Survived` Target을 확인합니다. STEP 05에서 `df_work = df.copy()`를 **한 번만** 만들고 STEP 10까지 이어서 사용합니다.

STEP 07의 `df_encoded`는 One-hot Encoding 같은 변환의 원리를 눈으로 이해하기 위한 교육용 복사본입니다. 최종 모델 입력으로 사용하지 않습니다. STEP 08~09의 시각화와 EDA는 사람이 의미를 읽기 쉬운 `df_work`를 기본으로 사용합니다. STEP 08은 barplot과 boxplot을 이용해 비율과 분포를 비교하고, STEP 09는 요약 통계와 간단한 통계검정으로 관찰된 차이를 추가 확인합니다.

STEP 10에서는 Feature 후보를 다음 두 종류로 구분합니다.

```text
A. 행 단위 결정적 변환
- 한 행의 값만으로 같은 결과를 다시 만들 수 있음

B. 데이터에서 기준을 학습하는 변환
- 중앙값, 분위수, 빈도, 범주 목록처럼 데이터 전체/부분에서 기준을 배워야 함
```

B 유형의 규칙은 최종 모델 평가에서 train 범위 안에서 학습해야 합니다.

## STEP 11~15: 누수 없는 모델 비교

STEP 11에서는 탐색용 `df_work`나 `df_encoded`를 그대로 모델 평가에 사용하지 않고 원본 `df`에서 `model_source`를 다시 만듭니다. 학생이 확정한 재현 가능한 결정적 Feature만 동일 규칙으로 추가한 뒤 `X`와 `y`를 만들고 **전처리보다 먼저 train/test를 분리**합니다.

STEP 12의 Baseline은 단순 estimator 하나가 아니라 다음 Pipeline을 기준으로 합니다.

```text
X_train
→ numeric: imputer → scaler
→ categorical: imputer → OneHotEncoder(handle_unknown="ignore")
→ LogisticRegression
```

Pipeline 전체를 `X_train, y_train`에 fit합니다. `X_test`에서 median/mode/category/scaler 기준을 새로 학습하지 않습니다.

STEP 14의 추가 모델도 같은 데이터 분할과 같은 전처리 계약을 사용하고 estimator만 바꿉니다. STEP 15에서는 train-only Cross Validation을 추가 근거로 사용하고 최종 객체를 `final_pipeline`으로 확정합니다.

## STEP 16~17: 저장과 서비스

최종 artifact 이름은 다음 기준을 사용합니다.

```text
models/titanic_final_pipeline.joblib
models/titanic_model_contract.json
```

`final_pipeline`은 전처리와 분류 모델을 함께 포함해야 합니다. 새로운 승객 또는 Streamlit 앱에서 `pd.get_dummies()`, median 계산, scaler fit을 다시 만들지 않습니다.

결정적 파생 Feature가 필요하다면 Notebook과 Streamlit이 **같은 함수 구현**을 공유하도록 합니다.

예측 확률은 배열의 두 번째 열을 무조건 `Survived=1`이라고 가정하지 않고 `classes_`를 확인해 positive class 위치를 찾습니다.

## 개인 판단

이 과정에서는 여러 지점에서 AI에게 후보를 요청한 뒤 학생이 직접 선택합니다. 모든 학생의 결측 처리, 추가 EDA, Feature, 추가 모델이 같을 필요는 없습니다. 중요한 것은 **실제 결과와 선택 이유가 연결되어 있는가**입니다.

## 제출 전 자기 점검

- 모든 핵심 코드 셀을 직접 실행했는가?
- 출력이 필요한 셀에 실제 출력이 남아 있는가?
- 실행하지 않은 결과를 AI가 작성하지 않았는가?
- 관찰과 해석을 구분했는가?
- 최소 5개 이상의 개인 판단 또는 추가 분석 흔적이 있는가?
- STEP 11 이후 학습형 전처리가 train 범위 안에서 fit되는가?
- 최종 Pipeline 저장 전/후 예측이 일치하는가?
- Streamlit이 저장된 Pipeline과 같은 입력 계약을 사용하는가?

현재 이 문서는 **전체 실행 규칙을 고정하는 학생용 기준 문서**입니다. 각 STEP의 상세 코드와 프롬프트는 이후 순차적으로 보강합니다.
