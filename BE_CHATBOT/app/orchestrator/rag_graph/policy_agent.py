from langchain.prompts.chat import ChatPromptTemplate
from .prompts import POLICY_SYSTEM_PROMPT
from .tools.policy_tool import recall_memory,RAG_Agent
from schemas.device_schemas import CompleteOrEscalate
from .tools.it_support import it_support_agent
from ...utils.logging.logger import get_logger
logger = get_logger(__name__)


import datetime
POLICY_SYSTEM_MESSAGES = [
    ("system", POLICY_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]

policy_assistant_prompt = ChatPromptTemplate.from_messages(POLICY_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)


# Use the modified RAG Agent
tools = [RAG_Agent,it_support_agent, recall_memory]

def create_policy_tool(model):
    """Creates a policy tool with the provided language model.
    
    Args:
        model: The language model to use with the tool
        
    Returns:
        A runnable that can be used to answer policy questions
    """
    logger.info("Creating policy tools with the following capabilities:")
    logger.info(f"Available tools: {[tool.__name__ for tool in tools]}")
    
    policy_tools_runnable = policy_assistant_prompt | model.bind_tools(tools + [CompleteOrEscalate])
    return policy_tools_runnable