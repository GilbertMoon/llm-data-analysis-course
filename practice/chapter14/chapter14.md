# 14장 실습. 반복되는 분석 흐름을 안전하게 자동화하기

> 목표는 Airflow 화면을 띄우는 것이 아니라 **검증된 로컬 분석을 반복 실행 가능한 Task로 나누고, 실패·재시도·멱등성·산출물 Validation을 확인한 뒤 검증된 결과만 다음 단계로 전달하는 것**입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter14/templates/chapter14_assignment.md`
- 주 제출물: `chapter14/chapter14.ipynb`

공식 Notebook:

```text
notebooks/ch14_airflow_pipeline.ipynb
```

주요 스크립트/자산:

```text
scripts/run_ch14_pipeline.py
scripts/ch14_preprocessing.py
scripts/ch14_analysis.py
scripts/ch14_visualization.py
scripts/ch14_report.py
scripts/ch14_validate_outputs.py
automation/airflow/
docs/ch14_docker_airflow_guide.md
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 `chapter14/chapter14.ipynb`로 사용합니다. Docker/Airflow UI와 터미널 Evidence는 `chapter14/images/`에 저장합니다.

## STEP 1. 자동화 전에 로컬 분석 검증
Airflow를 먼저 실행하지 않습니다.

프로젝트 루트에서:

```powershell
python scripts/run_ch14_pipeline.py
```

확인할 것:
- 입력 파일 존재/범위
- 전처리 성공
- 분석 결과 생성
- 시각화/보고서 생성
- 최종 산출물 Validation

```text
로컬 Python 분석 정상
→ 산출물 Validation 정상
→ 그 다음 자동화
```

## STEP 2. 같은 입력으로 재실행
같은 입력으로 다시 실행했을 때 뜻하지 않은 중복·누적·혼합 결과가 생기지 않는지 확인합니다.

답안에 기록:
- 첫 실행 결과
- 두 번째 실행 결과
- 새로 생긴/변경된 파일
- 중복 누적 여부
- 같은 입력으로 같은 의미의 결과가 나왔는가

### 해석 포인트
멱등성(idempotency)이 왜 자동화에서 중요한지 자신의 말로 설명합니다.

## STEP 3. Task 계약 정리
각 Task에 대해 최소 다음을 작성합니다.

| Task | 입력 | 출력 | 실패 기준 | Retry 가능 여부 | 이유 |
| --- | --- | --- | --- | --- | --- |
| preprocessing | | | | | |
| analysis | | | | | |
| visualization/report | | | | | |
| validation | | | | | |

데이터 컬럼 누락처럼 **결정적 오류(deterministic failure)**는 무의미하게 반복 retry하지 않습니다.

## STEP 4. Docker 환경 확인
실습 환경에서 다음을 확인합니다.

```powershell
docker --version
docker compose version
docker run hello-world
```

Docker가 정상이어도 분석 코드가 맞다는 뜻은 아닙니다.

Evidence:
- Docker 버전/hello-world 핵심 화면
- 실패했다면 오류와 해결 과정

## STEP 5. Airflow 초기화와 DAG 확인
`docs/ch14_docker_airflow_guide.md` 기준으로 Airflow를 초기화하고 DAG를 확인합니다.

대표 흐름:

```text
cd automation/airflow
.env.example → .env
Docker Compose 초기화
Airflow 실행
DAG 확인
```

Secret은 `.env`에만 두고 화면 캡처에 노출하지 않습니다.

## STEP 6. DAG 실행과 Task 상태 확인
DAG를 실행하고 Task별 상태와 로그를 확인합니다.

Evidence 예:
- DAG graph
- Task 성공/실패 상태
- 실패 원인이 드러나는 핵심 로그

하지만 다음 원칙을 반드시 적용합니다.

```text
Task 초록색 ≠ 분석 결과 검증 성공
```

## STEP 7. 최종 산출물 Validation
Airflow Task가 성공한 뒤에도 최종 결과를 별도로 검증합니다.

확인할 것:
- 파일 존재
- 파일이 이번 실행의 결과인가
- 기대 행/컬럼/총합
- 최신성(freshness)
- 여러 산출물이 같은 run에 속하는가
- Validation PASS/FAIL

가능하면 `scripts/ch14_validate_outputs.py` 또는 Notebook의 검증 로직을 사용합니다.

## STEP 8. 실패·Retry 판단
실패 사례 또는 가정 사례 하나 이상을 정해 다음을 작성합니다.

```text
오류 유형
→ 일시적(transient) / 결정적(deterministic)
→ retry 여부
→ retry 횟수/timeout을 제한해야 하는 이유
→ 실패 후 다음 단계로 결과를 전달해도 되는가
```

검증 실패 상태에서는 외부 전달 단계로 넘어가지 않습니다.

## STEP 9. 외부 전달 Gate 설계
Make/n8n/이메일/Slack 등 외부 전달을 연결한다면 다음 조건을 먼저 둡니다.

```text
Task 성공
AND
최종 산출물 Validation PASS
→ 전달 가능
```

중복 전달 방지를 위한 idempotency key 또는 run identifier가 필요한 이유를 설명합니다.

## STEP 10. 최종 자동화 판단
답안에 다음을 작성합니다.

1. 자동화 전에 로컬 검증이 필요한 이유
2. 가장 위험한 실패 유형
3. retry하면 안 되는 오류 사례
4. Task 성공과 분석 Validation의 차이
5. 같은 run 산출물을 확인하는 방법
6. 자동화했을 때 얻는 이점
7. 자동화가 오히려 위험을 키울 수 있는 경우

## 최종 제출

```text
chapter14/
├─ chapter14.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter14/chapter14.ipynb
```

## 완료 체크
- [ ] 로컬 파이프라인 먼저 검증
- [ ] 산출물 Validation 확인
- [ ] 같은 입력 재실행/멱등성 확인
- [ ] Task 입력·출력·실패 계약 작성
- [ ] Docker/Airflow 실행 Evidence
- [ ] DAG/Task 상태 확인
- [ ] Task 성공과 분석 성공을 구분
- [ ] retry 판단 근거 작성
- [ ] 검증 전 외부 전달 금지 원칙 확인
- [ ] 최종 Notebook URL 제출