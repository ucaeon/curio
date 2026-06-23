# API 수집 후 raw JSON 저장
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.config.settings import Settings, get_settings
from app.ingestion.seoul_event.client import fetch_all

logger = logging.getLogger(__name__)


def save_raw_events(rows: list[dict], output_dir: Path) -> Path:
    # data/raw/seoul_event/ 에 JSON 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"seoul_events_{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)

    logger.info("raw 저장 완료: %s (%s건)", output_path, len(rows))
    return output_path


def fetch_and_save_raw(settings: Settings | None = None, limit: int | None = None) -> Path:
    # 수집 + 저장 한 번에 실행
    config = settings or get_settings()
    rows = fetch_all(config.seoul_api_key, limit=limit)
    return save_raw_events(rows, Path(config.raw_seoul_event_dir))
