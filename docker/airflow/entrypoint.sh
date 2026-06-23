#!/usr/bin/env bash
set -euo pipefail

export UV_PROJECT_ENVIRONMENT=/opt/airflow/.curio-venv

# Airflow UI 비밀번호 파일 생성 (Git에 올리지 않음)
PASSWORDS_FILE=/opt/airflow/config/simple_auth_manager_passwords.json
AIRFLOW_WEB_PASSWORD="${AIRFLOW_WEB_PASSWORD:-airflow}"
if [ ! -f "${PASSWORDS_FILE}" ]; then
  printf '{"airflow": "%s"}\n' "${AIRFLOW_WEB_PASSWORD}" >"${PASSWORDS_FILE}"
fi

cd /opt/curio

# 호스트 .venv 대신 컨테이너 내부 Linux venv 사용
if [ ! -d "${UV_PROJECT_ENVIRONMENT}" ]; then
  uv venv --python 3.11 "${UV_PROJECT_ENVIRONMENT}"
fi
uv sync --frozen --no-dev

exec airflow standalone
