ARG AIRFLOW_VERSION=3.3.0
FROM apache/airflow:${AIRFLOW_VERSION}

# Re-declare the build arg after FROM so it is available to RUN.
ARG AIRFLOW_VERSION

COPY requirements.txt /requirements.txt

# Keep apache-airflow pinned to the exact base-image version while adding the
# course dependencies. This follows the Airflow Docker guidance and reduces
# accidental Airflow upgrades/downgrades during pip dependency resolution.
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt \
    && pip check
