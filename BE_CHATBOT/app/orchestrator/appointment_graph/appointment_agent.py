from langchain.prompts.chat import ChatPromptTemplate
from .prompts import APPOINTMENT_SYSTEM_PROMPT
from .tools.appointment_tool import book_appointment,track_appointment,cancel_appointment
from schemas.device_schemas import CompleteOrEscalate
from ...utils.logging.logger import get_logger
logger = get_logger(__name__)


APPOINTMENT_SYSTEM_MESSAGES = [
    ("system", APPOINTMENT_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]
import datetime
appointment_assistant_prompt = ChatPromptTemplate.from_messages(APPOINTMENT_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)

appointment_safe_tools = [track_appointment]
appointment_sensitive_tools = [book_appointment,cancel_appointment]
appointment_tools = appointment_safe_tools + appointment_sensitive_tools 

def create_appointment_tool(model):
    """Creates a appointment support tool with the provided language model.
    
    Args:
        model: The language model to use with the tool
        
    Returns:
        A runnable that can be used to handle appointment support queries
    """
    logger.info("Creating appointment support tools with the following capabilities:")
    logger.info(f"Safe tools: {[tool.__name__ for tool in appointment_safe_tools]}")
    logger.info(f"Sensitive tools: {[tool.__name__ for tool in appointment_sensitive_tools]}")
    
    appointment_tools_runnable = appointment_assistant_prompt | model.bind_tools(appointment_tools + [CompleteOrEscalate])
    return appointment_tools_runnable
