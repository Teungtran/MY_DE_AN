from typing import Union, Callable

from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

from config.base_config import OpenAIConfig


def create_openai_chat_model(chat_config: OpenAIConfig) -> BaseChatModel:
    from langchain_openai import ChatOpenAI
    
    api_key = chat_config.api_key
    if isinstance(api_key, Callable):  # If api_key is a function
        api_key = api_key()  # Call the function to get the value
    if isinstance(api_key, SecretStr):  # If api_key is a SecretStr
        api_key = api_key.get_secret_value()  # Get the string value
    
    # Prepare kwargs, only set parameters if not in kwargs
    kwargs = chat_config.kwargs or {}
    model_params = {
        "openai_api_key": api_key,
        "model": chat_config.model,
    }
    
    # Only add parameters if not already in kwargs
    if "temperature" not in kwargs:
        model_params["temperature"] = 0.0
        
    if "streaming" not in kwargs:
        model_params["streaming"] = False
        
    return ChatOpenAI(
        **model_params,
        **kwargs
    )


def create_chat_model(chat_config: Union[OpenAIConfig]) -> BaseChatModel:
    """Connect to the configured chat model (Azure)."""
    match chat_config:
        case OpenAIConfig():
            return create_openai_chat_model(chat_config)

        case _:
            raise ValueError(f"Unsupported chat model provider: {type(chat_config)}")
