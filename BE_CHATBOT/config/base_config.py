from pydantic_settings import BaseSettings
from typing import Optional

class MongoConfig(BaseSettings):
    url: str = "mongodb://localhost:27017"
    database: str = "langgraph"
    collection: str = "states"

class ChatModelConfig(BaseSettings):
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000

class AppConfig(BaseSettings):
    mongo_config: MongoConfig = MongoConfig()
    chat_model_config: Optional[ChatModelConfig] = None

APP_CONFIG = AppConfig() 