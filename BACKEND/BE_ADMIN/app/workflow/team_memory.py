from agno.models.openai import OpenAIChat
from agno.memory.v2.db.mongodb import MongoMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.agent.mongodb import MongoDbAgentStorage
from config.base_config import APP_CONFIG

DB_URL = APP_CONFIG.mongo_config.url
DB_NAME = APP_CONFIG.mongo_config.db_name
AGENT_MEMORY_COLLECTION = APP_CONFIG.mongo_config.memory_collection
STORE_COLLECTION = APP_CONFIG.mongo_config.store_collection
OPENAI_API_KEY = APP_CONFIG.chat_model_config.api_key
ID = APP_CONFIG.chat_model_config.model
def get_memory():
    memory_db = MongoMemoryDb(
        db_url=DB_URL,
        db_name=DB_NAME,
        collection_name=AGENT_MEMORY_COLLECTION)
    return memory_db
def get_storage():
    memory = Memory(model=OpenAIChat(id=ID,api_key=OPENAI_API_KEY), db=get_memory())
    storage = MongoDbAgentStorage(    
        db_url=DB_URL,
        db_name=DB_NAME,
        collection_name=STORE_COLLECTION)
    return memory,storage
