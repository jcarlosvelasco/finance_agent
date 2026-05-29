import os

from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from src.settings import settings


class SentimentResponse(BaseModel):
    sentiment: str
    key_events: list[str]


def get_llm() -> BaseChatModel:
    CHAT_MODEL = settings.generator_model
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "mock":
        return GenericFakeChatModel(
            messages=iter(
                [AIMessage(content="This is a mock response for CI testing.")]
            )
        )
    return ChatOllama(model=CHAT_MODEL, temperature=0, base_url=OLLAMA_BASE_URL)
