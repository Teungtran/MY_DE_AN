from agno.agent import Agent
from agno.tools.sql import SQLTools
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from app.config.base_config import OpenAIConfig
from typing import Callable
from pydantic import SecretStr
import os
from pathlib import Path

chat_config = OpenAIConfig()
api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()

# Get SQLite database path (same logic as db.py)
def get_db_uri():
    """Get SQLite database connection string"""
    db_path = os.getenv("SQLITE_DB_PATH")
    
    if db_path:
        # Use environment variable (Docker or custom path)
        return f"sqlite:///{db_path}"
    else:
        # Default: Use shared location in BACKEND directory for local development
        backend_dir = Path(__file__).parent.parent.parent.parent.parent  # Navigate to BACKEND/
        shared_db = backend_dir / "shared_data" / "auth.db"
        shared_db.parent.mkdir(parents=True, exist_ok=True)  # Create directory if needed
        return f"sqlite:///{shared_db}"

sql_agent = Agent(
    name="sql_agent",
    model=OpenAIChat(id="gpt-4o-mini", api_key=api_key),
    role="Access to SQL DB, retrieve DB informations from user request",
    tools=[SQLTools(db_url=get_db_uri())],
    goal="Provide accurate, real-time information about the database based on user queries.",
    instructions="""
        You are a SQL assistant connected to an SQLite database. Follow these guidelines carefully:

        1. **Understand user intent**  
        - If the user asks for data, write and execute appropriate SELECT queries.  
        - If the user asks to change, add, or delete data, generate valid SQL (UPDATE, INSERT, DELETE).  

        2. **Be explicit about actions**  
        - Before making any changes, explain what you’re about to do.  
        - Example: “I will update the customer's name where id=3.”

        3. **Keep responses human-readable**  
        - Always display query results in a clean markdown table format.  
        - If no data is found, say “No results found.”

        4. **Be cautious with schema**  
        - Never drop tables or alter schemas unless the user explicitly requests it.  
        - For schema info, use PRAGMA or INFORMATION_SCHEMA queries as needed.

        5. **Ensure correctness**  
        - Write SQL statements compatible with SQLite syntax.
        - Validate column names and table names before executing.

        6. **Data persistence**  
        - Changes (INSERT/UPDATE/DELETE) are saved permanently in the database file.  
        - Confirm any successful modification.

        7. **Respect privacy & scope**  
        - Only interact with the connected database.  
        - Do not access external systems or files.
""",
    show_tool_calls=True,
    markdown=True,
)

