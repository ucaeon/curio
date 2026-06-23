# processed CSV 경로 탐색
from pathlib import Path


def find_latest_csv(input_dir: Path) -> Path:
    csv_files = sorted(input_dir.glob("*.csv"), key=lambda path: path.stat().st_mtime)
    if not csv_files:
        raise FileNotFoundError(f"CSV 파일이 없습니다: {input_dir}")
    return csv_files[-1]


def find_latest_prefixed_csv(input_dir: Path, prefix: str) -> Path:
    csv_files = sorted(
        input_dir.glob(f"{prefix}_*.csv"),
        key=lambda path: path.stat().st_mtime,
    )
    if not csv_files:
        raise FileNotFoundError(f"{prefix}_*.csv 파일이 없습니다: {input_dir}")
    return csv_files[-1]
