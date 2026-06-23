# ETL·에이전트 파이프라인 Slack 알림
import argparse
import json
import logging
import os
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

from app.agents.schemas import AgentRunResult, EnrichedStrategy
from app.analytics.strategy_labels import format_strategy_line
from app.config.settings import get_settings
from app.io.paths import find_latest_prefixed_csv
from app.pipeline.load import load_pipeline_data

logger = logging.getLogger(__name__)

TOP_STRATEGY_COUNT = 2


def default_agent_result_path() -> Path:
    return Path(get_settings().agent_result_path)


def load_agent_result(path: Path | str | None = None) -> AgentRunResult | None:
    target = Path(path) if path is not None else default_agent_result_path()
    if not target.exists():
        return None
    return AgentRunResult.model_validate_json(target.read_text(encoding="utf-8"))


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8") as fp:
        return max(sum(1 for _ in fp) - 1, 0)


def _format_strategy_bullet(index: int, strategy: EnrichedStrategy) -> str:
    line = format_strategy_line(strategy.target_condition, strategy.recommended_action)
    ctr_pct = strategy.expected_ctr_gain * 100
    return f"{index}. {line} (CTR +{ctr_pct:.1f}%, lift {strategy.lift:.2f})"


def _format_strategy_row_bullet(index: int, row: object) -> str:
    target = str(getattr(row, "target_condition", row["target_condition"]))
    action = str(getattr(row, "recommended_action", row["recommended_action"]))
    ctr_gain = float(getattr(row, "expected_ctr_gain", row["expected_ctr_gain"]))
    lift = float(getattr(row, "lift", row["lift"]))
    line = format_strategy_line(target, action)
    return f"{index}. {line} (CTR +{ctr_gain * 100:.1f}%, lift {lift:.2f})"


def build_etl_section() -> str:
    data = load_pipeline_data(top_n=TOP_STRATEGY_COUNT)
    features_dir = Path(data.creatives_path).parent
    context_path = find_latest_prefixed_csv(features_dir, "context")

    creatives_rows = _count_csv_rows(data.creatives_path)
    context_rows = _count_csv_rows(context_path) if context_path else 0
    synthetic_rows = data.impression_count

    ctr = float(data.metrics.iloc[0]["ctr"])
    cvr = float(data.metrics.iloc[0]["cvr"])
    ctcvr = float(data.metrics.iloc[0]["ctcvr"])

    kpi_line = (
        f"노출 {synthetic_rows:,} | CTR {ctr * 100:.2f}% | "
        f"CVR {cvr * 100:.2f}% | CTCVR {ctcvr * 100:.2f}%"
    )
    return f"📊 KPI\n{kpi_line}\n소재 {creatives_rows:,} · 상황 {context_rows:,}"


def build_strategy_section(agent_result: AgentRunResult | None) -> str:
    if agent_result is not None and agent_result.strategies:
        bullets = [
            _format_strategy_bullet(index, strategy)
            for index, strategy in enumerate(agent_result.strategies[:TOP_STRATEGY_COUNT], start=1)
        ]
        return "🎯 Top 전략\n" + "\n".join(bullets)

    data = load_pipeline_data(top_n=TOP_STRATEGY_COUNT)
    if data.strategies.empty:
        return "🎯 Top 전략\n없음"

    bullets = [
        _format_strategy_row_bullet(index, row)
        for index, row in enumerate(data.strategies.head(TOP_STRATEGY_COUNT).itertuples(), start=1)
    ]
    return "🎯 Top 전략\n" + "\n".join(bullets)


def build_agent_section(agent_result: AgentRunResult) -> str:
    critic = agent_result.critic
    status = "✅ 승인" if critic.approved else "❌ 거절"
    issue_count = len(critic.issues)
    summary = critic.revised_summary.strip() or agent_result.overall_recommendation.strip()
    if len(summary) > 180:
        summary = summary[:177] + "..."

    lines = [
        "🤖 에이전트",
        f"Critic: {status} (이슈 {issue_count}건)",
    ]
    if summary:
        lines.append(f"권고: {summary}")
    return "\n".join(lines)


