from agno.agent import Agent
from agno.models.openai import OpenAIChat
from config.base_config import OpenAIConfig
from .get_db import db_url
from agno.tools.sql import SQLTools
from typing import Callable
from pydantic import SecretStr
from .prompt import PROMPT
chat_config = OpenAIConfig()
api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()
    

sql_agent = Agent(   
            name="SQLAgent",
            role="Access to a SQL Server database, retrieve data and insight from user request", 
            model=OpenAIChat(id="gpt-4o-mini",api_key=api_key),
            tools=[SQLTools(db_url=db_url,run_sql_query=True)],
            instructions=PROMPT,
            goal="Provide accurate data with SQL query",
            show_tool_calls=True
)
