# pass@k · pass^k 지표 계산
from app.evaluation.schemas import CaseAggregateResult, CaseTrialResult, EvalSuiteResult


def case_pass_at_k(trial_passes: list[bool], k: int) -> bool:
    if not trial_passes:
        return False
    window = trial_passes[:k]
    return any(window)


def case_pass_pow_k(trial_passes: list[bool], k: int) -> bool:
    if len(trial_passes) < k:
        return False
    return all(trial_passes[:k])


def aggregate_suite_results(
    trial_results: list[CaseTrialResult],
    *,
    k: int,
    trials: int,
) -> EvalSuiteResult:
    case_ids = sorted({item.case_id for item in trial_results})
    case_trials: dict[str, list[bool]] = {case_id: [] for case_id in case_ids}

    for item in sorted(trial_results, key=lambda row: (row.case_id, row.trial)):
        case_trials[item.case_id].append(item.passed)

    case_aggregates = [
        CaseAggregateResult(
            case_id=case_id,
            trial_passes=passes,
            pass_at_k=case_pass_at_k(passes, k),
            pass_pow_k=case_pass_pow_k(passes, k),
        )
        for case_id, passes in case_trials.items()
    ]

    case_count = len(case_aggregates)
    if case_count == 0:
        return EvalSuiteResult(
            k=k,
            trials=trials,
            case_count=0,
            pass_at_k=0.0,
            pass_pow_k=0.0,
            pass_at_1=0.0,
            cases=[],
            trial_results=trial_results,
        )

    pass_at_k = sum(item.pass_at_k for item in case_aggregates) / case_count
    pass_pow_k = sum(item.pass_pow_k for item in case_aggregates) / case_count
    pass_at_1 = sum(case_pass_at_k(item.trial_passes, 1) for item in case_aggregates) / case_count

    return EvalSuiteResult(
        k=k,
        trials=trials,
        case_count=case_count,
        pass_at_k=pass_at_k,
        pass_pow_k=pass_pow_k,
        pass_at_1=pass_at_1,
        cases=case_aggregates,
        trial_results=trial_results,
    )
