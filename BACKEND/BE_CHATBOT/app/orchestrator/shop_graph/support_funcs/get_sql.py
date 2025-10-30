from langchain_community.utilities import SQLDatabase
import os
from pathlib import Path

def connect_to_db(server: str, database: str) -> SQLDatabase:
    """Connect to local SQLite database used by chatbot"""
    db_path = os.getenv("SQLITE_DB_PATH")
    
    if db_path:
        DATABASE_URL = f"sqlite:///{db_path}"
    else:
        # Use shared location in BACKEND directory for local development
        backend_dir = Path(__file__).parent.parent.parent.parent.parent.parent  # Navigate to BACKEND/
        shared_db = backend_dir / "shared_data" / "auth.db"
        DATABASE_URL = f"sqlite:///{shared_db}"
    
    return SQLDatabase.from_uri(DATABASE_URL)