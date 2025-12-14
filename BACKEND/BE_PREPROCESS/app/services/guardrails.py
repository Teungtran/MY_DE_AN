
from pydantic import BaseModel, ConfigDict
from app.config.base_config import APP_CONFIG
from app.utils.logger.logger import get_logger
from langchain.prompts import ChatPromptTemplate
from typing import Literal, Annotated
from app.services.data_pipeline.chat_model.factory import create_chat_model

model = create_chat_model(APP_CONFIG.chat_model_config)
logger = get_logger(__name__)

class GuardrailVerificationError(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    result: Annotated[
        Literal["VALID DATA", "INVALID DATA"],
        "Result of guardrail verification indicating if the data is valid or invalid."
    ]
def data_guardrails(input_data:str, guardrails_prompt:str)-> dict:
    """
    Apply guardrails to the input data before processing.
    This function can be extended to include various checks and transformations.
    """
    
    logger.info("Applying guardrails to the input data.")
    GUARDRAILS_PROMPT = ChatPromptTemplate.from_messages([
        (("system", guardrails_prompt)),
        ("human", "{input_data}")
    ])
    verification = model.with_structured_output(schema=GuardrailVerificationError).invoke(GUARDRAILS_PROMPT.format_messages(input_data=input_data))
    return verification.model_dump(mode='json')
