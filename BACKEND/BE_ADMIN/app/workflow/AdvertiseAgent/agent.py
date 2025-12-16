from agno.agent import Agent
from agno.models.openai import OpenAIChat
from .custom_tools.agent_tools import extract_url_content, draft_advertise_from_input
from agno.models.openai import OpenAIChat
from typing import Callable
from pydantic import SecretStr
from textwrap import dedent
from app.config.base_config import OpenAIConfig
from app.workflow.prompt import ADVERTISE_PROMPT,ROLE,GOAL

chat_config = OpenAIConfig()
api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()
    
    
advertise_expert =  Agent(
    name="AdvertiseExpert",
    role=ROLE,
    model=OpenAIChat(id="gpt-4.1-mini", api_key=api_key),
    tools=[extract_url_content, draft_advertise_from_input],
    instructions = dedent(ADVERTISE_PROMPT),
    goal=GOAL,
    show_tool_calls=True,
    markdown=True
    
)