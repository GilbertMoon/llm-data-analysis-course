# 14장 Docker Compose 기반 Airflow 실습 안내

이 문서는 14장 실습에서 사용할 Docker Compose 기반 Airflow 실행 흐름을 정리합니다.

Docker Desktop 설치와 기본 사용법은 별도 블로그 글을 참고합니다.

- Docker 설치 가이드: https://blog.naver.com/dev-dog/224341211248

이 저장소의 14장 강의안과 노트북은 Docker가 이미 설치되어 있다고 가정하고, Airflow 파이프라인 실행과 DAG 실습에 집중합니다.

## 1. Docker 설치 확인

프로젝트 루트 또는 임의의 터미널에서 아래 명령을 실행합니다.

```bash
docker --version
docker compose version
docker run hello-world
```

세 명령이 모두 정상 동작하면 Docker 기반 Airflow 실습을 진행할 수 있습니다.

## 2. Python 파이프라인 사전 검증

Airflow를 실행하기 전에 분석 코드 자체가 정상인지 먼저 확인합니다.

```bash
python scripts/generate_sample_data.py
python scripts/run_ch14_pipeline.py
```

이 단계에서 실패하면 Docker나 Airflow 문제가 아니라 Python 분석 코드 또는 데이터 파일 문제일 가능성이 큽니다.

## 3. Docker Compose Airflow 실행

Airflow 실습 폴더로 이동합니다.

```bash
cd automation/airflow
```

환경변수 예시 파일을 복사합니다.

macOS/Linux/WSL2:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
copy .env.example .env
```

최초 1회 초기화를 실행합니다.

```bash
docker compose up airflow-init
```

초기화가 완료되면 Airflow 서비스를 실행합니다.

```bash
docker compose up
```

## 4. Airflow UI 접속

브라우저에서 아래 주소로 접속합니다.

```text
http://localhost:8080
```

수업용 기본 계정은 다음과 같습니다.

```text
ID: airflow
PW: airflow
```

## 5. DAG 실행

Airflow UI에서 `ch14_local_analysis_pipeline` DAG를 찾습니다.

1. DAG를 활성화합니다.
2. 수동 실행 버튼을 클릭합니다.
3. Graph 또는 Grid 화면에서 Task 실행 순서를 확인합니다.
4. 실패한 Task가 있으면 로그를 확인합니다.

실행 순서는 다음과 같습니다.

```text
check_input_files
→ run_preprocessing
→ run_analysis
→ generate_visualizations
→ generate_report
→ validate_outputs
```

## 6. 산출물 확인

프로젝트 루트 기준으로 다음 파일이 생성되어야 합니다.

```text
data/processed/customers_clean.csv
data/processed/products_clean.csv
data/processed/orders_clean.csv
data/processed/order_items_clean.csv
reports/ch14_daily_sales.csv
reports/ch14_category_sales.csv
reports/figures/ch14_daily_sales.png
reports/ch14_airflow_report.md
reports/ch14_airflow_validation_log.csv
```

검증 로그는 다음 파일에서 확인합니다.

```text
reports/ch14_airflow_validation_log.csv
```

모든 행의 `status`가 `ok`이면 주요 산출물 생성이 정상입니다.

## 7. 종료와 초기화

Airflow 컨테이너를 종료합니다.

```bash
docker compose down
```

DB와 볼륨까지 완전히 초기화하려면 다음 명령을 사용합니다.

```bash
docker compose down --volumes --remove-orphans
```

이 명령은 Airflow 메타DB도 삭제하므로, DAG 실행 기록과 계정 정보가 초기화됩니다.

## 8. 자주 발생하는 문제

### 8080 포트 충돌

이미 다른 프로그램이 8080 포트를 사용 중이면 Airflow UI가 열리지 않을 수 있습니다. 이 경우 `automation/airflow/docker-compose.yml`에서 포트를 바꿉니다.

```yaml
ports:
  - "8081:8080"
```

이후 브라우저에서 `http://localhost:8081`로 접속합니다.

### Docker 메모리 부족

Airflow는 여러 컨테이너를 실행하므로 Docker Desktop에 충분한 메모리가 필요합니다. Docker Desktop 설정에서 메모리를 4GB 이상, 가능하면 8GB 정도로 설정하는 것을 권장합니다.

### ModuleNotFoundError

DAG 실행 중 `ModuleNotFoundError`가 발생하면 다음을 확인합니다.

- `automation/airflow/Dockerfile`에서 `requirements.txt`를 설치하는지 확인
- `automation/airflow/requirements.txt`에 필요한 패키지가 있는지 확인
- `docker compose build --no-cache` 후 다시 실행

```bash
docker compose build --no-cache
docker compose up airflow-init
docker compose up
```

### 입력 파일 없음

`check_input_files` 단계에서 실패하면 프로젝트 루트에서 샘플 데이터를 생성합니다.

```bash
python scripts/generate_sample_data.py
```

또는 Docker 컨테이너 내부에서 실행하려면 다음처럼 실행할 수 있습니다.

```bash
docker compose run --rm airflow-api-server python /opt/airflow/project/scripts/generate_sample_data.py
```

## 9. 수업 운영 기준

- Docker 설치 과정은 별도 블로그 글로 분리합니다.
- 14장 강의안은 Docker 설치가 완료되어 있다는 전제에서 시작합니다.
- Airflow 설치 자체보다 DAG, Task, 의존성, 로그, 실패 확인, 산출물 검증에 집중합니다.
- Python 파이프라인 사전 검증 후 Docker Compose Airflow를 실행합니다.
