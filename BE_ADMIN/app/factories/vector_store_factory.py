from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from config.base_config import BaseConfiguration, QdrantConfig

from .embedding_factory import create_embedding_model


def create_qdrant_vector_store(vector_store_config: QdrantConfig, embedding_model: Embeddings) -> VectorStore:
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

    # Connect to the Qdrant client
    qdrant_client = QdrantClient(
        url=vector_store_config.url,
        api_key=vector_store_config.api_key.get_secret_value(),
    )

    # Create the Qdrant vector store
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=vector_store_config.collection_name,
        embedding=embedding_model,
    )

    return vector_store


def create_vector_store(
    configuration: BaseConfiguration, *, embedding_model: Optional[Embeddings] = None
) -> VectorStore:
    """Create a retriever for the agent, based on the current configuration."""
    _embedding_model = (
        embedding_model if embedding_model else create_embedding_model(configuration.embedding_model_config)
    )
    # print(1111, _embedding_model)
    config = configuration.vector_store_config
    match config:
        case QdrantConfig():
            return create_qdrant_vector_store(config, _embedding_model)

        # case CosmosMongoDBConfig():
        #     return create_cosmos_vector_store(config, _embedding_model)

        # case AzureSearchConfig():
        #     return create_azure_search_vector_store(config, _embedding_model)

        case _:
            raise ValueError(f"Unsupported chat model provider: {type(config)}")
