# Titanic data

이 폴더는 Titanic AI 분석 실습용 데이터를 준비하는 위치입니다.

생성 경로:

```text
data/titanic/train.csv
```

## 데이터 준비 방법

저장소 루트에서 다음 명령을 실행합니다.

```powershell
python scripts/prepare_titanic_data.py
```

성공하면 `data/titanic/train.csv`가 생성됩니다.

스크립트는 다음 순서로 동작합니다.

```text
고정된 공개 원본 URL에서 다운로드
→ 891행 × 12열 확인
→ 컬럼 이름/순서 확인
→ PassengerId 1~891 및 중복 여부 확인
→ Survived 값/분포 확인
→ 주요 결측치 개수 확인
→ data/titanic/train.csv 저장
→ 저장 파일 재로딩 검증
```

이미 정상 파일이 있으면 다시 다운로드하지 않습니다. 강제로 다시 만들려면 다음을 사용합니다.

```powershell
python scripts/prepare_titanic_data.py --force
```

## 사용 데이터

이번 강의에서는 우리가 원래 설계한 **891행 Titanic training set** 구조를 사용합니다.

예상 구조:

```text
rows: 891
columns: 12
Target: Survived
```

컬럼:

```text
PassengerId, Survived, Pclass, Name, Sex, Age,
SibSp, Parch, Ticket, Fare, Cabin, Embarked
```

주요 검증 기준:

```text
PassengerId: 1..891, unique
Survived: 0/1 only
Survived counts: 0=549, 1=342
Age missing: 177
Cabin missing: 687
Embarked missing: 2
```

이 숫자는 **데이터 무결성 검증 기준**이며, 학생이 Notebook 실행 결과를 작성할 때 복사해서 제출하는 값이 아닙니다. 실제 Notebook에서 직접 실행한 결과를 사용합니다.

## 출처와 재배포 정책

다운로드 원본은 pandas 공식 저장소의 문서용 Titanic CSV를 사용합니다.

- pandas repository: https://github.com/pandas-dev/pandas
- source file: `doc/data/titanic.csv`
- pinned source commit: `54cf59b4fabae5db3b8c7b6b6003f9275596d5f2`
- pandas repository license: BSD-3-Clause
- Kaggle Titanic schema reference: https://www.kaggle.com/competitions/titanic/data

Kaggle competition 페이지는 원본 competition data를 `Subject to Competition Rules`로 표시합니다. 따라서 이 저장소는 Kaggle에서 내려받은 competition 파일을 직접 커밋하지 않습니다.

또한 pandas 저장소의 BSD-3-Clause 라이선스가 이 제3자 데이터셋 자체의 모든 권리를 별도로 재허가한다고 단정하지 않습니다. 그래서 **CSV 자체는 Git에 포함하지 않고 학생이 준비 스크립트로 공개 원본을 내려받도록** 구성합니다.

자세한 출처 설명은 `SOURCE.md`를 확인합니다.

## 무결성 원칙

`scripts/prepare_titanic_data.py`는 URL의 `main` 브랜치가 아니라 **고정 commit**을 사용합니다. 원본 저장소가 나중에 변경되어도 수업 입력이 갑자기 달라지지 않도록 하기 위한 것입니다.

검증에 실패하면 스크립트가 중단됩니다. 데이터가 없거나 검증에 실패했다고 해서 가짜 CSV를 만들거나 예상 숫자를 실제 결과처럼 사용하지 않습니다.

`train.csv`는 재현 가능한 다운로드 결과물이므로 `.gitignore` 대상이며 기본적으로 Git에 커밋하지 않습니다.
