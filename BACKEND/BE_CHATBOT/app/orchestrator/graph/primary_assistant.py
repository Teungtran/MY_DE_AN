import datetime
from langchain_core.runnables import RunnableLambda
from .state import AgenticState
from langgraph.graph import END
from langgraph.prebuilt import tools_condition
from app.config.base_config import APP_CONFIG
from langchain_openai import ChatOpenAI
from app.schemas.device_schemas import CompleteOrEscalate
from langchain.prompts.chat import ChatPromptTemplate
from app.orchestrator.graph.prompts import MAIN_SYSTEM_PROMPT
from app.factories.chat_factory import create_chat_model
from ..shop_graph.shop_agent import create_shop_tool, shop_safe_tools
from ..shop_graph.state import ToShopAssistant
from ..rag_tool.tools.policy_tool import RAG_Agent
from ..web_crawler.tool import url_extraction, url_followup
from textwrap import dedent
from ..appointment_graph.state import ToAppointmentAssistant
from ..appointment_graph.appointment_agent  import create_appointment_tool , appointment_safe_tools
from ..it_graph.state import ToITAssistant
from ..it_graph.it_agent import create_it_tool, it_safe_tools
from .tools.support_nodes import inject_user_info
chat_config = APP_CONFIG.chat_model_config
import os
from app.utils.logging.logger import get_logger
logger = get_logger(__name__)

if not chat_config:
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),   
        model="gpt-4.1-mini",     
        temperature=0,
        max_tokens=3000
    )
else:
    llm = create_chat_model(chat_config)
    
def assistant_runnable_with_user_info(state):
    result = (primary_assistant_prompt | llm.bind_tools([ToShopAssistant, ToAppointmentAssistant, ToITAssistant, RAG_Agent, url_extraction, url_followup])).invoke(state)
    return inject_user_info(state, result)

