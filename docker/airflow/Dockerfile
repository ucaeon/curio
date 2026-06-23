FROM apache/airflow:3.1.3-python3.11

USER root

# uv 설치 (airflow 유저도 사용 가능하도록 /usr/local/bin)
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
  && install -m 0755 /root/.local/bin/uv /usr/local/bin/uv \
  && install -m 0755 /root/.local/bin/uvx /usr/local/bin/uvx

RUN mkdir -p /opt/airflow/config /opt/curio \
  && chown -R airflow:root /opt/airflow /opt/curio
COPY docker/airflow/entrypoint.sh /opt/airflow/config/entrypoint.sh
RUN chown -R airflow:root /opt/airflow/config \
  && chmod 0755 /opt/airflow/config/entrypoint.sh

WORKDIR /opt/curio

USER airflow
