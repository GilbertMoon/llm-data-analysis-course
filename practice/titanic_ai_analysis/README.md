# Titanic AI Data Analysis Practice

이 폴더는 **AI와 함께 Titanic 데이터 분석 한 사이클을 처음부터 끝까지 완주하는 학생용 실습 자료**를 담습니다.

핵심 원칙은 다음 한 문장입니다.

> 코드는 AI의 도움을 받아 최소한으로 작성하지만, 분석을 단계별로 진행하고 실제 결과를 보고 다음 행동을 결정하는 사람은 학생입니다.

## 실습 시작 순서

1. 이 저장소를 준비하고 VS Code에서 저장소 루트 폴더를 연다.
2. 사용할 Python 환경을 선택하고 터미널에서 `python --version`과 `python -c "import sys; print(sys.executable)"`로 확인한다.
3. 필요한 경우 `python -m pip install -r requirements.txt`를 실행한다.
4. 아래 데이터 준비 명령을 실행한다.
5. `notebooks/titanic_ai_analysis.ipynb`를 열고 같은 Python 환경을 Kernel로 선택한다.
6. STEP 01부터 순서대로 셀을 직접 실행한다.

## 먼저 데이터 준비

저장소 루트에서 실행합니다.

```powershell
python scripts/prepare_titanic_data.py
```

성공하면 다음 파일이 생성됩니다.

```text
data/titanic/train.csv
```

이번 실습은 891행 × 12열 Titanic training set 구조를 사용합니다.

```text
PassengerId, Survived, Pclass, Name, Sex, Age,
SibSp, Parch, Ticket, Fare, Cabin, Embarked
```

자세한 출처·재배포 정책은 `../../data/titanic/SOURCE.md`를 확인합니다.

## 현재 파일

- `titanic_ai_analysis.md` : 학생용 전체 진행 가이드
- `titanic_ai_analysis_template.md` : 실행 결과와 개인 판단 기록 Template
- `../../notebooks/titanic_ai_analysis.ipynb` : STEP 00~17 주 실행 Notebook
- `../../src/titanic_app/app.py` : STEP 17 Streamlit 예측 앱
- `../../src/titanic_app/features.py` : 이후 함수/모듈 리팩터링 참고 파일
- `../../scripts/titanic_modeling_smoke_test.py` : STEP 11~16 모델링 실행 검증
- `../../scripts/validate_titanic_public_release.py` : 데이터·Notebook·artifact·Streamlit 통합 자동 QA

## 진행 흐름

```text
STEP 00 전체 지도
→ STEP 01 환경
→ STEP 02 데이터
→ STEP 03 품질
→ STEP 04 Target
→ STEP 05 결측치 원리
→ STEP 06 컬럼
→ STEP 07 인코딩 원리
→ STEP 08 시각화
→ STEP 09 EDA/통계
→ STEP 10 Feature
→ STEP 11 Train/Test split
→ STEP 12 결측치 처리
   → One-Hot Encoding
   → 정규화/표준화 비교
   → StandardScaler 표준화
   → 데이터 결합
   → Logistic Regression
→ STEP 13 평가/오류
→ STEP 14 추가 모델
→ STEP 15 최종 모델 선택
→ STEP 16 전처리 객체·모델 저장/새 입력
→ STEP 17 Streamlit
```

## 중요한 데이터 객체 계약

```text
df           = train.csv를 읽은 원본 기준 데이터
df_work      = STEP 5~10 탐색/EDA 작업본
df_encoded   = STEP 7 인코딩 원리 학습용 임시 데이터
feature_demo = STEP 10 파생 Feature 실험용 데이터
model_source = STEP 11에서 df로 다시 만드는 모델링 기준 데이터
```

최종 모델링은 다음 순서로 진행합니다.

```text
model_source
→ X / y
→ train / test split
→ Train에서 숫자형 중앙값 학습
→ Train에서 범주형 최빈값 학습
→ Train에서 OneHotEncoder 범주 학습
→ 정규화와 표준화 차이 확인
→ Train에서 StandardScaler 평균/표준편차 학습
→ 숫자형 + 범주형 데이터 결합
→ 모델 fit
```

### 정규화와 표준화

이번 수업에서는 두 개념을 구분합니다.

```text
정규화 Normalization
대표 예: MinMaxScaler
→ 값을 보통 0~1 범위로 맞춤

표준화 Standardization
대표 예: StandardScaler
→ 평균 0, 표준편차 1을 기준으로 맞춤
```

`MinMaxScaler`는 개념 확인용으로 실행하고, 기본 Logistic Regression에는 `StandardScaler` 표준화를 사용합니다.

가장 중요한 원칙은 다음입니다.

```text
Train → fit_transform()
Test  → transform()
```

Test 데이터로 중앙값, 최빈값, 범주 목록, 평균, 표준편차를 다시 학습하지 않습니다.

## 기본 Model Input Contract

```text
raw input:
Pclass, Sex, Age, SibSp, Parch, Fare, Embarked

fixed derived feature:
FamilySize = SibSp + Parch + 1
IsAlone = 1 if FamilySize == 1 else 0

learned preprocessing objects:
numeric_imputer
categorical_imputer
encoder
scaler
model
```

## STEP 16 저장 artifact

```text
models/titanic_model_bundle.joblib
models/titanic_model_contract.json
```

`titanic_model_bundle.joblib`은 한 개의 sklearn Pipeline이 아니라 다음 객체를 묶어 저장합니다.

```text
numeric_imputer
categorical_imputer
encoder
scaler
model
```

새 승객도 학습 때와 같은 순서로 각각 `transform()`한 뒤 모델에 전달합니다.

## 전체 자동 QA

저장소 루트에서 다음 명령으로 데이터 준비, 모델링 smoke test, Notebook 순차 실행, artifact 검증, Streamlit 실행 검증을 수행합니다.

```powershell
python scripts/validate_titanic_public_release.py
```

검증 항목:

```text
Titanic 데이터 준비/무결성
모델링 smoke test
Notebook nbformat / clean-state
Notebook Code Cell 순차 실행
split-first 확인
단계별 결측치 처리 / 인코딩 / 표준화 실행
model bundle 저장/재로드
Model Input Contract
새 승객 predict / predict_proba
Streamlit form submit / prediction result
Streamlit headless health
```

## STEP 17 Streamlit

STEP 16에서 artifact를 만든 뒤 실행합니다.

```powershell
streamlit run src/titanic_app/app.py
```

앱은 저장된 전처리 객체와 모델을 학습 때와 같은 순서로 사용합니다. 앱에서 중앙값·최빈값·범주 목록·scaling 기준을 다시 `fit()`하지 않습니다.

자동 QA에서 출력되는 정확도·확률 등의 숫자는 수업 답안이 아닙니다. 학생은 자신의 Notebook을 직접 실행한 결과를 관찰하고 기록해야 합니다.
