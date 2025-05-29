from typing import Union

from langchain_core.language_models import BaseChatModel

from config.base_config import AzureOpenAIConfig


def create_azure_chat_model(chat_config: AzureOpenAIConfig) -> BaseChatModel:
    from langchain_openai import AzureChatOpenAI

    return AzureChatOpenAI(
        api_key=chat_config.api_key,
        azure_endpoint=chat_config.azure_endpoint,
        api_version=chat_config.api_version,
        azure_deployment=chat_config.azure_deployment,
        **(chat_config.kwargs if chat_config.kwargs else {}),
    )


def create_chat_model(chat_config: Union[AzureOpenAIConfig]) -> BaseChatModel:
    """Connect to the configured chat model (Azure)."""
    match chat_config:
        case AzureOpenAIConfig():
            return create_azure_chat_model(chat_config)

        case _:
            raise ValueError(f"Unsupported chat model provider: {type(chat_config)}")
