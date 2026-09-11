# Titanic AI Data Analysis Practice

이 폴더는 **AI와 함께 Titanic 데이터 분석 한 사이클을 처음부터 끝까지 완주하는 학생용 실습 자료**를 담습니다.

핵심 원칙은 다음 한 문장입니다.

> 코드는 AI의 도움을 받아 최소한으로 작성하지만, 분석을 단계별로 진행하고 실제 결과를 보고 다음 행동을 결정하는 사람은 학생입니다.

## 실습 시작 순서

1. 이 저장소를 준비하고 VS Code에서 저장소 루트 폴더를 연다.
2. 사용할 Python 환경을 선택하고 터미널에서 `python --version`과 `python -c "import sys; print(sys.executable)"`로 확인한다.
3. 해당 환경에 `requirements.txt`의 패키지가 설치되어 있는지 확인한다. 설치가 필요하면 저장소 루트의 같은 터미널에서 `python -m pip install -r requirements.txt`를 직접 실행한다. Notebook은 자동 설치하지 않는다.
4. 아래 데이터 준비 명령을 실행한다.
5. VS Code에서 `notebooks/titanic_ai_analysis.ipynb`를 열고 오른쪽 위 Kernel에서 같은 Python 환경을 선택한다. Python Interpreter와 Notebook Kernel은 다를 수 있다.
6. STEP 01부터 순서대로 직접 실행하고 각 STEP 마지막의 빈 학생 작성 영역을 채운다. 커널 작업 경로는 저장소 루트 또는 `notebooks/`를 사용한다.

## 먼저 데이터 준비

저장소 루트에서 다음 명령을 한 번 실행합니다.

```powershell
python scripts/prepare_titanic_data.py
```

성공하면 다음 파일이 생성됩니다.

```text
data/titanic/train.csv
```

이번 실습은 강의안과 동일하게 **891행 × 12열 Titanic training set** 구조를 사용합니다.

```text
PassengerId, Survived, Pclass, Name, Sex, Age,
SibSp, Parch, Ticket, Fare, Cabin, Embarked
```

공개 저장소에는 CSV 자체를 커밋하지 않습니다. 준비 스크립트가 pandas 공식 저장소의 고정 commit에 있는 문서용 Titanic CSV를 다운로드한 뒤 891행 구조, 컬럼, PassengerId, Target 분포, 주요 결측치를 검증합니다.

자세한 출처·재배포 정책은 `../../data/titanic/SOURCE.md`를 확인합니다.

## 현재 파일

- `titanic_ai_analysis.md` : 학생용 전체 진행 가이드
- `titanic_ai_analysis_template.md` : 실행 결과와 개인 판단을 기록하는 Markdown 템플릿
- `../../notebooks/titanic_ai_analysis.ipynb` : STEP 00~17 실행 Notebook 골격
- `../../data/titanic/README.md` : 데이터 준비/검증 방법
- `../../data/titanic/SOURCE.md` : 출처·사용 정책
- `../../data/titanic/dataset_manifest.json` : 기계 판독 가능한 무결성 기준

## 진행 흐름

`STEP 00 전체 지도 → STEP 01 환경 → STEP 02 데이터 → STEP 03 품질 → STEP 04 Target → STEP 05 결측치 → STEP 06 컬럼 → STEP 07 인코딩 원리 → STEP 08 시각화 → STEP 09 EDA → STEP 10 Feature → STEP 11 split → STEP 12 Baseline Pipeline → STEP 13 평가/오류 → STEP 14 추가 모델 → STEP 15 최종 Pipeline → STEP 16 저장/새 입력 → STEP 17 Streamlit`

## 중요한 데이터 객체 계약

```text
df          = 891행 train.csv를 읽은 원본 기준 데이터
df_work     = STEP 5~10 탐색/EDA 작업본
df_encoded  = STEP 7 인코딩 원리 학습용 임시 데이터
model_source= STEP 11에서 df로 다시 만드는 모델링 기준 데이터
```

최종 모델링은 `model_source → X/y → train/test split → ColumnTransformer + Pipeline` 순서로 진행합니다. 전체 데이터에서 미리 학습한 중앙값, 최빈값, 범주 목록, scaling 기준을 test 데이터에 섞지 않습니다.

## 현재 상태

STEP 01~03은 실행 환경 확인, 데이터 로딩, 데이터 구조·품질 관찰 코드와 학생 작성 영역을 제공합니다. STEP 03에서 추가 품질 확인 항목 하나를 학생이 직접 선택합니다. STEP 04~17은 기존 주석 골격이며, 전체 셀이 실행되더라도 이후 분석·모델링까지 완료한 것은 아닙니다.
