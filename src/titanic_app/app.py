from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from features import MODEL_FEATURE_COLUMNS, build_model_features


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "titanic_final_pipeline.joblib"
CONTRACT_PATH = PROJECT_ROOT / "models" / "titanic_model_contract.json"


@st.cache_resource
def load_artifacts():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"모델 파일이 없습니다: {MODEL_PATH}\n"
            "Notebook STEP 16을 먼저 실행해 최종 Pipeline을 저장하세요."
        )

    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(
            f"Contract 파일이 없습니다: {CONTRACT_PATH}\n"
            "Notebook STEP 16을 먼저 실행하세요."
        )

    pipeline = joblib.load(MODEL_PATH)
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return pipeline, contract


def positive_class_probability(
    pipeline,
    frame: pd.DataFrame,
    positive_class: int = 1,
) -> float:
    estimator = pipeline.named_steps["model"]
    positions = np.where(estimator.classes_ == positive_class)[0]
    if len(positions) != 1:
        raise ValueError(
            f"positive class {positive_class} not found in {estimator.classes_}"
        )

    return float(pipeline.predict_proba(frame)[:, positions[0]][0])


st.set_page_config(
    page_title="Titanic Survival Prediction",
    page_icon="🚢",
    layout="centered",
)

st.title("🚢 Titanic 생존 예측")
st.caption(
    "이 앱은 수업에서 직접 학습하고 저장한 Pipeline을 사용합니다. "
    "예측 결과는 실제 생존 가능성을 보장하지 않습니다."
)

try:
    pipeline, contract = load_artifacts()
except Exception as exc:
    st.error(str(exc))
    st.stop()

with st.form("passenger_form"):
    pclass = st.selectbox("객실 등급 (Pclass)", [1, 2, 3], index=2)
    sex = st.selectbox("성별 (Sex)", ["female", "male"], index=1)
    age = st.number_input(
        "나이 (Age)",
        min_value=0.0,
        max_value=100.0,
        value=30.0,
        step=1.0,
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
    fare = st.number_input(
        "운임 (Fare)",
        min_value=0.0,
        value=10.0,
        step=1.0,
    )
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
        feature_frame = build_model_features(raw_input)

        contract_columns = contract.get("model_feature_columns", [])
        if contract_columns != MODEL_FEATURE_COLUMNS:
            raise ValueError(
                "현재 app의 Feature 목록과 저장된 Model Input Contract가 다릅니다. "
                "Notebook STEP 16과 src/titanic_app/features.py를 다시 확인하세요."
            )

        model_input = feature_frame[contract_columns]

        predicted_class = int(pipeline.predict(model_input)[0])
        probability = positive_class_probability(
            pipeline,
            model_input,
            positive_class=int(contract.get("positive_class", 1)),
        )

        if predicted_class == 1:
            st.success("모델 예측: 생존")
        else:
            st.warning("모델 예측: 비생존")

        st.metric("생존 확률(모델 출력)", f"{probability:.1%}")

        with st.expander("모델에 전달된 Feature 확인"):
            st.dataframe(model_input, use_container_width=True)

        st.info(
            "이 값은 수업용 Titanic 데이터와 선택한 Feature/모델을 기반으로 한 "
            "예측 결과입니다. 실제 인과관계나 개인의 실제 생존 가능성을 의미하지 않습니다."
        )

    except Exception as exc:
        st.error(f"예측 처리 중 오류가 발생했습니다: {exc}")
