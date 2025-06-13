from langchain.prompts.chat import ChatPromptTemplate
from .prompts import SHOP_SYSTEM_PROMPT
import datetime
from .tools.customer_tools import recommend_system, get_device_details, order_purchase, cancel_order, track_order,update_order
from schemas.device_schemas import CompleteOrEscalate
from ...utils.logging.logger import get_logger
logger = get_logger(__name__)


SHOP_SYSTEM_MESSAGES = [
    ("system", SHOP_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]
shop_assistant_prompt = ChatPromptTemplate.from_messages(SHOP_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)

shop_safe_tools = [recommend_system, get_device_details, track_order]
shop_sensitive_tools = [order_purchase, cancel_order,update_order]
shop_tools = shop_safe_tools + shop_sensitive_tools 

def create_shop_tool(model):
    """Creates a shop support tool with the provided language model.
    
    Args:
        model: The language model to use with the tool
        
    Returns:
        A runnable that can be used to handle shop support queries
    """
    logger.info("Creating shop support tools with the following capabilities:")
    logger.info(f"Safe tools: {[tool.__name__ for tool in shop_safe_tools]}")
    logger.info(f"Sensitive tools: {[tool.__name__ for tool in shop_sensitive_tools]}")
    
    shop_tools_runnable = shop_assistant_prompt | model.bind_tools(shop_tools + [CompleteOrEscalate])
    return shop_tools_runnable
