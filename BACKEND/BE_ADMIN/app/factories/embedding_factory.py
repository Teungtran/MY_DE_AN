from typing import Union, Callable

from langchain_core.embeddings import Embeddings
from pydantic import SecretStr

from config.base_config import EmbeddingConfig, OpenAIConfig


def create_openai_embedding_model(embedding_config: Union[EmbeddingConfig, OpenAIConfig]) -> Embeddings:
    from langchain_openai import OpenAIEmbeddings
    
    api_key = embedding_config.api_key
    if isinstance(api_key, Callable):  # If api_key is a function
        api_key = api_key()  # Call the function to get the value
    if isinstance(api_key, SecretStr):  # If api_key is a SecretStr
        api_key = api_key.get_secret_value()  # Get the string value

    return OpenAIEmbeddings(
        openai_api_key=api_key,
        model=embedding_config.model
    )


def create_embedding_model(embedding_config: Union[EmbeddingConfig, OpenAIConfig]) -> Embeddings:
    """Connect to the configured text encoder."""
    match embedding_config:
        case EmbeddingConfig() | OpenAIConfig():
            return create_openai_embedding_model(embedding_config)
        case _:
            raise ValueError(f"Unsupported embedding provider: {type(embedding_config)}")
