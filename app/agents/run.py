import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from app.agents.schemas import AgentRunResult
from app.config.settings import get_settings
from app.graph.workflow import run_agent_pipeline
from app.monitoring.slack_notify import notify_critic_rejected, notify_pipeline_success

logger = logging.getLogger(__name__)


def _save_agent_result(result: AgentRunResult, result_path: Path) -> None:
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("에이전트 결과 저장: %s", result_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Curio LangGraph 타겟팅 에이전트 실행")
    parser.add_argument(
        "--output",
        choices=["json", "report"],
        default="report",
        help="json: 전체 구조화 결과, report: 최종 보고서만",
    )
    parser.add_argument(
        "--result-path",
        default=None,
        help="에이전트 구조화 결과 JSON 저장 경로",
    )
    parser.add_argument(
        "--slack",
        action="store_true",
        help="단독 실행 성공 시 Slack 알림 전송 (Critic 거절은 항상 전송)",
    )
    return parser


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    args = _build_parser().parse_args()
    result_path = Path(args.result_path or get_settings().agent_result_path)
    execution_date = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")

    try:
        result = run_agent_pipeline()
    except FileNotFoundError as exc:
        logger.error("데이터 파일 없음: %s", exc)
        return 1
    except Exception as exc:
        logger.exception("Agent 실행 실패: %s", exc)
        return 1

    _save_agent_result(result, result_path)

    if not result.critic.approved:
        notify_critic_rejected(execution_date, result_path)
        logger.warning("Critic 거절: issues=%s", len(result.critic.issues))
        if args.output == "json":
            print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        else:
            print(result.report)
        return 2

    if args.slack:
        notify_pipeline_success(execution_date, duration_sec=0, agent_result_path=result_path)

    if args.output == "json":
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    else:
        print(result.report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
