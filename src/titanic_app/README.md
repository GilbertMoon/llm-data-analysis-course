# Titanic Streamlit app

이 폴더는 STEP 17에서 사용할 Titanic 예측 앱과 Notebook이 공유하는 결정적 Feature 규칙을 담습니다.

현재 구조:

```text
src/titanic_app/
├─ app.py
└─ features.py
```

## `features.py`

Notebook STEP 11 이후와 Streamlit이 같은 규칙을 사용합니다.

```text
raw input:
Pclass, Sex, Age, SibSp, Parch, Fare, Embarked

fixed derived feature:
FamilySize = SibSp + Parch + 1
IsAlone = 1 if FamilySize == 1 else 0
```

여기에는 전체 데이터의 평균·중앙값·빈도·Target을 학습해야 하는 변환을 넣지 않습니다. 그런 학습형 전처리는 저장된 scikit-learn Pipeline이 담당합니다.

## `app.py`

앱의 최종 예측 흐름은 다음으로 고정합니다.

```text
사용자 원본 입력
→ 입력 검증
→ build_model_features()
→ Model Input Contract 컬럼 확인
→ 저장된 final_pipeline.predict()
→ estimator.classes_에서 class 1 위치 확인
→ predict_proba()
→ 결과와 한계 표시
```

앱에서 median/mode를 새로 계산하거나 `pd.get_dummies()`를 별도로 실행하거나 scaler를 다시 fit하지 않습니다.

## 실행 전 준비

Notebook STEP 16 또는 개발 검증 스크립트로 다음 artifact가 있어야 합니다.

```text
models/titanic_final_pipeline.joblib
models/titanic_model_contract.json
```

개발 검증용 Baseline artifact가 필요한 경우 저장소 루트에서 실행할 수 있습니다.

```powershell
python scripts/titanic_modeling_smoke_test.py --save-artifacts
```

정식 수업 흐름에서는 학생이 STEP 15에서 최종 모델을 직접 선택한 뒤 STEP 16에서 artifact를 저장합니다.

## Streamlit 실행

```powershell
streamlit run src/titanic_app/app.py
```

`requirements.txt`에는 `joblib`, `streamlit`을 명시적으로 포함합니다.
