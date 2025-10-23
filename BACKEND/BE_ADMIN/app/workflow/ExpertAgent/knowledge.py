
from agno.vectordb.qdrant import Qdrant
from agno.embedder.openai import OpenAIEmbedder
from typing import Callable
from pydantic import SecretStr

from app.config.base_config import EmbeddingConfig,APP_CONFIG
embedding_config = EmbeddingConfig()
api_key = embedding_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()

QDRANT_URL = APP_CONFIG.vector_store_config.url
QDRANT_API_KEY = APP_CONFIG.vector_store_config.api_key
COLLECTION = APP_CONFIG.vector_store_config.collection_name
embedder = OpenAIEmbedder(
    api_key=api_key,
    id=embedding_config.model
)
def get_vector_db():
    vector_db = Qdrant(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection=COLLECTION,
        embedder=embedder
    )
    return vector_db,embedder
