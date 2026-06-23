# .env 기반 애플리케이션 설정
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 문화행사 API 설정
    seoul_api_key: str
    raw_seoul_event_dir: str = "data/raw/seoul_event"
    processed_seoul_event_dir: str = "data/processed/seoul_event"
    seoul_event_page_size: int = 1000

    # 관광지 API 설정
    tour_api_key: str
    raw_tour_dir: str = "data/raw/tour"
    processed_tour_dir: str = "data/processed/tour"
    tour_page_size: int = 1000

    # 날씨 API 설정
    weather_api_key: str
    raw_weather_dir: str = "data/raw/weather"
    processed_weather_dir: str = "data/processed/weather"
    weather_nx: int = 60
    weather_ny: int = 127

    # feature engineering 설정
    processed_features_dir: str = "data/processed/features"
    processed_synthetic_dir: str = "data/processed/synthetic"

    # Agent (OpenAI)
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    agent_top_n: int = 5
    agent_result_path: str = "data/processed/agent/run_latest.json"

    # Langfuse (LLM 모니터링, 선택)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"


def get_settings() -> Settings:
    return Settings()
