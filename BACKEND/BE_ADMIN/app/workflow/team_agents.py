from agno.models.openai import OpenAIChat
from agno.tools.reasoning import ReasoningTools
from agno.team.team import Team
from config.base_config import OpenAIConfig
from .prompt import TEAM_PROMPT
from .AdvertiseAgent.agent import advertise_expert
from .SearchAgent.agent import tavily_agent
from .SQLAgent.agent import sql_agent
from .ExpertAgent.agent import expert_agent
from .team_memory import get_storage
from typing import Callable
from pydantic import SecretStr
chat_config = OpenAIConfig()
api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()
    
memory,storage = get_storage()

store_team = Team(
    description = "A team of Store Manager Assistants that can answer questions related to store management and sales.",
    name="SAGE- R&D Supporting Team",
    model=OpenAIChat(id="gpt-4o-mini", api_key=api_key),
    mode="coordinate",
    tools=[ReasoningTools(add_instructions=True,think=True, analyze=True)],
    instructions=TEAM_PROMPT,
    members=[tavily_agent, sql_agent, expert_agent, advertise_expert],
    expected_output="A Markdown format answer that is clear for the user, using simple vocabulary",
    markdown=True,
    add_history_to_messages=True,
    num_history_runs=10,
    memory=memory,
    storage=storage,
    enable_user_memories=True,
    enable_agentic_memory=True,
    enable_session_summaries=True,
    enable_team_history=True,
    add_state_in_messages=True,
    add_session_summary_references=True,
    share_member_interactions=True,
    show_members_responses=True,
)