MAIN_SYSTEM_MESSAGES = [
    ("system", dedent(MAIN_SYSTEM_PROMPT).strip()),
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
        logger.info("[ROUTING] Primary assistant routing to END (no tool calls)")
        return END
    
    last_message = state["messages"][-1] if state["messages"] else None
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_calls = last_message.tool_calls
        tool_name = tool_calls[0]["name"]
        tool_args = tool_calls[0].get("args", {})
        
        conversation_id = state.get("conversation_id", "N/A")
        user_id = state.get("user_id", "N/A")
        
        if tool_name == ToShopAssistant.__name__:
            logger.info(
                f"[ROUTING] Primary assistant routing to Shop Assistant | "
                f"Conversation ID: {conversation_id} | "
                f"User ID: {user_id} | "
                f"Tool args: {tool_args}"
            )
            return "enter_shop_node"
        elif tool_name == ToAppointmentAssistant.__name__:
            logger.info(
                f"[ROUTING] Primary assistant routing to Appointment Assistant | "
                f"Conversation ID: {conversation_id} | "
                f"User ID: {user_id} | "
                f"Tool args: {tool_args}"
            )
            return "enter_appointment_node"
        elif tool_name == ToITAssistant.__name__:
            logger.info(
                f"[ROUTING] Primary assistant routing to IT Assistant | "
                f"Conversation ID: {conversation_id} | "
                f"User ID: {user_id} | "
                f"Tool args: {tool_args}"
            )
            return "enter_it_node"
        elif tool_name == "rag_agent":
            logger.info(
                f"[ROUTING] Primary assistant routing to RAG Agent tool | "
                f"Conversation ID: {conversation_id} | "
                f"User ID: {user_id} | "
                f"Tool args: {tool_args}"
            )
            return "rag_agent_node"
        elif tool_name == "url_extraction":
            logger.info(
                f"[ROUTING] Primary assistant routing to URL Extraction tool | "
                f"Conversation ID: {conversation_id} | "
                f"User ID: {user_id} | "
                f"Tool args: {tool_args}"
            )
            return "url_agent_node"
        elif tool_name == "url_followup":
            logger.info(
                f"[ROUTING] Primary assistant routing to URL Followup tool | "
                f"Conversation ID: {conversation_id} | "
                f"User ID: {user_id} | "
                f"Tool args: {tool_args}"
            )
            return "url_followup_node"
        
        logger.warning(
            f"[ROUTING] Primary assistant received unknown tool: {tool_name} | "
            f"Conversation ID: {conversation_id}"
        )
        return END
    
    logger.info("[ROUTING] Primary assistant routing to END (no valid tool calls)")
    return END

def route_update_shop(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        logger.info("[ROUTING] Shop Assistant routing to END (no tool calls)")
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    conversation_id = state.get("conversation_id", "N/A")
    user_id = state.get("user_id", "N/A")
    
    # Log all tool calls
    tool_names = [tc.get("name", "unknown") for tc in tool_calls]
    logger.info(
        f"[ROUTING] Shop Assistant tool calls: {tool_names} | "
        f"Conversation ID: {conversation_id} | "
        f"User ID: {user_id}"
    )
    
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        logger.info(
            f"[ROUTING] Shop Assistant routing to leave_skill (CompleteOrEscalate called) | "
            f"Conversation ID: {conversation_id}"
        )
        return "leave_skill"
    
    safe_toolnames = [t.name for t in shop_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        logger.info(
            f"[ROUTING] Shop Assistant routing to update_shop_safe_tools | "
            f"Tools: {tool_names} | "
            f"Conversation ID: {conversation_id}"
        )
        return "update_shop_safe_tools"
    
    logger.info(
        f"[ROUTING] Shop Assistant routing to update_shop_sensitive_tools | "
        f"Tools: {tool_names} | "
        f"Conversation ID: {conversation_id}"
    )
    return "update_shop_sensitive_tools"

def route_update_appointment(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        logger.info("[ROUTING] Appointment Assistant routing to END (no tool calls)")
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    conversation_id = state.get("conversation_id", "N/A")
    user_id = state.get("user_id", "N/A")
    
    # Log all tool calls
    tool_names = [tc.get("name", "unknown") for tc in tool_calls]
    logger.info(
        f"[ROUTING] Appointment Assistant tool calls: {tool_names} | "
        f"Conversation ID: {conversation_id} | "
        f"User ID: {user_id}"
    )
    
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        logger.info(
            f"[ROUTING] Appointment Assistant routing to leave_skill (CompleteOrEscalate called) | "
            f"Conversation ID: {conversation_id}"
        )
        return "leave_skill"
    
    safe_toolnames = [t.name for t in appointment_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        logger.info(
            f"[ROUTING] Appointment Assistant routing to update_appointment_safe_tools | "
            f"Tools: {tool_names} | "
            f"Conversation ID: {conversation_id}"
        )
        return "update_appointment_safe_tools"
    
    logger.info(
        f"[ROUTING] Appointment Assistant routing to update_appointment_sensitive_tools | "
        f"Tools: {tool_names} | "
        f"Conversation ID: {conversation_id}"
    )
    return "update_appointment_sensitive_tools"


def route_update_it(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        logger.info("[ROUTING] IT Assistant routing to END (no tool calls)")
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    conversation_id = state.get("conversation_id", "N/A")
    user_id = state.get("user_id", "N/A")
    
    # Log all tool calls
    tool_names = [tc.get("name", "unknown") for tc in tool_calls]
    logger.info(
        f"[ROUTING] IT Assistant tool calls: {tool_names} | "
        f"Conversation ID: {conversation_id} | "
        f"User ID: {user_id}"
    )
    
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        logger.info(
            f"[ROUTING] IT Assistant routing to leave_skill (CompleteOrEscalate called) | "
            f"Conversation ID: {conversation_id}"
        )
        return "leave_skill"
    
    safe_toolnames = [t.name for t in it_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        logger.info(
            f"[ROUTING] IT Assistant routing to update_it_safe_tools | "
            f"Tools: {tool_names} | "
            f"Conversation ID: {conversation_id}"
        )
        return "update_it_safe_tools"
    
    logger.info(
        f"[ROUTING] IT Assistant routing to update_it_sensitive_tools | "
        f"Tools: {tool_names} | "
        f"Conversation ID: {conversation_id}"
    )
    return "update_it_sensitive_tools"
