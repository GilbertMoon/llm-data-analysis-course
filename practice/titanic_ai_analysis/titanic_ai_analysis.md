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
→ Train/Test 분리
→ 결측치 처리
→ 인코딩
→ 정규화/표준화
→ Baseline 분류
→ 오류 분석
→ 추가 모델 선택
→ 최종 모델 선정
→ 전처리 객체·모델 저장
→ 새로운 입력 예측
→ Streamlit 서비스
```

## 매 STEP의 공통 진행 방식

각 단계는 다음 순서로 진행합니다.

```text
1. 실행 계획 작성
2. AI에게 현재 STEP에 필요한 코드만 요청
3. 코드를 직접 실행
4. 실제 결과 확인
5. 결과 해석
6. 필요하면 추가 분석 후보 요청
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

STEP 00~04에서 전체 지도, 환경, 데이터 구조, 분석 문제와 `Survived` Target을 확인합니다. STEP 05에서 `df_work = df.copy()`를 한 번 만들고 STEP 10까지 탐색·EDA용으로 사용합니다.

STEP 07의 `df_encoded`는 One-Hot Encoding 원리를 눈으로 이해하기 위한 교육용 복사본입니다. 최종 모델 입력으로 사용하지 않습니다.

STEP 10에서는 Feature 후보를 다음 두 종류로 구분합니다.

```text
A. 행 단위 결정적 변환
- 한 행의 값만으로 같은 결과를 다시 만들 수 있음

B. 데이터에서 기준을 학습하는 변환
- 중앙값, 분위수, 빈도, 범주 목록처럼 데이터에서 기준을 배워야 함
```

이번 기본 실습에서는 `FamilySize`, `IsAlone`처럼 행 단위 결정적 Feature를 사용합니다.

## STEP 11~15: 모델링을 하나씩 직접 실행

STEP 11에서는 원본 `df`에서 `model_source`를 다시 만들고 **전처리보다 먼저 Train/Test를 분리**합니다.

```text
원본 df
→ FamilySize / IsAlone 직접 생성
→ X / y
→ Train/Test split
```

STEP 12에서는 전처리를 한꺼번에 묶지 않고 각각 직접 실행합니다.

```text
숫자형 결측치 처리
→ 범주형 결측치 처리
→ One-Hot Encoding
→ 정규화와 표준화 차이 확인
→ StandardScaler 표준화
→ 숫자형 + 범주형 결합
→ Logistic Regression 학습
```

### Train/Test 적용 원칙

```text
Train → fit_transform()
Test  → transform()
```

즉 Train에서만 다음 기준을 배웁니다.

```text
숫자형 중앙값
범주형 최빈값
One-Hot 범주 목록
StandardScaler 평균·표준편차
```

Test에는 Train에서 배운 기준을 그대로 적용합니다.

### 정규화와 표준화

```text
정규화 Normalization
대표 예: MinMaxScaler
→ 값을 보통 0~1 범위로 맞춤

표준화 Standardization
대표 예: StandardScaler
→ 평균 0, 표준편차 1을 기준으로 맞춤
```

이번 실습에서는 `MinMaxScaler` 결과를 개념 확인용으로 보고, 실제 Logistic Regression 입력에는 `StandardScaler` 표준화를 사용합니다.

STEP 13에서는 `baseline_model.predict(X_test_ready)` 결과로 Accuracy, Precision, Recall, F1, Confusion Matrix를 확인합니다.

STEP 14에서는 같은 `X_train_ready`, `X_test_ready`를 이용해 Random Forest 같은 추가 모델을 학습해 비교합니다.

STEP 15에서는 실제 결과를 보고 학생이 최종 모델을 직접 선택합니다.

## STEP 16~17: 저장과 서비스

최종 artifact는 다음 기준을 사용합니다.

```text
models/titanic_model_bundle.joblib
models/titanic_model_contract.json
```

`titanic_model_bundle.joblib`에는 한 개의 Pipeline이 아니라 다음 객체를 각각 저장합니다.

```text
numeric_imputer
categorical_imputer
encoder
scaler
model
```

새 승객도 학습 때와 같은 순서로 처리합니다.

```text
원본 입력
→ FamilySize / IsAlone
→ numeric_imputer.transform()
→ scaler.transform()
→ categorical_imputer.transform()
→ encoder.transform()
→ 숫자형 + 범주형 결합
→ model.predict()
```

앱에서는 중앙값, 최빈값, 범주 목록, scaling 기준을 다시 `fit()`하지 않습니다.

예측 확률은 `classes_`를 확인해 `Survived=1`의 위치를 찾습니다.

## 개인 판단

이 과정에서는 여러 지점에서 AI에게 후보를 요청한 뒤 학생이 직접 선택합니다. 모든 학생의 결측 처리, 추가 EDA, Feature, 추가 모델이 같을 필요는 없습니다. 중요한 것은 **실제 결과와 선택 이유가 연결되어 있는가**입니다.

## 제출 전 자기 점검

- 모든 핵심 코드 셀을 직접 실행했는가?
- 실행하지 않은 결과를 AI가 작성하지 않았는가?
- 관찰과 해석을 구분했는가?
- STEP 11에서 전처리보다 먼저 Train/Test를 분리했는가?
- Train에는 `fit_transform()`, Test에는 `transform()`을 사용했는가?
- 정규화와 표준화의 차이를 설명할 수 있는가?
- One-Hot Encoding 결과를 직접 확인했는가?
- StandardScaler 적용 결과를 직접 확인했는가?
- 최종 모델을 직접 선택했는가?
- 저장한 전처리 객체와 모델을 새 입력에도 같은 순서로 적용했는가?

현재 이 문서는 **전체 실행 규칙을 고정하는 학생용 기준 문서**입니다. 실제 코드는 `notebooks/titanic_ai_analysis.ipynb`에서 셀별로 실행합니다.
