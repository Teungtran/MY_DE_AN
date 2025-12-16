from agno.models.openai import OpenAIChat
from typing import Callable
from pydantic import SecretStr
from agno.agent import Agent
from app.workflow.AdvertiseAgent.custom_tools.tool_schema import InferredDeviceType
from app.config.base_config import OpenAIConfig
chat_config = OpenAIConfig()
api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()

get_type = Agent(
    model=OpenAIChat(
        id="gpt-4.1-mini", 
        api_key=api_key
    ),
    name="get_type",
    description="Get the type of the device",
    response_model=InferredDeviceType,
    use_json_mode=True)
