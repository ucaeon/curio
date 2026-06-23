# 골든셋 평가 실행
import logging
from datetime import UTC, datetime

from langfuse import get_client, observe, propagate_attributes

from app.config.settings import Settings, get_settings
from app.evaluation.case_runner import execute_golden_trial
from app.evaluation.golden_cases import load_golden_cases
from app.evaluation.metrics import aggregate_suite_results
from app.evaluation.schemas import CaseTrialResult, EvalSuiteResult, GoldenCase
from app.monitoring.langfuse_trace import flush_langfuse, init_langfuse

logger = logging.getLogger(__name__)


def _score_langfuse_trace(passed: bool, reasons: list[str]) -> None:
    comment = "pass" if passed else "; ".join(reasons[:5])
    get_client().score_current_trace(
        name="golden_pass",
        value=1.0 if passed else 0.0,
        data_type="NUMERIC",
        comment=comment,
    )


@observe(name="golden-eval-case", as_type="evaluator")
def run_golden_case_trial(
    case: GoldenCase,
    trial: int,
    settings: Settings | None = None,
) -> CaseTrialResult:
    config = settings or get_settings()
    with propagate_attributes(
        trace_name=f"golden-eval/{case.case_id}/trial-{trial}",
        tags=["golden-eval", case.case_id],
        metadata={
            "suite": "golden-agent-eval",
            "case_id": case.case_id,
            "trial": trial,
            "description": case.description,
            "expected_approved": case.expectation.expected_approved,
        },
    ):
        _result, trial_result = execute_golden_trial(case, trial, settings=config)
        _score_langfuse_trace(trial_result.passed, trial_result.reasons)
        logger.info(
            "골든셋 trial 완료: case=%s trial=%s passed=%s approved=%s",
            case.case_id,
            trial,
            trial_result.passed,
            trial_result.critic_approved,
        )
        return trial_result


@observe(name="golden-eval-suite", as_type="evaluator")
def run_golden_eval_suite(
    *,
    k: int = 3,
    trials: int = 3,
    case_ids: list[str] | None = None,
    settings: Settings | None = None,
) -> EvalSuiteResult:
    if k < 1 or trials < 1:
        raise ValueError("k와 trials는 1 이상이어야 합니다")
    if trials < k:
        raise ValueError("trials는 k 이상이어야 합니다")

    config = settings or get_settings()
    init_langfuse(config)

    try:
        cases = load_golden_cases()
        if case_ids:
            selected = {case_id for case_id in case_ids}
            cases = [case for case in cases if case.case_id in selected]
            if not cases:
                raise ValueError(f"골든셋 case_id를 찾을 수 없습니다: {case_ids}")

        run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        with propagate_attributes(
            trace_name=f"golden-eval-suite/{run_id}",
            tags=["golden-eval", "suite"],
            metadata={
                "suite": "golden-agent-eval",
                "run_id": run_id,
                "k": k,
                "trials": trials,
                "case_count": len(cases),
            },
        ):
            trial_results: list[CaseTrialResult] = []
            for case in cases:
                for trial in range(1, trials + 1):
                    trial_results.append(run_golden_case_trial(case, trial, settings=config))

            suite_result = aggregate_suite_results(trial_results, k=k, trials=trials)
            get_client().score_current_trace(
                name="pass_at_k",
                value=suite_result.pass_at_k,
                data_type="NUMERIC",
                comment=f"k={k}, trials={trials}",
            )
            get_client().score_current_trace(
                name="pass_pow_k",
                value=suite_result.pass_pow_k,
                data_type="NUMERIC",
                comment=f"k={k}, trials={trials}",
            )
            logger.info(
                "골든셋 평가 완료: pass@1=%.3f pass@%s=%.3f pass^%s=%.3f",
                suite_result.pass_at_1,
                k,
                suite_result.pass_at_k,
                k,
                suite_result.pass_pow_k,
            )
            return suite_result
    finally:
        flush_langfuse()
