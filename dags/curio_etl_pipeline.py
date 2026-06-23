# Curio ETL DAG: ingestion -> feature -> synthetic -> agent -> slack
from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

from app.monitoring.airflow_callbacks import (
    agent_result_path,
    notify_slack_failure,
    notify_slack_success,
    project_dir,
)

with DAG(
    dag_id="curio_etl_pipeline",
    description="Curio ingestion -> feature -> synthetic -> agent -> slack",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["curio", "etl"],
    default_args={"on_failure_callback": notify_slack_failure},
):
    base = project_dir()
    result_path = agent_result_path()

    env_exports = (
        "export PYTHONUNBUFFERED=1 "
        "PATH=/usr/local/bin:$PATH "
        "UV_PROJECT_ENVIRONMENT=/opt/airflow/.curio-venv;"
    )
    workdir = f"cd {base} &&"

    seoul_event = BashOperator(
        task_id="ingest_seoul_event",
        bash_command=f"{env_exports} {workdir} uv run python -m app.ingestion.seoul_event.run",
    )
    tour = BashOperator(
        task_id="ingest_tour",
        bash_command=f"{env_exports} {workdir} uv run python -m app.ingestion.tour.run",
    )
    weather = BashOperator(
        task_id="ingest_weather",
        bash_command=f"{env_exports} {workdir} uv run python -m app.ingestion.weather.run",
    )

    build_feature_and_synthetic = BashOperator(
        task_id="build_feature_and_synthetic",
        bash_command=f"{env_exports} {workdir} uv run python -m app.preprocessing.feature.run",
    )

    run_agent = BashOperator(
        task_id="run_agent_pipeline",
        bash_command=(
            f"{env_exports} {workdir} "
            f"uv run python -m app.agents.run --output json "
            f"--result-path {result_path}"
        ),
    )

    slack = PythonOperator(
        task_id="notify_slack",
        python_callable=notify_slack_success,
    )

    [seoul_event, tour, weather] >> build_feature_and_synthetic >> run_agent >> slack
