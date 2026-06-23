# 통합 feature dataset 및 synthetic log 생성 실행
import argparse
import logging
from pathlib import Path

from app.config.settings import get_settings
from app.io.paths import find_latest_csv, find_latest_prefixed_csv
from app.preprocessing.feature.build import (
    build_and_save_feature_dataset,
    load_processed_csv,
)
from app.preprocessing.feature.synthetic_log import generate_and_save_synthetic_log

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="feature dataset 및 synthetic log 생성")
    parser.add_argument("--events-path", type=Path, default=None, help="문화행사 processed CSV")
    parser.add_argument("--tour-path", type=Path, default=None, help="관광 processed CSV")
    parser.add_argument("--weather-path", type=Path, default=None, help="날씨 processed CSV")
    parser.add_argument("--creatives-path", type=Path, default=None, help="creatives feature CSV")
    parser.add_argument("--context-path", type=Path, default=None, help="context feature CSV")
    parser.add_argument("--skip-feature", action="store_true", help="기존 feature CSV 사용")
    parser.add_argument("--skip-synthetic", action="store_true", help="synthetic log 생성 생략")
    parser.add_argument("--n-impressions", type=int, default=10_000, help="생성할 노출 로그 건수")
    parser.add_argument("--n-users", type=int, default=500, help="synthetic 유저 수")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    features_dir = Path(settings.processed_features_dir)

    if args.skip_feature:
        creatives_path = args.creatives_path or find_latest_prefixed_csv(features_dir, "creatives")
        context_path = args.context_path or find_latest_prefixed_csv(features_dir, "context")
    else:
        events_path = args.events_path or find_latest_csv(Path(settings.processed_seoul_event_dir))
        tour_path = args.tour_path or find_latest_csv(Path(settings.processed_tour_dir))
        weather_path = args.weather_path or find_latest_csv(Path(settings.processed_weather_dir))
        creatives_path, context_path = build_and_save_feature_dataset(
            events_path=events_path,
            tour_path=tour_path,
            weather_path=weather_path,
            output_dir=features_dir,
        )

    logger.info("feature 입력: creatives=%s, context=%s", creatives_path, context_path)

    if args.skip_synthetic:
        logger.info("synthetic log 생성 생략")
        return

    creative_catalog = load_processed_csv(creatives_path)
    context_catalog = load_processed_csv(context_path)
    synthetic_path = generate_and_save_synthetic_log(
        creative_catalog=creative_catalog,
        context_catalog=context_catalog,
        output_dir=Path(settings.processed_synthetic_dir),
        n_impressions=args.n_impressions,
        n_users=args.n_users,
    )
    logger.info("완료: synthetic=%s", synthetic_path)


if __name__ == "__main__":
    main()
