# prompts 폴더 로더
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = PROJECT_ROOT / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        msg = f"프롬프트 파일 없음: {path}"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8").strip()
