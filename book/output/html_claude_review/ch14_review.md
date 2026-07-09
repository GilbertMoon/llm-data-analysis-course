# ch14 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 파일**: `book/chapters/ch14_airflow_pipeline.md`  
> **상태**: Docker Compose 기반 실습 흐름 반영본  
> **갱신 내용**: Docker 설치는 별도 블로그 글로 분리하고, 강의안과 실습 자료는 Docker Compose 기반 Airflow 실행으로 재구성

---

## 1. 반영 요약

기존 14장은 로컬 Python 가상환경에 Airflow를 설치하고 `airflow standalone`으로 실행하는 흐름이 중심이었다. 이번 개정에서는 수업 운영 안정성을 위해 Docker 설치 과정은 별도 블로그 글로 분리하고, 강의안 본문은 Docker Compose 기반 Airflow 실행과 DAG 실습에 집중하도록 변경했다.

참고 블로그:

- https://blog.naver.com/dev-dog/224341211248

---

## 2. 주요 변경 사항

| 구분 | 기존 방향 | 변경 방향 |
|---|---|---|
| Docker 설명 | Docker는 실습에서 제외 | Docker 설치는 별도 글 참고, 실습은 Docker Compose 기준 |
| Airflow 설치 | 로컬 venv + pip install + airflow standalone | `automation/airflow/docker-compose.yml` 기준 실행 |
| Windows 안내 | WSL2 직접 Airflow 설치 권장 | Docker Desktop 설치 후 Docker Compose 실행 권장 |
| 사전 검증 | 일부 안내 | `python scripts/run_ch14_pipeline.py`로 Python 코드 먼저 검증 |
| DAG 경로 | 로컬 경로 중심 | 컨테이너 내부 `/opt/airflow/project` 기준 |
| 의존성 | 로컬 Python 의존성 | `automation/airflow/requirements.txt`와 Dockerfile로 관리 |
| 산출물 검증 | 유지 | Docker 실행 후에도 동일한 검증 로그 확인 |

---

## 3. 변경된 주요 파일

| 파일 | 변경 내용 |
|---|---|
| `book/chapters/ch14_airflow_pipeline.md` | Docker Compose 기반 강의안으로 재작성 |
| `notebooks/ch14_airflow_pipeline.ipynb` | Docker 설치 참고, Compose 실행, DAG 실행 중심으로 재구성 |
| `automation/airflow/docker-compose.yml` | Airflow 3.3.0 + Postgres + LocalExecutor 구성으로 보강 |
| `automation/airflow/Dockerfile` | Airflow 이미지에 수업용 Python 패키지 설치 |
| `automation/airflow/requirements.txt` | pandas, matplotlib, scikit-learn 등 추가 |
| `automation/airflow/.env.example` | 수업용 Airflow 기본 환경변수 예시 추가 |
| `automation/airflow/dags/ch14_local_analysis_pipeline.py` | Docker 내부 경로 기준 DAG 추가 |
| `dags/ch14_local_analysis_pipeline.py` | Docker Compose 경로 기준으로 보완 |
| `src/automation_pipeline.py` | `PROJECT_ROOT` 환경변수와 Docker 기반 setup guide 반영 |
| `docs/ch14_docker_airflow_guide.md` | Docker Compose 기반 Airflow 실행 절차 별도 문서 추가 |
| `.gitignore` | Airflow logs/config/plugins/.env 등 런타임 파일 제외 |

---

## 4. 현재 실습 흐름

```bash
# 1. Docker 설치 확인
docker --version
docker compose version
docker run hello-world

# 2. Python 분석 코드 사전 검증
python scripts/generate_sample_data.py
python scripts/run_ch14_pipeline.py

# 3. Airflow Docker Compose 실행
cd automation/airflow
cp .env.example .env
# Windows PowerShell: copy .env.example .env

docker compose up airflow-init
docker compose up
```

Airflow UI:

```text
http://localhost:8080
ID: airflow
PW: airflow
```

실행 DAG:

```text
ch14_local_analysis_pipeline
```

---

## 5. 검토 결과

이번 개정으로 다음 문제가 해소되었다.

- 학생별 로컬 Airflow 설치 오류 가능성 감소
- Windows PowerShell, WSL2, macOS/Linux 간 환경 차이 감소
- Docker 설치 학습과 Airflow 파이프라인 학습의 관심사 분리
- Airflow 실행 전 Python 코드 문제를 먼저 분리해 확인 가능
- Docker 컨테이너 내부 경로와 호스트 프로젝트 경로의 기준 명확화
- `requirements.txt` 기반으로 Airflow 컨테이너 의존성 관리 가능

---

## 6. 남은 운영상 주의사항

- Docker Desktop 설치와 WSL2 backend 설정은 별도 블로그 글에서 충분히 안내되어야 한다.
- Docker Desktop 메모리가 부족하면 Airflow 컨테이너가 불안정할 수 있으므로 4GB 이상, 가능하면 8GB 권장을 공지한다.
- 8080 포트 충돌 시 `docker-compose.yml`의 포트 매핑을 `8081:8080` 등으로 변경하도록 안내한다.
- 수업 중 네트워크가 불안정하면 최초 이미지 빌드가 오래 걸릴 수 있으므로 사전 설치를 권장한다.
- HTML 출력본은 이번 개정 내용에 맞춰 단순 HTML 형태로 갱신했으며, 최종 출판용 HTML은 별도 빌드 파이프라인에서 재생성하는 것이 바람직하다.
