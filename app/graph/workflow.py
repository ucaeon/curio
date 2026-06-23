# LangGraph 멀티 에이전트 워크플로
import logging

from langfuse import observe
from langgraph.graph import END, START, StateGraph

from app.agents.analyst import build_analyst_summary
from app.agents.critic_agent import run_critic_agent
from app.agents.pattern_agent import build_pattern_summary
from app.agents.report_agent import run_report_agent
from app.agents.schemas import AgentRunResult, CriticOutput, EnrichedStrategy, PipelineSnapshot
from app.agents.strategy_agent import run_strategy_agent
from app.config.settings import Settings, get_settings
from app.graph.state import AgentGraphState
from app.monitoring.langfuse_trace import flush_langfuse, init_langfuse
from app.pipeline.snapshot import build_pipeline_snapshot

logger = logging.getLogger(__name__)


def create_agent_graph(
    snapshot: PipelineSnapshot,
    settings: Settings | None = None,
):
    config = settings or get_settings()

    def analyst_node(_state: AgentGraphState) -> AgentGraphState:
        return {"analyst_summary": build_analyst_summary(snapshot)}

    def pattern_node(state: AgentGraphState) -> AgentGraphState:
        return {"pattern_summary": build_pattern_summary(snapshot)}

    def strategy_node(state: AgentGraphState) -> AgentGraphState:
        enriched, overall = run_strategy_agent(
            snapshot,
            state["analyst_summary"],
            state["pattern_summary"],
            settings=config,
        )
        return {
            "enriched_strategies": [item.model_dump() for item in enriched],
            "overall_recommendation": overall,
        }

    def critic_node(state: AgentGraphState) -> AgentGraphState:
        enriched = [EnrichedStrategy(**item) for item in state["enriched_strategies"]]
        critic = run_critic_agent(
            snapshot,
            state["analyst_summary"],
            state["pattern_summary"],
            enriched,
            state["overall_recommendation"],
            settings=config,
        )
        return {"critic": critic.model_dump()}

    def report_node(state: AgentGraphState) -> AgentGraphState:
        enriched = [EnrichedStrategy(**item) for item in state["enriched_strategies"]]
        critic = CriticOutput(**state["critic"])
        report = run_report_agent(
            state["analyst_summary"],
            state["pattern_summary"],
            enriched,
            state["overall_recommendation"],
            critic,
            settings=config,
        )
        return {"report": report}

    graph = StateGraph(AgentGraphState)
    graph.add_node("analyst", analyst_node)
    graph.add_node("pattern", pattern_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("critic", critic_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "analyst")
    graph.add_edge("analyst", "pattern")
    graph.add_edge("pattern", "strategy")
    graph.add_edge("strategy", "critic")
    graph.add_edge("critic", "report")
    graph.add_edge("report", END)

    return graph.compile()


def run_agent_from_snapshot(
    snapshot: PipelineSnapshot,
    settings: Settings | None = None,
) -> AgentRunResult:
    config = settings or get_settings()
    graph = create_agent_graph(snapshot, settings=config)
    final_state = graph.invoke({})

    enriched = [EnrichedStrategy(**item) for item in final_state["enriched_strategies"]]
    critic = CriticOutput(**final_state["critic"])
    return AgentRunResult(
        analyst_summary=final_state["analyst_summary"],
        pattern_summary=final_state["pattern_summary"],
        strategies=enriched,
        overall_recommendation=final_state["overall_recommendation"],
        critic=critic,
        report=final_state["report"],
    )


@observe(name="curio-agent-pipeline")
def run_agent_pipeline(
    settings: Settings | None = None,
    top_n: int | None = None,
) -> AgentRunResult:
    config = settings or get_settings()
    init_langfuse(config)
    try:
        snapshot = build_pipeline_snapshot(settings=config, top_n=top_n)
        result = run_agent_from_snapshot(snapshot, settings=config)
        logger.info("Agent 파이프라인 완료: approved=%s", result.critic.approved)
        return result
    finally:
        flush_langfuse()
