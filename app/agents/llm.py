# OpenAI LLM 팩토리
from langchain_openai import ChatOpenAI

from app.config.settings import Settings, get_settings


def get_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    config = settings or get_settings()
    return ChatOpenAI(
        api_key=config.openai_api_key,
        model=config.openai_model,
        temperature=0.2,
    )
