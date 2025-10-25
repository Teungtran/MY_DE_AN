from langchain_community.utilities import SQLDatabase
from app.config.base_config import SQLConfig

def connect_to_db(server: str, database: str) -> SQLDatabase:
    """Connect to PostgreSQL database"""
    config = SQLConfig()
    
    DATABASE_URL = f"postgresql+psycopg2://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}?sslmode=require"
    
    return SQLDatabase.from_uri(DATABASE_URL)