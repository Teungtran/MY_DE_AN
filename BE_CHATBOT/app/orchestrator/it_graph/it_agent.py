from langchain.prompts.chat import ChatPromptTemplate
from .prompts import IT_SYSTEM_PROMPT
from .tools.message import track_ticket,send_ticket,cancel_ticket,update_ticket
from schemas.device_schemas import CompleteOrEscalate
from .tools.it_support import it_support_agent
from ...utils.logging.logger import get_logger
logger = get_logger(__name__)


import datetime
IT_SYSTEM_MESSAGES = [
    ("system", IT_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]

it_assistant_prompt = ChatPromptTemplate.from_messages(IT_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)


it_safe_tools = [it_support_agent, track_ticket]
it_sensitive_tools = [send_ticket, cancel_ticket,update_ticket]
it_tools = it_safe_tools + it_sensitive_tools  

def create_it_tool(model):
    """Creates a it support tool with the provided language model.
    
    Args:
        model: The language model to use with the tool
        
    Returns:
        A runnable that can be used to handle it support queries
    """
    logger.info("Creating it support tools with the following capabilities:")
    logger.info(f"Safe tools: {[tool.__name__ for tool in it_safe_tools]}")
    logger.info(f"Sensitive tools: {[tool.__name__ for tool in it_sensitive_tools]}")
    
    it_tools_runnable = it_assistant_prompt | model.bind_tools(it_tools + [CompleteOrEscalate])
    return it_tools_runnable
