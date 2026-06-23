# API 수집 후 raw JSON 저장
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.config.settings import Settings, get_settings
from app.ingestion.weather.client import fetch_all

logger = logging.getLogger(__name__)


def save_raw_weather(items: list[dict], output_dir: Path) -> Path:
    # data/raw/weather/ 에 JSON 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"weather_{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(items, file, ensure_ascii=False, indent=2)

    logger.info("raw 저장 완료: %s (%s건)", output_path, len(items))
    return output_path


def fetch_and_save_raw(settings: Settings | None = None, limit: int | None = None) -> Path:
    # 수집 + 저장 한 번에 실행
    config = settings or get_settings()
    items = fetch_all(
        api_key=config.weather_api_key,
        nx=config.weather_nx,
        ny=config.weather_ny,
        limit=limit,
    )
    return save_raw_weather(items, Path(config.raw_weather_dir))
