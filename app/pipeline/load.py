# 파이프라인 데이터 로딩
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.analytics.metrics import compute_metrics
from app.config.settings import Settings, get_settings
from app.io.paths import find_latest_prefixed_csv
from app.preprocessing.feature.build import load_processed_csv
from app.strategy.engine import STRATEGY_COLUMNS, generate_top_strategies

logger = logging.getLogger(__name__)

TOP_N_DEFAULT = 5


@dataclass(frozen=True)
class PipelineData:
    log_path: Path
    creatives_path: Path
    log_df: pd.DataFrame
    metrics: pd.DataFrame
    strategies: pd.DataFrame
    impression_count: int
    user_count: int


DashboardData = PipelineData


def load_pipeline_data(
    settings: Settings | None = None,
    top_n: int = TOP_N_DEFAULT,
) -> PipelineData:
    config = settings or get_settings()
    features_dir = Path(config.processed_features_dir)
    synthetic_dir = Path(config.processed_synthetic_dir)

    log_path = find_latest_prefixed_csv(synthetic_dir, "synthetic_log")
    creatives_path = find_latest_prefixed_csv(features_dir, "creatives")

    log_df = pd.read_csv(log_path)
    creatives_df = load_processed_csv(creatives_path)
    metrics = compute_metrics(log_df)
    strategies = generate_top_strategies(log_df, creatives_df, top_n=top_n)

    if not strategies.empty:
        strategies = strategies[STRATEGY_COLUMNS]

    impression_count = len(log_df)
    user_count = int(log_df["user_id"].nunique()) if "user_id" in log_df.columns else 0

    logger.info(
        "파이프라인 데이터 로딩: impressions=%s, strategies=%s",
        impression_count,
        len(strategies),
    )
    return PipelineData(
        log_path=log_path,
        creatives_path=creatives_path,
        log_df=log_df,
        metrics=metrics,
        strategies=strategies,
        impression_count=impression_count,
        user_count=user_count,
    )


def load_dashboard_data(
    settings: Settings | None = None,
    top_n: int = TOP_N_DEFAULT,
) -> PipelineData:
    return load_pipeline_data(settings=settings, top_n=top_n)
