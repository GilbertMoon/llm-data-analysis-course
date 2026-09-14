# Titanic Streamlit app

이 폴더는 STEP 17에서 사용할 Titanic 예측 앱을 담습니다.

현재 구조:

```text
src/titanic_app/
├─ app.py
└─ features.py
```

## 수업 기준

Notebook에서는 핵심 전처리 로직을 별도 모듈에 숨기지 않습니다. 학생이 다음 작업을 각각 직접 실행합니다.

```text
FamilySize / IsAlone 생성
→ 숫자형 결측치 처리
→ 범주형 결측치 처리
→ One-Hot Encoding
→ StandardScaler 표준화
→ 숫자형 + 범주형 결합
→ 모델 예측
```

`features.py`는 이후 실무에서 반복 코드를 함수/모듈로 정리하는 방법을 보여주기 위해 남겨 둔 참고 파일이며, 현재 학생용 Notebook과 `app.py`의 필수 의존성이 아닙니다.

## `app.py`

앱은 Notebook STEP 16에서 저장한 객체를 각각 불러와 **학습 때와 같은 순서**로 적용합니다.

```text
사용자 원본 입력
→ FamilySize / IsAlone 직접 생성
→ numeric_imputer.transform()
→ scaler.transform()
→ categorical_imputer.transform()
→ encoder.transform()
→ 숫자형 + 범주형 결합
→ model.predict()
→ model.predict_proba()
→ 결과와 한계 표시
```

앱에서는 중앙값·최빈값·범주 목록·평균·표준편차를 새로 학습하지 않습니다. Notebook의 Train 데이터에서 학습해 저장한 객체를 그대로 사용합니다.

## 실행 전 준비

Notebook STEP 16 또는 개발 검증 스크립트로 다음 artifact가 있어야 합니다.

```text
models/titanic_model_bundle.joblib
models/titanic_model_contract.json
```

`titanic_model_bundle.joblib`에는 다음 객체가 각각 저장됩니다.

```text
numeric_imputer
categorical_imputer
encoder
scaler
model
```

개발 검증용 artifact가 필요한 경우 저장소 루트에서 실행합니다.

```powershell
python scripts/titanic_modeling_smoke_test.py --save-artifacts
```

정식 수업 흐름에서는 학생이 STEP 15에서 최종 모델을 직접 선택한 뒤 STEP 16에서 artifact를 저장합니다.

## Streamlit 실행

```powershell
streamlit run src/titanic_app/app.py
```

`requirements.txt`에는 `joblib`, `streamlit`을 명시적으로 포함합니다.
