# processed CSV → 통합 feature dataset
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

CREATIVE_COLUMNS = [
    "creative_id",
    "creative_type",
    "title",
    "district",
    "category",
    "season",
    "month",
    "weekday",
    "is_free",
    "has_image",
    "has_website",
    "latitude",
    "longitude",
]

CONTEXT_COLUMNS = [
    "context_id",
    "base_date",
    "base_time",
    "fcst_date",
    "fcst_time",
    "temperature",
    "sky_status",
    "sky_status_name",
    "precipitation_probability",
    "precipitation_type",
    "precipitation_type_name",
    "humidity",
    "wind_speed",
]


def load_processed_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def build_event_creatives(events_df: pd.DataFrame) -> pd.DataFrame:
    # 문화행사 processed → creative 스키마 정규화
    df = events_df.copy()
    df["creative_id"] = [f"event_{index:06d}" for index in range(len(df))]
    df["creative_type"] = "event"
    df["district"] = df["guname"]
    df["category"] = df["codename"]
    df["latitude"] = pd.to_numeric(df["lat"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["lot"], errors="coerce")
    return df[CREATIVE_COLUMNS]


def build_tour_creatives(tour_df: pd.DataFrame) -> pd.DataFrame:
    # 관광 processed → creative 스키마 정규화
    df = tour_df.copy()
    df["creative_id"] = df["content_id"].apply(lambda value: f"tour_{int(value)}")
    df["creative_type"] = "tour"
    df["category"] = df["content_type_name"]
    df["season"] = None
    df["month"] = None
    df["weekday"] = None
    df["is_free"] = None
    df["has_website"] = None
    return df[CREATIVE_COLUMNS]


def build_creative_catalog(events_df: pd.DataFrame, tour_df: pd.DataFrame) -> pd.DataFrame:
    # event + tour creative 카탈로그 통합
    event_creatives = build_event_creatives(events_df)
    tour_creatives = build_tour_creatives(tour_df)
    catalog = pd.concat([event_creatives, tour_creatives], ignore_index=True)
    catalog = catalog.drop_duplicates(subset=["creative_id"]).reset_index(drop=True)
    return catalog


def build_context_catalog(weather_df: pd.DataFrame) -> pd.DataFrame:
    # 날씨 processed → context 카탈로그 정규화
    df = weather_df.copy()
    df["context_id"] = df.apply(
        lambda row: f"{row['fcst_date']}_{row['fcst_time']}",
        axis=1,
    )
    for column in CONTEXT_COLUMNS:
        if column not in df.columns:
            df[column] = None
    return df[CONTEXT_COLUMNS].drop_duplicates(subset=["context_id"]).reset_index(drop=True)


def build_feature_dataset(
    events_path: Path,
    tour_path: Path,
    weather_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # processed CSV 3종 로드 후 creative·context 카탈로그 생성
    events_df = load_processed_csv(events_path)
    tour_df = load_processed_csv(tour_path)
    weather_df = load_processed_csv(weather_path)

    creative_catalog = build_creative_catalog(events_df, tour_df)
    context_catalog = build_context_catalog(weather_df)

    logger.info(
        "feature dataset 생성: creatives=%s건, context=%s건",
        len(creative_catalog),
        len(context_catalog),
    )
    return creative_catalog, context_catalog


def save_feature_dataset(
    creative_catalog: pd.DataFrame,
    context_catalog: pd.DataFrame,
    output_dir: Path,
) -> tuple[Path, Path]:
    # 통합 feature dataset CSV 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    creatives_path = output_dir / f"creatives_{timestamp}.csv"
    context_path = output_dir / f"context_{timestamp}.csv"

    creative_catalog.to_csv(creatives_path, index=False, encoding="utf-8")
    context_catalog.to_csv(context_path, index=False, encoding="utf-8")

    logger.info("creatives 저장 완료: %s (%s건)", creatives_path, len(creative_catalog))
    logger.info("context 저장 완료: %s (%s건)", context_path, len(context_catalog))
    return creatives_path, context_path


def build_and_save_feature_dataset(
    events_path: Path,
    tour_path: Path,
    weather_path: Path,
    output_dir: Path,
) -> tuple[Path, Path]:
    # 통합 feature dataset 생성 + 저장
    creative_catalog, context_catalog = build_feature_dataset(
        events_path=events_path,
        tour_path=tour_path,
        weather_path=weather_path,
    )
    return save_feature_dataset(creative_catalog, context_catalog, output_dir)
