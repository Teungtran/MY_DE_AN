import datetime
from langgraph.graph import END
from langgraph.prebuilt import tools_condition
from config.base_config import APP_CONFIG
from langchain_openai import ChatOpenAI
from schemas.device_schemas import CompleteOrEscalate
from langchain.prompts.chat import ChatPromptTemplate
from .prompts import MAIN_SYSTEM_PROMPT
from factories.chat_factory import create_chat_model
from ..internal_graph.tech_agent import create_tech_tool,tech_safe_tools
from ..internal_graph.state import ToTechAssistant
from ..research_graph.state import ToPolicyAssistant
from .state import AgenticState
from ..research_graph.policy_agent import create_policy_tool
chat_config = APP_CONFIG.chat_model_config
import os
if not chat_config:
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),   
        model="gpt-4o-mini",     
        temperature=0,
        max_tokens=3000
    )
else:
    llm = create_chat_model(chat_config)
MAIN_SYSTEM_MESSAGES = [
    ("system", MAIN_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]
primary_assistant_prompt = ChatPromptTemplate.from_messages(MAIN_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)



update_tech_runnable = create_tech_tool(llm)
update_policy_runnable = create_policy_tool(llm)
assistant_runnable = primary_assistant_prompt | llm.bind_tools([ToTechAssistant, ToPolicyAssistant])

def route_primary_assistant(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    
    last_message = state["messages"][-1] if state["messages"] else None
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_calls = last_message.tool_calls
        if tool_calls[0]["name"] == ToTechAssistant.__name__:
            return "enter_tech_node"
        elif tool_calls[0]["name"] == ToPolicyAssistant.__name__:
            return "enter_policy_node"
        return END
    
    return END

def route_update_tech(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in tech_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "update_tech_safe_tools"
    return "update_tech_sensitive_tools"

def route_policy_agent(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    return "policy_tool"

