# Langfuse trace 초기화·flush
import logging
import os

from langfuse import get_client

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def is_langfuse_enabled(settings: Settings | None = None) -> bool:
    if settings is not None:
        return bool(settings.langfuse_public_key and settings.langfuse_secret_key)
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def init_langfuse(settings: Settings | None = None) -> bool:
    config = settings or get_settings()
    if not is_langfuse_enabled(config):
        os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
        logger.info("Langfuse 비활성: PUBLIC_KEY 또는 SECRET_KEY 없음")
        return False

    os.environ["LANGFUSE_PUBLIC_KEY"] = config.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = config.langfuse_secret_key
    os.environ["LANGFUSE_BASE_URL"] = config.langfuse_base_url
    os.environ["LANGFUSE_TRACING_ENABLED"] = "true"
    logger.info("Langfuse trace 활성화")
    return True


def flush_langfuse() -> None:
    if not is_langfuse_enabled():
        return
    get_client().flush()
    logger.info("Langfuse flush 완료")
