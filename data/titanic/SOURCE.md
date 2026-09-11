# Titanic dataset source and usage policy

이 실습은 **891행 Titanic training set** 구조를 사용합니다.

## 선택 이유

강의안과 Notebook은 처음부터 다음 구조를 기준으로 설계했습니다.

```text
891 rows
12 columns
PassengerId
Survived
Pclass
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

Kaggle `Titanic - Machine Learning from Disaster`의 `train.csv`가 이 구조를 사용하지만, Kaggle competition 데이터 페이지는 데이터 라이선스를 **`Subject to Competition Rules`**로 표시합니다.

따라서 이 공개 수업 저장소에서는 Kaggle에서 내려받은 competition 파일을 그대로 재배포하지 않습니다.

대신 pandas 공식 저장소의 문서 예제에서 공개적으로 제공되는 동일한 891행 구조의 CSV를 **학생이 로컬에서 다운로드**하도록 합니다.

## 다운로드 출처

- Repository: `pandas-dev/pandas`
- Repository URL: https://github.com/pandas-dev/pandas
- File: `doc/data/titanic.csv`
- Pinned commit: `54cf59b4fabae5db3b8c7b6b6003f9275596d5f2`
- Pinned raw URL:
  `https://raw.githubusercontent.com/pandas-dev/pandas/54cf59b4fabae5db3b8c7b6b6003f9275596d5f2/doc/data/titanic.csv`
- pandas documentation tutorial using Titanic data:
  https://pandas.pydata.org/docs/getting_started/intro_tutorials/02_read_write.html
- pandas repository license: BSD-3-Clause

해당 commit은 `doc/data/titanic.csv`의 이력을 고정하기 위해 사용합니다. `main` 브랜치를 직접 사용하지 않으므로 이후 pandas 저장소가 변경되어도 강의 데이터가 의도치 않게 바뀌는 위험을 줄입니다.

## 라이선스 해석에 대한 주의

pandas 저장소 전체는 BSD-3-Clause 라이선스로 배포됩니다. 다만 이 사실만으로 저장소 안에 포함된 **제3자 데이터셋의 원 권리까지 모두 BSD-3-Clause로 재허가되었다고 단정하지 않습니다.**

그래서 이 프로젝트는 다음 정책을 사용합니다.

```text
CSV를 이 저장소에 직접 vendor/재배포하지 않음
→ scripts/prepare_titanic_data.py로 학생이 공개 원본에서 직접 다운로드
→ 출처와 고정 commit 기록
→ 다운로드 후 구조/값을 검증
```

Kaggle competition 페이지는 데이터 구조와 원래 학습 과제의 참고 링크로만 사용하며, competition 파일을 이 저장소에 복제하지 않습니다.

## 수업용 데이터 무결성 기준

다운로드한 CSV는 다음 조건을 모두 만족해야 합니다.

```text
shape: (891, 12)

columns:
PassengerId
Survived
Pclass
Name
Sex
Age
SibSp
Parch
Ticket
Fare
Cabin
Embarked

PassengerId:
1..891 순서
중복 없음
결측 없음

Survived:
0 또는 1만 허용
0 = 549
1 = 342
결측 없음

missing:
Age = 177
Cabin = 687
Embarked = 2
```

검증 기준은 잘못된 파일이나 다른 Titanic 변형 데이터셋이 섞이는 것을 막기 위한 것입니다.

## 중요한 차이

이전에 검토했던 OpenML Titanic dataset 40945는 1309명의 승객을 포함하며 `PassengerId`가 없는 다른 버전입니다. 데이터 자체는 유효하지만 현재 강의안의 891행 Kaggle-style 구조와 일치하지 않으므로 **본 실습 기준 데이터로 사용하지 않습니다.**

## 생성 파일

학생이 다음 명령을 실행하면:

```powershell
python scripts/prepare_titanic_data.py
```

다음 파일이 로컬에 생성됩니다.

```text
data/titanic/train.csv
```

이 파일은 `.gitignore` 대상이며 공개 저장소에는 커밋하지 않습니다.
