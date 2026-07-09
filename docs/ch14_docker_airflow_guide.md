# 14장 Docker Compose 기반 Airflow 실습 안내

이 문서의 상세 내용은 **14장 메인 강의안**에 통합되었습니다.

- 메인 강의안: `book/chapters/ch14_airflow_pipeline.md`
- 실습 노트북: `notebooks/ch14_airflow_pipeline.ipynb`
- 도커 설치 가이드 블로그 주소: https://blog.naver.com/dev-dog/224341211248

14장 실습은 다음 흐름으로 진행합니다.

```bash
# 1. Docker 설치 확인
docker --version
docker compose version
docker run hello-world

# 2. Python 파이프라인 사전 검증
python scripts/generate_sample_data.py
python scripts/run_ch14_pipeline.py

# 3. Docker Compose 기반 Airflow 실행
cd automation/airflow
cp .env.example .env
# Windows PowerShell: copy .env.example .env

docker compose up airflow-init
docker compose up
```

Airflow UI 접속:

```text
http://localhost:8080
ID: airflow
PW: airflow
```

이 문서는 중복 설명을 피하기 위한 짧은 안내 역할만 유지합니다. 수업 자료로는 `book/chapters/ch14_airflow_pipeline.md`를 기준으로 사용하세요.