def build_pipeline_success_message(
    execution_date: str,
    duration_sec: int,
    agent_result_path: Path | str | None = None,
) -> str:
    agent_result = load_agent_result(agent_result_path)
    if agent_result is None:
        raise FileNotFoundError("에이전트 결과 파일이 없습니다")

    if not agent_result.critic.approved:
        raise ValueError("Critic 미승인 결과로 성공 알림을 보낼 수 없습니다")

    return (
        "✅ Curio 파이프라인 완료\n\n"
        f"실행: {execution_date} | {duration_sec}초\n\n"
        f"{build_etl_section()}\n\n"
        f"{build_strategy_section(agent_result)}\n\n"
        f"{build_agent_section(agent_result)}"
    )


def build_critic_rejected_message(
    execution_date: str,
    agent_result_path: Path | str | None = None,
) -> str:
    agent_result = load_agent_result(agent_result_path)
    if agent_result is None:
        raise FileNotFoundError("에이전트 결과 파일이 없습니다")

    issue_lines = [
        f"- {issue.strategy_id}: {issue.issue}" for issue in agent_result.critic.issues[:3]
    ]
    issues_text = "\n".join(issue_lines) if issue_lines else "- 없음"

    return (
        "❌ Curio 파이프라인 실패: Critic 거절\n\n"
        f"실행: {execution_date}\n\n"
        f"{build_etl_section()}\n\n"
        f"{build_strategy_section(agent_result)}\n\n"
        f"{build_agent_section(agent_result)}\n\n"
        f"이슈:\n{issues_text}"
    )


def build_failure_message(task_id: str, execution_date: str, error: str) -> str:
    return (
        "❌ Curio 파이프라인 실패\n\n"
        f"실패 태스크: {task_id}\n"
        f"실행: {execution_date}\n\n"
        f"오류:\n{error}\n\n"
        "Airflow 로그를 확인해 주세요."
    )


def send_slack_message(text: str) -> None:
    load_dotenv()
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL이 없어 Slack 알림을 건너뜁니다")
        return

    payload = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()
    logger.info("Slack 알림 전송 완료")


def notify_pipeline_success(
    execution_date: str,
    duration_sec: int,
    agent_result_path: Path | str | None = None,
) -> None:
    message = build_pipeline_success_message(execution_date, duration_sec, agent_result_path)
    send_slack_message(message)


def notify_critic_rejected(
    execution_date: str,
    agent_result_path: Path | str | None = None,
) -> None:
    message = build_critic_rejected_message(execution_date, agent_result_path)
    send_slack_message(message)


def notify_failure(task_id: str, execution_date: str, error: str) -> None:
    message = build_failure_message(task_id, execution_date, error)
    send_slack_message(message)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Curio 파이프라인 Slack 알림")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    pipeline_parser = subparsers.add_parser("pipeline", help="ETL+에이전트 성공 알림")
    pipeline_parser.add_argument("--execution-date", required=True)
    pipeline_parser.add_argument("--duration-sec", type=int, default=0)
    pipeline_parser.add_argument(
        "--agent-result-path",
        default=str(default_agent_result_path()),
    )

    critic_parser = subparsers.add_parser("critic-rejected", help="Critic 거절 알림")
    critic_parser.add_argument("--execution-date", required=True)
    critic_parser.add_argument(
        "--agent-result-path",
        default=str(default_agent_result_path()),
    )

    failure_parser = subparsers.add_parser("failure", help="실패 알림")
    failure_parser.add_argument("--task", required=True)
    failure_parser.add_argument("--execution-date", required=True)
    failure_parser.add_argument("--error", required=True)

    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    args = _parse_args()

    if args.mode == "pipeline":
        notify_pipeline_success(
            args.execution_date,
            args.duration_sec,
            args.agent_result_path,
        )
        return

    if args.mode == "critic-rejected":
        notify_critic_rejected(args.execution_date, args.agent_result_path)
        return

    notify_failure(args.task, args.execution_date, args.error)


if __name__ == "__main__":
    main()
