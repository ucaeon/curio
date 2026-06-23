# metrics 지표 계산 테스트
import pandas as pd

from app.analytics.metrics import compute_ctcvr, compute_ctr, compute_cvr, compute_metrics


def test_compute_ctr() -> None:
    log_df = pd.DataFrame({"clicked": [1, 0, 1, 0], "converted": [1, 0, 0, 0]})
    assert compute_ctr(log_df) == 0.5


def test_compute_cvr() -> None:
    log_df = pd.DataFrame({"clicked": [1, 1, 0, 0], "converted": [1, 0, 0, 0]})
    assert compute_cvr(log_df) == 0.5


def test_compute_ctcvr() -> None:
    log_df = pd.DataFrame({"clicked": [1, 1, 0, 0], "converted": [1, 0, 0, 0]})
    assert compute_ctcvr(log_df) == 0.25


def test_compute_cvr_when_no_clicks() -> None:
    log_df = pd.DataFrame({"clicked": [0, 0], "converted": [0, 0]})
    assert compute_cvr(log_df) == 0.0


def test_compute_metrics() -> None:
    log_df = pd.DataFrame({"clicked": [1, 1, 0, 0], "converted": [1, 0, 0, 0]})
    metrics_df = compute_metrics(log_df)
    assert metrics_df.iloc[0]["ctr"] == 0.5
    assert metrics_df.iloc[0]["cvr"] == 0.5
    assert metrics_df.iloc[0]["ctcvr"] == 0.25


def test_empty_log() -> None:
    log_df = pd.DataFrame({"clicked": pd.Series(dtype=int), "converted": pd.Series(dtype=int)})
    assert compute_ctr(log_df) == 0.0
    assert compute_cvr(log_df) == 0.0
    assert compute_ctcvr(log_df) == 0.0
