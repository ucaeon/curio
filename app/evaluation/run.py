# 골든셋 평가 CLI
import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from app.config.settings import get_settings
from app.evaluation.golden_cases import export_golden_cases, load_golden_cases
from app.evaluation.runner import run_golden_eval_suite

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Curio 골든셋 Agent 평가 (Langfuse trace)")
    parser.add_argument("--k", type=int, default=3, help="pass@k / pass^k k 값")
    parser.add_argument("--trials", type=int, default=3, help="케이스당 trial 횟수")
    parser.add_argument(
        "--case-id",
        action="append",
        default=None,
        help="특정 case_id만 실행 (반복 지정 가능)",
    )
    parser.add_argument(
        "--export-golden",
        action="store_true",
        help="골든셋 JSON만 생성하고 종료",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="평가 결과 JSON 저장 경로",
    )
    return parser


def _default_output_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return Path(f"data/eval/results/golden_eval_{stamp}.json")


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    args = _build_parser().parse_args()

    if args.export_golden:
        path = export_golden_cases()
        logger.info("골든셋 JSON 생성: %s (%s cases)", path, len(load_golden_cases(path)))
        return 0

    if not get_settings().openai_api_key:
        logger.error("OPENAI_API_KEY가 없습니다")
        return 1

    try:
        result = run_golden_eval_suite(
            k=args.k,
            trials=args.trials,
            case_ids=args.case_id,
        )
    except ValueError as error:
        logger.error("%s", error)
        return 1
    except Exception as error:
        logger.exception("골든셋 평가 실패: %s", error)
        return 1

    output_path = Path(args.output) if args.output else _default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "case_count": result.case_count,
                "k": result.k,
                "trials": result.trials,
                "pass_at_1": round(result.pass_at_1, 4),
                "pass_at_k": round(result.pass_at_k, 4),
                "pass_pow_k": round(result.pass_pow_k, 4),
                "result_path": str(output_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
