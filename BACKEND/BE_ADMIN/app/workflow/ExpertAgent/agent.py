from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge.agent import AgentKnowledge
from .knowledge import get_vector_db
from config.base_config import OpenAIConfig
from .prompt import PROMPT
from textwrap import dedent
from typing import Callable
from pydantic import SecretStr
chat_config = OpenAIConfig()
api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()
vector_db,embedder = get_vector_db()


expert_agent = Agent(
    name="ExpertAgent",
    role="Act as a Marketing, Sales, and eCommerce strategist, offering expert advice to help stores grow and succeed.",
    model=OpenAIChat(
        id=chat_config.id, 
        api_key=api_key
    ),
    knowledge=AgentKnowledge(
    vector_db=vector_db,
    num_documents=10,
    optimize_on=100
    
    ),
    instructions=dedent(PROMPT),
    goal="Provide strategic, practical advice to help stores grow and succeed.",
    show_tool_calls=True,
    search_knowledge=True,
)