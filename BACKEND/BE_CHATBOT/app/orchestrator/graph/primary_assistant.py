import datetime
from langchain_core.runnables import RunnableLambda
from .state import AgenticState
from langgraph.graph import END
from langgraph.prebuilt import tools_condition
from config.base_config import APP_CONFIG
from langchain_openai import ChatOpenAI
from schemas.device_schemas import CompleteOrEscalate
from langchain.prompts.chat import ChatPromptTemplate
from .prompts import MAIN_SYSTEM_PROMPT
from factories.chat_factory import create_chat_model
from ..shop_graph.shop_agent import create_shop_tool, shop_safe_tools
from ..shop_graph.state import ToShopAssistant
from ..rag_tool.tools.policy_tool import RAG_Agent
from ..web_crawler.tool import url_extraction, url_followup

from ..appointment_graph.state import ToAppointmentAssistant
from ..appointment_graph.appointment_agent  import create_appointment_tool , appointment_safe_tools
from ..it_graph.state import ToITAssistant
from ..it_graph.it_agent import create_it_tool, it_safe_tools
from .tools.support_nodes import inject_user_info
chat_config = APP_CONFIG.chat_model_config
import os
from utils.logging.logger import get_logger
logger = get_logger(__name__)

if not chat_config:
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),   
        model="gpt-4o-mini",     
        temperature=0,
        max_tokens=3000
    )
else:
    llm = create_chat_model(chat_config)
    
def assistant_runnable_with_user_info(state):
    result = (primary_assistant_prompt | llm.bind_tools([ToShopAssistant, ToAppointmentAssistant, ToITAssistant, RAG_Agent, url_extraction, url_followup])).invoke(state)
    return inject_user_info(state, result)

MAIN_SYSTEM_MESSAGES = [
    ("system", MAIN_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]
primary_assistant_prompt = ChatPromptTemplate.from_messages(MAIN_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)
update_shop_runnable = create_shop_tool(llm)
update_appointment_runnable = create_appointment_tool(llm)
update_it_runnable = create_it_tool(llm)
assistant_runnable = RunnableLambda(assistant_runnable_with_user_info)

def route_primary_assistant(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    
    last_message = state["messages"][-1] if state["messages"] else None
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_calls = last_message.tool_calls
        tool_name = tool_calls[0]["name"]
        
        if tool_name == ToShopAssistant.__name__:
            return "enter_shop_node"
        elif tool_name == ToAppointmentAssistant.__name__:
            return "enter_appointment_node"
        elif tool_name == ToITAssistant.__name__:
            return "enter_it_node"
        elif tool_name == "rag_agent":
            return "rag_agent_node"
        elif tool_name == "url_extraction":
            return "url_agent_node"
        elif tool_name == "url_followup":
            return "url_followup_node"
        return END
    
    return END

def route_update_shop(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in shop_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "update_shop_safe_tools"
    return "update_shop_sensitive_tools"

def route_update_appointment(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in appointment_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "update_appointment_safe_tools"
    return "update_appointment_sensitive_tools"


def route_update_it(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in it_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "update_it_safe_tools"
    return "update_it_sensitive_tools"
