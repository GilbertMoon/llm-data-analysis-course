from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parents[1]
BUNDLE_PATH = PROJECT_ROOT / "models" / "titanic_model_bundle.joblib"
CONTRACT_PATH = PROJECT_ROOT / "models" / "titanic_model_contract.json"


@st.cache_resource
def load_artifacts():
    if not BUNDLE_PATH.is_file():
        raise FileNotFoundError(
            f"모델 파일이 없습니다: {BUNDLE_PATH}\n"
            "Notebook STEP 16을 먼저 실행해 전처리 객체와 모델을 저장하세요."
        )

    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(
            f"Contract 파일이 없습니다: {CONTRACT_PATH}\n"
            "Notebook STEP 16을 먼저 실행하세요."
        )

    bundle = joblib.load(BUNDLE_PATH)
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return bundle, contract


def prepare_model_input(
    raw_input: pd.DataFrame,
    bundle: dict,
    contract: dict,
) -> pd.DataFrame:
    """Notebook에서 학습한 순서를 그대로 새 입력에 적용한다."""
    frame = raw_input.copy()

    # STEP 10/11에서 직접 만든 결정적 파생 Feature와 같은 규칙
    frame["FamilySize"] = frame["SibSp"] + frame["Parch"] + 1
    frame["IsAlone"] = (frame["FamilySize"] == 1).astype(int)

    numeric_features = contract["numeric_features"]
    categorical_features = contract["categorical_features"]

    numeric_imputed = bundle["numeric_imputer"].transform(frame[numeric_features])
    numeric_scaled = bundle["scaler"].transform(numeric_imputed)

    categorical_imputed = bundle["categorical_imputer"].transform(
        frame[categorical_features]
    )
    categorical_encoded = bundle["encoder"].transform(categorical_imputed)

    prepared_array = np.hstack([numeric_scaled, categorical_encoded])
    prepared_columns = contract["prepared_feature_columns"]

    return pd.DataFrame(prepared_array, columns=prepared_columns, index=frame.index)


st.set_page_config(
    page_title="Titanic Survival Prediction",
    page_icon="🚢",
    layout="centered",
)

st.title("🚢 Titanic 생존 예측")
st.caption(
    "이 앱은 수업에서 따로 학습한 결측치 처리, 인코딩, 표준화 객체와 모델을 "
    "같은 순서로 적용합니다. 예측 결과는 실제 생존 가능성을 보장하지 않습니다."
)

try:
    bundle, contract = load_artifacts()
except Exception as exc:
    st.error(str(exc))
    st.stop()

with st.form("passenger_form"):
    pclass = st.selectbox("객실 등급 (Pclass)", [1, 2, 3], index=2)
    sex = st.selectbox("성별 (Sex)", ["female", "male"], index=1)
    age = st.number_input(
        "나이 (Age)", min_value=0.0, max_value=100.0, value=30.0, step=1.0
    )
    sibsp = st.number_input(
        "함께 탑승한 형제·배우자 수 (SibSp)",
        min_value=0,
        max_value=10,
        value=0,
        step=1,
    )
    parch = st.number_input(
        "함께 탑승한 부모·자녀 수 (Parch)",
        min_value=0,
        max_value=10,
        value=0,
        step=1,
    )
    fare = st.number_input("운임 (Fare)", min_value=0.0, value=10.0, step=1.0)
    embarked = st.selectbox("탑승 항구 (Embarked)", ["S", "C", "Q"], index=0)

    submitted = st.form_submit_button("예측하기")

if submitted:
    raw_input = pd.DataFrame(
        [
            {
                "Pclass": pclass,
                "Sex": sex,
                "Age": age,
                "SibSp": sibsp,
                "Parch": parch,
                "Fare": fare,
                "Embarked": embarked,
            }
        ]
    )

    try:
        model_input = prepare_model_input(raw_input, bundle, contract)
        model = bundle["model"]

        predicted_class = int(model.predict(model_input)[0])
        classes = list(model.classes_)
        positive_class = int(contract.get("positive_class", 1))
        positive_index = classes.index(positive_class)
        probability = float(model.predict_proba(model_input)[0][positive_index])

        if predicted_class == 1:
            st.success("모델 예측: 생존")
        else:
            st.warning("모델 예측: 비생존")

        st.metric("생존 확률(모델 출력)", f"{probability:.1%}")

        with st.expander("모델에 전달된 최종 숫자 데이터 확인"):
            st.dataframe(model_input, width="stretch")

        st.info(
            "이 값은 수업용 Titanic 데이터와 선택한 전처리/모델을 기반으로 한 "
            "예측 결과입니다. 실제 인과관계나 개인의 실제 생존 가능성을 의미하지 않습니다."
        )

    except Exception as exc:
        st.error(f"예측 처리 중 오류가 발생했습니다: {exc}")
