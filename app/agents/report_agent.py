# Report Agent: 운영자용 최종 보고
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe

from app.agents.llm import get_chat_model
from app.agents.prompt_loader import load_prompt
from app.agents.schemas import CriticOutput, EnrichedStrategy
from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


@observe(as_type="generation", name="report-agent")
def run_report_agent(
    analyst_summary: str,
    pattern_summary: str,
    enriched: list[EnrichedStrategy],
    overall_recommendation: str,
    critic: CriticOutput,
    settings: Settings | None = None,
) -> str:
    config = settings or get_settings()
    system_prompt = load_prompt("report_agent.md")
    user_payload = {
        "analyst_summary": analyst_summary,
        "pattern_summary": pattern_summary,
        "overall_recommendation": overall_recommendation,
        "strategies": [item.model_dump() for item in enriched],
        "critic": critic.model_dump(),
    }
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=json.dumps(user_payload, ensure_ascii=False, indent=2)),
    ]

    llm = get_chat_model(config)
    response = llm.invoke(messages)
    report = str(response.content).strip()
    logger.info("Report Agent 완료: length=%s", len(report))
    return report
