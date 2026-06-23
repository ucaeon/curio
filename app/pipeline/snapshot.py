# Agent 입력용 PipelineSnapshot 생성
import logging

import pandas as pd

from app.agents.schemas import PipelineSnapshot, StrategyRecord
from app.config.settings import Settings, get_settings
from app.pipeline.load import PipelineData, load_pipeline_data

logger = logging.getLogger(__name__)


def _row_to_strategy(row: pd.Series) -> StrategyRecord:
    return StrategyRecord(
        strategy_id=str(row["strategy_id"]),
        strategy_name=str(row["strategy_name"]),
        target_condition=str(row["target_condition"]),
        recommended_action=str(row["recommended_action"]),
        expected_ctr_gain=float(row["expected_ctr_gain"]),
        expected_cvr_gain=float(row["expected_cvr_gain"]),
        support=float(row["support"]),
        confidence=float(row["confidence"]),
        lift=float(row["lift"]),
        strategy_score=float(row["strategy_score"]),
        reason=str(row["reason"]),
    )


def build_pipeline_snapshot(
    data: PipelineData | None = None,
    settings: Settings | None = None,
    top_n: int | None = None,
) -> PipelineSnapshot:
    config = settings or get_settings()
    n = top_n if top_n is not None else config.agent_top_n
    pipeline_data = data or load_pipeline_data(settings=config, top_n=n)

    ctr = float(pipeline_data.metrics.iloc[0]["ctr"])
    cvr = float(pipeline_data.metrics.iloc[0]["cvr"])
    ctcvr = float(pipeline_data.metrics.iloc[0]["ctcvr"])

    strategies: list[StrategyRecord] = []
    if not pipeline_data.strategies.empty:
        strategies = [_row_to_strategy(row) for _, row in pipeline_data.strategies.iterrows()]

    snapshot = PipelineSnapshot(
        log_path=str(pipeline_data.log_path),
        impression_count=pipeline_data.impression_count,
        user_count=pipeline_data.user_count,
        ctr=ctr,
        cvr=cvr,
        ctcvr=ctcvr,
        strategies=strategies,
    )
    logger.info("파이프라인 스냅샷 생성: strategies=%s", len(strategies))
    return snapshot
