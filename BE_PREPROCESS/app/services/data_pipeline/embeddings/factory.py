from typing import Union

from langchain_core.embeddings import Embeddings

from config.base_config import EmbeddingConfig


def create_openai_embedding_model(embedding_config: EmbeddingConfig) -> Embeddings:
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        openai_api_key=embedding_config.api_key,
        model=embedding_config.model
    )


def create_embedding_model(embedding_config: Union[EmbeddingConfig]) -> Embeddings:
    """Connect to the configured text encoder."""
    match embedding_config:
        case EmbeddingConfig():
            return create_openai_embedding_model(embedding_config)
        case _:
            raise ValueError(f"Unsupported embedding provider: {type(embedding_config)}")
