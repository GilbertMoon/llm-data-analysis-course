FROM apache/airflow:3.3.0

ARG AIRFLOW_VERSION=3.3.0

COPY requirements.txt /requirements.txt

# Airflow 공식 Docker Compose 문서의 권장 방식에 맞춰,
# requirements 설치 시 apache-airflow를 같은 버전으로 함께 지정합니다.
# 이렇게 해야 pip가 Airflow 또는 관련 provider 의존성을 예상치 못하게 바꾸는 상황을 줄일 수 있습니다.
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
