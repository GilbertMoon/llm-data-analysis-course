# Titanic Streamlit app

이 폴더는 STEP 17에서 사용할 Streamlit 예측 앱을 위한 위치입니다.

예정 구조:

```text
src/titanic_app/
├─ app.py
└─ features.py   # 결정적 파생 Feature가 있을 때만
```

앱의 최종 예측 흐름은 다음으로 고정합니다.

```text
사용자 원본 입력
→ 입력 검증
→ 필요한 결정적 파생 Feature 생성
→ 저장된 final_pipeline.predict()
→ classes_ 확인
→ predict_proba()
→ 결과 표시
```

앱에서 median/mode를 새로 계산하거나 `pd.get_dummies()`를 별도로 실행하거나 scaler를 다시 fit하지 않습니다. 학습형 전처리는 저장된 Pipeline이 담당합니다.

`app.py`와 `features.py`는 최종 Model Input Contract가 확정된 뒤 생성합니다.
