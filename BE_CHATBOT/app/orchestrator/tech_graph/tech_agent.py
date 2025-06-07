from langchain.prompts.chat import ChatPromptTemplate
from .prompts import TECH_SYSTEM_PROMPT
from .tools.customer_tools import recommend_system, get_device_details, order_purchase, cancel_order, track_order,book_appointment
from schemas.device_schemas import CompleteOrEscalate
from ...utils.logging.logger import get_logger
logger = get_logger(__name__)


TECH_SYSTEM_MESSAGES = [
    ("system", TECH_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]
import datetime
tech_assistant_prompt = ChatPromptTemplate.from_messages(TECH_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)

tech_safe_tools = [recommend_system, get_device_details, track_order]
tech_sensitive_tools = [order_purchase, cancel_order, book_appointment]
tech_tools = tech_safe_tools + tech_sensitive_tools 

def create_tech_tool(model):
    """Creates a tech support tool with the provided language model.
    
    Args:
        model: The language model to use with the tool
        
    Returns:
        A runnable that can be used to handle tech support queries
    """
    logger.info("Creating tech support tools with the following capabilities:")
    logger.info(f"Safe tools: {[tool.__name__ for tool in tech_safe_tools]}")
    logger.info(f"Sensitive tools: {[tool.__name__ for tool in tech_sensitive_tools]}")
    
    tech_tools_runnable = tech_assistant_prompt | model.bind_tools(tech_tools + [CompleteOrEscalate])
    return tech_tools_runnable
