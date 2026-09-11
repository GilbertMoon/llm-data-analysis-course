# Titanic AI Data Analysis Practice

이 폴더는 **AI와 함께 Titanic 데이터 분석 한 사이클을 처음부터 끝까지 완주하는 학생용 실습 자료**를 담습니다.

핵심 원칙은 다음 한 문장입니다.

> 코드는 AI의 도움을 받아 최소한으로 작성하지만, 분석을 단계별로 진행하고 실제 결과를 보고 다음 행동을 결정하는 사람은 학생입니다.

## 현재 파일

- `titanic_ai_analysis.md` : 학생용 전체 진행 가이드
- `titanic_ai_analysis_template.md` : 실행 결과와 개인 판단을 기록하는 Markdown 템플릿
- `../../notebooks/titanic_ai_analysis.ipynb` : STEP 00~17 실행 Notebook 골격
- `../../data/titanic/README.md` : Titanic 데이터 배치 기준

## 진행 흐름

`STEP 00 전체 지도 → STEP 01 환경 → STEP 02 데이터 → STEP 03 품질 → STEP 04 Target → STEP 05 결측치 → STEP 06 컬럼 → STEP 07 인코딩 원리 → STEP 08 시각화 → STEP 09 EDA → STEP 10 Feature → STEP 11 split → STEP 12 Baseline Pipeline → STEP 13 평가/오류 → STEP 14 추가 모델 → STEP 15 최종 Pipeline → STEP 16 저장/새 입력 → STEP 17 Streamlit`

## 중요한 데이터 객체 계약

```text
df          = 원본 기준 데이터
df_work     = STEP 5~10 탐색/EDA 작업본
df_encoded  = STEP 7 인코딩 원리 학습용 임시 데이터
model_source= STEP 11에서 원본 df로 다시 만드는 모델링 기준 데이터
```

최종 모델링은 `model_source → X/y → train/test split → ColumnTransformer + Pipeline` 순서로 진행합니다. 전체 데이터에서 미리 학습한 중앙값, 최빈값, 범주 목록, scaling 기준을 test 데이터에 섞지 않습니다.

## 현재 상태

이 커밋은 **학생용 실행 구조와 Notebook 골격을 먼저 만드는 단계**입니다. `data/titanic/train.csv`, 완성 코드, Streamlit 앱, 모델 artifact는 아직 포함하지 않습니다. 검증된 데이터 파일과 단계별 코드는 이후 작업에서 순차적으로 추가합니다.
