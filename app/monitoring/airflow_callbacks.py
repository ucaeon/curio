# Airflow Slack 콜백
import json
import logging
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

AGENT_RESULT_REL_PATH = "data/processed/agent/run_latest.json"


def project_dir() -> Path:
    return Path(os.environ.get("CURIO_PROJECT_DIR", "/opt/curio"))


def agent_result_path() -> Path:
    rel = os.environ.get("AGENT_RESULT_PATH", AGENT_RESULT_REL_PATH)
    return project_dir() / rel


def format_execution_date(dag_run: object) -> str:
    run_after = getattr(dag_run, "run_after", None)
    if run_after is not None:
        return run_after.strftime("%Y-%m-%d %H:%M")
    logical_date = getattr(dag_run, "logical_date", None)
    if logical_date is not None:
        return logical_date.strftime("%Y-%m-%d %H:%M")
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M")


def invoke_slack_notify(args: list[str]) -> None:
    env = os.environ.copy()
    env["PATH"] = "/usr/local/bin:" + env.get("PATH", "")
    env["UV_PROJECT_ENVIRONMENT"] = os.environ.get(
        "UV_PROJECT_ENVIRONMENT",
        "/opt/airflow/.curio-venv",
    )
    result = subprocess.run(
        ["uv", "run", "python", "-m", "app.monitoring.slack_notify", *args],
        cwd=str(project_dir()),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Slack 알림 실행 실패: %s", result.stderr.strip())


def is_critic_rejection_already_notified() -> bool:
    result_path = agent_result_path()
    if not result_path.exists():
        return False
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        critic = payload.get("critic", {})
        return critic.get("approved") is False
    except (json.JSONDecodeError, OSError):
        return False


def notify_slack_success(**context: object) -> None:
    dag_run = context["dag_run"]
    start_date = getattr(dag_run, "start_date", None)
    duration_sec = 0
    if start_date is not None:
        duration_sec = max(int((datetime.now(UTC) - start_date).total_seconds()), 0)

    invoke_slack_notify(
        [
            "pipeline",
            "--execution-date",
            format_execution_date(dag_run),
            "--duration-sec",
            str(duration_sec),
            "--agent-result-path",
            str(agent_result_path()),
        ]
    )


def notify_slack_failure(context: dict[str, object]) -> None:
    task_instance = context["task_instance"]
    dag_run = context["dag_run"]
    exception = context.get("exception")
    error = str(exception) if exception else "알 수 없는 오류"
    task_id = str(task_instance.task_id)

    if task_id == "run_agent_pipeline" and is_critic_rejection_already_notified():
        logger.info("Critic 거절 Slack은 run_agent에서 이미 전송됨")
        return

    invoke_slack_notify(
        [
            "failure",
            "--task",
            task_id,
            "--execution-date",
            format_execution_date(dag_run),
            "--error",
            error,
        ]
    )
