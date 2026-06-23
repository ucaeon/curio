# 골든셋 케이스 1 trial 실행
from app.agents.schemas import AgentRunResult
from app.config.settings import Settings, get_settings
from app.evaluation.grader import grade_golden_case
from app.evaluation.schemas import CaseTrialResult, GoldenCase
from app.graph.workflow import run_agent_from_snapshot


def execute_golden_trial(
    case: GoldenCase,
    trial: int,
    settings: Settings | None = None,
) -> tuple[AgentRunResult, CaseTrialResult]:
    config = settings or get_settings()
    result = run_agent_from_snapshot(case.snapshot, settings=config)
    passed, reasons = grade_golden_case(case, result)
    trial_result = CaseTrialResult(
        case_id=case.case_id,
        trial=trial,
        passed=passed,
        critic_approved=result.critic.approved,
        reasons=reasons,
    )
    return result, trial_result


def execute_golden_trials(
    case: GoldenCase,
    trials: int,
    settings: Settings | None = None,
) -> list[CaseTrialResult]:
    return [
        execute_golden_trial(case, trial, settings=settings)[1] for trial in range(1, trials + 1)
    ]
