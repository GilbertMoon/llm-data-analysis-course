# Titanic dataset source and license

이 실습은 Kaggle 경쟁용 `train.csv`를 그대로 재배포하지 않고, **OpenML Titanic dataset 40945**를 기준 데이터로 사용합니다.

## 선택 이유

Kaggle의 `Titanic - Machine Learning from Disaster` 데이터 페이지는 데이터 라이선스를 **`Subject to Competition Rules`**로 표시합니다. 따라서 수업용 공개 저장소에서 Kaggle 파일을 임의로 복제·재배포하는 방식 대신, 재사용 조건이 명시된 OpenML 버전을 사용합니다.

OpenML dataset 40945는 MLCommons Croissant 메타데이터에서도 Titanic 데이터셋으로 기술되어 있으며, 메타데이터의 라이선스 값은 **`AFL-3.0` (Academic Free License v3.0)** 입니다.

AFL-3.0은 원본 저작물의 복제, 수정/변환, 배포를 허용하는 조항을 포함합니다. 실제 사용 시에는 라이선스 전체 조건을 확인해야 합니다.

## 출처

- Dataset: Titanic
- OpenML dataset ID: `40945`
- OpenML page: https://www.openml.org/d/40945
- 원 데이터 저자 표기: Frank E. Harrell Jr., Thomas Cason
- 원 출처 표기: Vanderbilt Biostatistics
- MLCommons Croissant metadata: https://github.com/mlcommons/croissant/blob/main/datasets/1.0/titanic/metadata.json
- 검증에 사용하는 raw CSV mirror: https://raw.githubusercontent.com/mlcommons/croissant/main/datasets/1.0/titanic/data/titanic.csv
- Croissant metadata version: `1.0.0`
- License: `AFL-3.0`
- SPDX license page: https://spdx.org/licenses/AFL-3.0

## 원본 무결성 기준

MLCommons Croissant metadata에 기록된 원본 CSV 정보:

```text
content size: 117743 bytes
sha256: c617db2c7470716250f6f001be51304c76bcc8815527ab8bae734bdca0735737
```

`scripts/prepare_titanic_data.py`는 다운로드 직후 이 SHA-256을 확인합니다. 값이 다르면 변환을 중단합니다.

## 수업용 `train.csv` 변환 규칙

원본은 1309행 × 14열입니다.

수업용 파일은 다음 11개 컬럼을 유지합니다.

```text
Pclass
Survived
Name
Sex
Age
SibSp
Parch
Ticket
Fare
Cabin
Embarked
```

원본 컬럼명은 강의안과 맞게 대소문자만 정규화합니다.

제외 컬럼:

```text
boat
body
home.dest
```

- `boat`, `body`: 생존 결과 이후에 알게 되는 정보가 포함되어 있어 예측 Feature로 사용하면 명백한 누수 위험이 있습니다.
- `home.dest`: 이번 입문 실습의 핵심 범위를 줄이기 위해 제외합니다.

`PassengerId`는 OpenML 40945 원본에 없으므로 임의로 생성하지 않습니다.

생성되는 `data/titanic/train.csv`는 **Kaggle competition의 891행 `train.csv`와 같은 파일이 아닙니다.** 이 수업에서는 1309명의 labeled 데이터를 가지고 STEP 11에서 직접 train/test split을 수행합니다.

## 예상 검증 결과

```text
prepared shape: (1309, 11)
Target: Survived
Survived missing: 0
Survived allowed values: 0, 1
Age missing: 263
Fare missing: 1
Cabin missing: 1014
Embarked missing: 2
```

실제 Notebook에서는 학생이 직접 실행한 결과를 기준으로 분석하며, 위 숫자를 실행 결과처럼 복사해 제출하지 않습니다.
