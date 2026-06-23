# 골든셋 pass@k · pass^k 지표 테스트
from app.evaluation.metrics import aggregate_suite_results, case_pass_at_k, case_pass_pow_k
from app.evaluation.schemas import CaseTrialResult


def test_case_pass_at_k_any_success() -> None:
    assert case_pass_at_k([False, True, False], k=3) is True
    assert case_pass_at_k([False, False, False], k=3) is False


def test_case_pass_pow_k_all_success() -> None:
    assert case_pass_pow_k([True, True, True], k=3) is True
    assert case_pass_pow_k([True, False, True], k=3) is False


def test_aggregate_suite_results() -> None:
    trial_results = [
        CaseTrialResult(
            case_id="gs_a",
            trial=1,
            passed=True,
            critic_approved=True,
            reasons=[],
        ),
        CaseTrialResult(
            case_id="gs_a",
            trial=2,
            passed=False,
            critic_approved=False,
            reasons=["fail"],
        ),
        CaseTrialResult(
            case_id="gs_a",
            trial=3,
            passed=True,
            critic_approved=True,
            reasons=[],
        ),
        CaseTrialResult(
            case_id="gs_b",
            trial=1,
            passed=True,
            critic_approved=True,
            reasons=[],
        ),
        CaseTrialResult(
            case_id="gs_b",
            trial=2,
            passed=True,
            critic_approved=True,
            reasons=[],
        ),
        CaseTrialResult(
            case_id="gs_b",
            trial=3,
            passed=True,
            critic_approved=True,
            reasons=[],
        ),
    ]

    result = aggregate_suite_results(trial_results, k=3, trials=3)
    assert result.case_count == 2
    assert result.pass_at_k == 1.0
    assert result.pass_pow_k == 0.5
    assert result.pass_at_1 == 1.0
