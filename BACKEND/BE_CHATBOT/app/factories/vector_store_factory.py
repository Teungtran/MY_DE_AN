from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from config.base_config import BaseConfiguration, PolicyConfig, RecommendConfig

from .embedding_factory import create_embedding_model
from utils.logging.logger import get_logger

logger = get_logger(__name__)

def connect_to_policy_store(vector_store_config: PolicyConfig, embedding_model: Embeddings) -> VectorStore:


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
    
    logger.info(f"Created Qdrant vector store: {vector_store}")
    return vector_store

def connect_to_recommend_store(vector_store_config: RecommendConfig, embedding_model: Embeddings) -> VectorStore:


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
    
    logger.info(f"Created Qdrant vector store: {vector_store}")
    return vector_store

def create_policy_store(
    configuration: BaseConfiguration, *, embedding_model: Optional[Embeddings] = None
) -> VectorStore:
    """Create a retriever for the agent, based on the current configuration."""
    _embedding_model = (
        embedding_model if embedding_model else create_embedding_model(configuration.embedding_model_config)
    )
    config = configuration.vector_store_config
    match config:
        case PolicyConfig():
            return connect_to_policy_store(config, _embedding_model)

        case _:
            raise ValueError(f"Unsupported chat model provider: {type(config)}")
        
def create_recommend_store(
    configuration: BaseConfiguration, *, embedding_model: Optional[Embeddings] = None
) -> VectorStore:
    """Create a retriever for the agent, based on the current configuration."""
    _embedding_model = (
        embedding_model if embedding_model else create_embedding_model(configuration.embedding_model_config)
    )
    config = configuration.recommend_config
    match config:
        case RecommendConfig():
            return connect_to_recommend_store(config, _embedding_model)

        case _:
            raise ValueError(f"Unsupported chat model provider: {type(config)}")
