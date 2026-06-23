# Dashboard 데이터 로딩 테스트
from pathlib import Path

import pytest

from app.pipeline.load import load_dashboard_data


def test_load_dashboard_data_returns_strategies() -> None:
    synthetic_dir = Path("data/processed/synthetic")
    if not any(synthetic_dir.glob("synthetic_log_*.csv")):
        pytest.skip("synthetic log CSV가 없습니다")

    data = load_dashboard_data(top_n=5)
    assert data.impression_count > 0
    assert data.user_count > 0
    assert {"ctr", "cvr", "ctcvr"}.issubset(data.metrics.columns)
    assert len(data.strategies) <= 5
    if not data.strategies.empty:
        assert "strategy_score" in data.strategies.columns
