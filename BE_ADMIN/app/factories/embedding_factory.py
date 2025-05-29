from typing import Union

from langchain_core.embeddings import Embeddings

from config.base_config import AzureOpenAIConfig


def create_azure_embedding_model(embedding_config: AzureOpenAIConfig) -> Embeddings:
    from langchain_openai import AzureOpenAIEmbeddings

    return AzureOpenAIEmbeddings(
        api_key=embedding_config.api_key,
        azure_endpoint=embedding_config.azure_endpoint,
        api_version=embedding_config.api_version,
        azure_deployment=embedding_config.azure_deployment,
        **(embedding_config.kwargs if embedding_config.kwargs else {}),
    )


def create_embedding_model(embedding_config: Union[AzureOpenAIConfig]) -> Embeddings:
    """Connect to the configured text encoder."""
    match embedding_config:
        case AzureOpenAIConfig():
            return create_azure_embedding_model(embedding_config)
        case _:
            raise ValueError(f"Unsupported embedding provider: {type(embedding_config)}")
