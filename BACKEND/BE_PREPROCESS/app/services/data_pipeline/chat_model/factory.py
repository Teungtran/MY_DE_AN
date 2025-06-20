from typing import Union

from langchain_core.language_models import BaseChatModel

from config.base_config import OpenAIConfig


def create_openai_chat_model(chat_config: OpenAIConfig) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    # Add temperature=0.0 for deterministic outputs (uses fewer tokens)
    # Add streaming=False to ensure complete responses without overhead
    return ChatOpenAI(
        openai_api_key=chat_config.api_key,
        model=chat_config.model,
        temperature=0.0,
        streaming=False,
        **(chat_config.kwargs if chat_config.kwargs else {}),
    )


def create_chat_model(chat_config: Union[OpenAIConfig]) -> BaseChatModel:
    """Connect to the configured chat model (Azure)."""
    match chat_config:
        case OpenAIConfig():
            return create_openai_chat_model(chat_config)

        case _:
            raise ValueError(f"Unsupported chat model provider: {type(chat_config)}")
