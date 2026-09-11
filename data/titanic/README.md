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

스크립트는 다음 순서로 동작합니다.

```text
검증된 원본 다운로드
→ raw SHA-256 확인
→ 원본 shape/columns 확인
→ 수업에 필요한 컬럼만 선택
→ 강의안과 맞게 컬럼명 정규화
→ 결과 shape/Target/결측치 개수 검증
→ data/titanic/train.csv 저장
→ 저장 파일 재로딩 검증
```

이미 정상 파일이 있으면 다시 다운로드하지 않습니다. 강제로 다시 만들려면 다음을 사용합니다.

```powershell
python scripts/prepare_titanic_data.py --force
```

## 출처와 라이선스

기준 데이터는 **OpenML Titanic dataset 40945**입니다.

- OpenML: https://www.openml.org/d/40945
- License metadata: `AFL-3.0`
- Source/attribution details: `SOURCE.md`
- Machine-readable validation rules: `dataset_manifest.json`

Kaggle competition 데이터 페이지는 라이선스를 `Subject to Competition Rules`로 표시하므로, Kaggle의 891행 `train.csv`를 그대로 이 공개 저장소에 복제하는 방식은 사용하지 않습니다.

## 수업용 파일 기준

생성되는 파일은 OpenML 40945의 1309명 labeled passenger 데이터를 기반으로 하며, STEP 11에서 학생이 직접 train/test split을 수행합니다.

예상 구조:

```text
rows: 1309
columns: 11
Target: Survived
```

컬럼:

```text
Pclass, Survived, Name, Sex, Age, SibSp, Parch, Ticket, Fare, Cabin, Embarked
```

`boat`, `body`, `home.dest`는 수업용 변환에서 제외합니다. `PassengerId`는 원본에 없으므로 임의 생성하지 않습니다.

## 무결성 원칙

원본 raw CSV의 기대 SHA-256:

```text
c617db2c7470716250f6f001be51304c76bcc8815527ab8bae734bdca0735737
```

SHA가 다르면 스크립트가 중단됩니다. 데이터가 없거나 검증에 실패했다고 해서 가짜 CSV를 만들거나 예상 숫자를 실제 결과처럼 사용하지 않습니다.

`train.csv`는 재현 가능한 다운로드/변환 결과물이므로 기본적으로 Git에 커밋하지 않습니다. 학생은 실습 시작 시 스크립트로 생성합니다.
