# Langfuse trace 단위 테스트
import os

from app.config.settings import Settings
from app.monitoring.langfuse_trace import flush_langfuse, init_langfuse, is_langfuse_enabled


def _settings_with_langfuse() -> Settings:
    return Settings(
        seoul_api_key="test",
        tour_api_key="test",
        weather_api_key="test",
        openai_api_key="test",
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
    )


def test_is_langfuse_disabled_without_keys(monkeypatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    settings = Settings(
        seoul_api_key="test",
        tour_api_key="test",
        weather_api_key="test",
        openai_api_key="test",
        langfuse_public_key="",
        langfuse_secret_key="",
    )
    assert is_langfuse_enabled(settings) is False


def test_is_langfuse_enabled_with_keys() -> None:
    assert is_langfuse_enabled(_settings_with_langfuse()) is True


def test_init_langfuse_sets_env(monkeypatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_TRACING_ENABLED", raising=False)

    enabled = init_langfuse(_settings_with_langfuse())
    assert enabled is True
    assert os.environ["LANGFUSE_PUBLIC_KEY"] == "pk-test"
    assert os.environ["LANGFUSE_TRACING_ENABLED"] == "true"


def test_flush_langfuse_noop_when_disabled() -> None:
    flush_langfuse()
