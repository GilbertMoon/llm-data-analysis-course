# Titanic AI Data Analysis Practice

이 폴더는 **AI와 함께 Titanic 데이터 분석 한 사이클을 처음부터 끝까지 완주하는 학생용 실습 자료**를 담습니다.

핵심 원칙은 다음 한 문장입니다.

> 코드는 AI의 도움을 받아 최소한으로 작성하지만, 분석을 단계별로 진행하고 실제 결과를 보고 다음 행동을 결정하는 사람은 학생입니다.

## 먼저 데이터 준비

저장소 루트에서 다음 명령을 한 번 실행합니다.

```powershell
python scripts/prepare_titanic_data.py
```

성공하면 다음 파일이 생성됩니다.

```text
data/titanic/train.csv
```

이 파일은 Kaggle competition의 891행 `train.csv`를 복제한 것이 아닙니다. 재사용 조건이 명시된 **OpenML Titanic dataset 40945**를 검증·정규화한 1309행 수업용 데이터입니다. 자세한 출처와 라이선스는 `../../data/titanic/SOURCE.md`를 확인합니다.

## 현재 파일

- `titanic_ai_analysis.md` : 학생용 전체 진행 가이드
- `titanic_ai_analysis_template.md` : 실행 결과와 개인 판단을 기록하는 Markdown 템플릿
- `../../notebooks/titanic_ai_analysis.ipynb` : STEP 00~17 실행 Notebook 골격
- `../../data/titanic/README.md` : 데이터 준비/검증 방법
- `../../data/titanic/SOURCE.md` : 출처·라이선스·변환 기준
- `../../data/titanic/dataset_manifest.json` : 기계 판독 가능한 무결성 기준

## 진행 흐름

`STEP 00 전체 지도 → STEP 01 환경 → STEP 02 데이터 → STEP 03 품질 → STEP 04 Target → STEP 05 결측치 → STEP 06 컬럼 → STEP 07 인코딩 원리 → STEP 08 시각화 → STEP 09 EDA → STEP 10 Feature → STEP 11 split → STEP 12 Baseline Pipeline → STEP 13 평가/오류 → STEP 14 추가 모델 → STEP 15 최종 Pipeline → STEP 16 저장/새 입력 → STEP 17 Streamlit`

## 중요한 데이터 객체 계약

```text
df          = 수업용 train.csv를 읽은 원본 기준 데이터
df_work     = STEP 5~10 탐색/EDA 작업본
df_encoded  = STEP 7 인코딩 원리 학습용 임시 데이터
model_source= STEP 11에서 df로 다시 만드는 모델링 기준 데이터
```

최종 모델링은 `model_source → X/y → train/test split → ColumnTransformer + Pipeline` 순서로 진행합니다. 전체 데이터에서 미리 학습한 중앙값, 최빈값, 범주 목록, scaling 기준을 test 데이터에 섞지 않습니다.

## 현재 상태

학생용 전체 실행 구조, 데이터 준비/검증 경로, Notebook 골격까지 준비되어 있습니다. Notebook의 단계별 완성 코드는 아직 채우지 않았으며, 다음 작업부터 STEP 01~03을 실제 실행 가능한 형태로 보강합니다.
