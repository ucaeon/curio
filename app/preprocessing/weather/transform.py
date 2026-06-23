# raw JSON → 분석용 CSV 전처리
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SOURCE_COLUMNS = [
    "baseDate",
    "baseTime",
    "fcstDate",
    "fcstTime",
    "category",
    "fcstValue",
]

CATEGORY_FEATURE_MAP = {
    "TMP": "temperature",
    "SKY": "sky_status",
    "PTY": "precipitation_type",
    "POP": "precipitation_probability",
    "REH": "humidity",
    "WSD": "wind_speed",
}

SKY_STATUS_MAP = {
    "1": "clear",
    "3": "cloudy",
    "4": "overcast",
}

PRECIPITATION_TYPE_MAP = {
    "0": "none",
    "1": "rain",
    "2": "rain_snow",
    "3": "snow",
    "4": "shower",
}


def transform_weather(items: list[dict]) -> pd.DataFrame:
    # long format → wide format 피벗 후 feature 생성
    df = pd.DataFrame(items)

    for column in SOURCE_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[SOURCE_COLUMNS].copy()
    df = df[df["category"].isin(CATEGORY_FEATURE_MAP.keys())]

    pivot_df = df.pivot_table(
        index=["baseDate", "baseTime", "fcstDate", "fcstTime"],
        columns="category",
        values="fcstValue",
        aggfunc="first",
    ).reset_index()

    pivot_df.columns.name = None
    pivot_df = pivot_df.rename(
        columns={
            "baseDate": "base_date",
            "baseTime": "base_time",
            "fcstDate": "fcst_date",
            "fcstTime": "fcst_time",
            **CATEGORY_FEATURE_MAP,
        }
    )

    for col in CATEGORY_FEATURE_MAP.values():
        if col in pivot_df.columns:
            pivot_df[col] = pd.to_numeric(pivot_df[col], errors="coerce")

    if "sky_status" in pivot_df.columns:
        pivot_df["sky_status_name"] = (
            pivot_df["sky_status"].astype("Int64").astype(str).map(SKY_STATUS_MAP)
        )

    if "precipitation_type" in pivot_df.columns:
        pivot_df["precipitation_type_name"] = (
            pivot_df["precipitation_type"].astype("Int64").astype(str).map(PRECIPITATION_TYPE_MAP)
        )

    return pivot_df


def load_raw_json(raw_path: Path) -> list[dict]:
    # raw JSON 로드
    with raw_path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("raw JSON은 리스트 형식이어야 합니다")
    return data


def save_processed_weather(df: pd.DataFrame, output_dir: Path) -> Path:
    # data/processed/weather/ 에 CSV 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"weather_{timestamp}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("processed 저장 완료: %s (%s건)", output_path, len(df))
    return output_path


def transform_and_save(raw_path: Path, output_dir: Path) -> Path:
    # 전처리 + 저장 한 번에 실행
    items = load_raw_json(raw_path)
    df = transform_weather(items)
    return save_processed_weather(df, output_dir)
