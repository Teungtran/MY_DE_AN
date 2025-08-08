from agno.agent import Agent
from agno.models.openai import OpenAIChat

from agno.tools.tavily import TavilyTools
from config.base_config import OpenAIConfig, APP_CONFIG
from .prompt import PROMPT
from typing import Callable
from textwrap import dedent
from pydantic import SecretStr
chat_config = OpenAIConfig()
api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()
    
TAVILY_API_KEY = APP_CONFIG.search_config.api_key
if isinstance(TAVILY_API_KEY, Callable):
    TAVILY_API_KEY = TAVILY_API_KEY()  
if isinstance(TAVILY_API_KEY, SecretStr):  
    TAVILY_API_KEY = TAVILY_API_KEY.get_secret_value()

tavily_agent = Agent(
    name="TavilyAgent",
    role="Access to Internet, retrieve latest informations from user request",
    model=OpenAIChat(id="gpt-4o-mini", api_key=api_key),
    tools=[TavilyTools(api_key=TAVILY_API_KEY)],
    instructions=dedent(PROMPT),
    goal="Provide accurate, real-time information",
    show_tool_calls=True
)