# 14장 Docker Compose 기반 Airflow 실습 안내

이 문서는 Chapter 14의 짧은 실행 순서 안내입니다. 상세 기준은 다음 파일을 우선 사용합니다.

- 메인 강의안: `book/chapters/ch14_airflow_pipeline.md`
- 실습 Notebook: `notebooks/ch14_airflow_pipeline.ipynb`
- Canonical DAG: `automation/airflow/dags/ch14_local_analysis_pipeline.py`

> 현재 Docker Compose 환경은 로컬 학습·탐색용입니다. 운영 배포 템플릿이 아닙니다.

## 1. Docker 자체 확인

```bash
docker --version
docker compose version
docker run --rm hello-world
```

실습 시점에는 Airflow 공식 Docker Compose 문서의 현재 요구사항을 다시 확인합니다.

## 2. Python Pipeline을 먼저 검증

프로젝트 루트에서 실행합니다.

```bash
python scripts/generate_sample_data.py
python scripts/run_ch14_pipeline.py
```

다음 조건이 통과되어야 Airflow 단계로 이동합니다.

- PK/FK와 `line_total` 검증
- completed 주문 기준
- 산출물 Freshness
- daily/category 총합
- category 비율
- `pipeline_run_id` 일치
- 보고서 Scope
- `ch14_airflow_validation_log.csv`의 모든 status가 `ok`

## 3. `.env` 준비

```bash
cd automation/airflow
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

`.env.example`의 다음 Secret 값은 **빈 상태가 정상**입니다.

```text
AIRFLOW_DB_PASSWORD=
AIRFLOW_API_JWT_SECRET=
_AIRFLOW_WWW_USER_PASSWORD=
```

실제 untracked `.env`에서 세 값을 서로 다른 임의 값으로 설정합니다.

- 실제 `.env`를 Git에 커밋하지 않습니다.
- 실제 Secret을 화면 공유·캡처·보고서에 출력하지 않습니다.
- 노출된 Secret은 삭제만 하지 말고 폐기·교체합니다.

## 4. Image Build와 Airflow 초기화

```bash
docker compose build
docker compose up airflow-init
```

정상 기준:

```text
airflow-init exit code 0
```

## 5. 서비스 시작

```bash
docker compose up -d
docker compose ps
```

주요 서비스가 running/healthy인지 확인합니다.

문제가 있으면 해당 서비스의 첫 오류 로그를 확인합니다.

## 6. UI 로그인과 DAG 실행

기본 포트라면 다음 주소를 사용합니다.

```text
http://localhost:8080
```

로그인 정보는 **실제 `.env`에서 직접 설정한 사용자 이름과 비밀번호**를 사용합니다.

하드코딩된 `airflow / airflow` 계정을 추측하지 않습니다.

DAG:

```text
ch14_local_analysis_pipeline
```

Graph 구조:

```text
check
 ↓
preprocess
 ↓
analysis
 ↙      ↘
visual  report
 ↘      ↙
 validate
```

마지막 `validate_outputs`가 성공한 뒤 프로젝트의 Validation CSV도 직접 확인합니다.

## 7. 일반 종료와 완전 초기화

일반 종료:

```bash
docker compose down
```

Postgres volume과 학습 실행 기록까지 삭제할 수 있는 파괴적 초기화:

```bash
docker compose down --volumes --remove-orphans
```

두 번째 명령은 완전 초기화가 필요한 학습 환경에서만 사용합니다.

## 8. 최종 원칙

```text
Local Validation PASS
→ Airflow Manual Run
→ Validation PASS 재확인
→ 필요 시 Make/n8n 외부 전달
```

외부 전달은 Validation 전에 실행하지 않으며, 재시도 시 동일 보고서 중복 발송을 막기 위한 별도 idempotency key 또는 Dag Run ID를 기록합니다.
