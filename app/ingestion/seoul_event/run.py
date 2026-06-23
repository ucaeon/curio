# 문화행사 수집·전처리 실행
import argparse
import logging
from pathlib import Path

from app.config.settings import get_settings
from app.ingestion.seoul_event.fetch import fetch_and_save_raw
from app.preprocessing.seoul_event.transform import transform_and_save

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="서울시 문화행사 수집 및 전처리")
    parser.add_argument("--limit", type=int, default=None, help="수집 건수 제한")
    parser.add_argument("--skip-fetch", action="store_true", help="raw 파일만 전처리")
    parser.add_argument("--raw-path", type=Path, default=None, help="전처리할 raw JSON 경로")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    if args.skip_fetch:
        if args.raw_path is None:
            raise ValueError("--skip-fetch 시 --raw-path 필요")
        raw_path = args.raw_path
    else:
        raw_path = fetch_and_save_raw(settings=settings, limit=args.limit)

    processed_path = transform_and_save(
        raw_path=raw_path,
        output_dir=Path(settings.processed_seoul_event_dir),
    )
    logger.info("완료: raw=%s, processed=%s", raw_path, processed_path)


if __name__ == "__main__":
    main()
