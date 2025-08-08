from pandasai import SmartDataframe
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from config.base_config import OpenAIConfig
from typing import Callable, Optional
import pandas as pd
from textwrap import dedent
from .prompt import PANDAS_PROMPT, ANALYSE_PROMPT
from .parse_file import import_data
from pydantic import SecretStr
chat_config = OpenAIConfig()
api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()
def ai_model():
    return ChatOpenAI(
        openai_api_key=api_key,
        model="gpt-4o-mini",
        temperature=0
    )

llm = ai_model()  

AI_prompt = PromptTemplate(input_variables=["question", "columns"], template=dedent(PANDAS_PROMPT))
analyse_prompt = PromptTemplate(
    input_variables=["question", "data"],
    template=dedent(ANALYSE_PROMPT)
)
def DataFrameAgent(question: str):
    """
    Analyze data from artifact folder using natural language questions.
    
    Args:
        question: Natural language question about the data
        filename: Optional specific filename to analyze. If None, uses first available file.
    
    Returns:
        Analysis result from the AI agent
    """
    df = import_data()
    
    sdf = SmartDataframe(df, config={
        "llm": llm,
        "prompt_template": AI_prompt
    })
    result = sdf.chat(question) 
    if isinstance(result, pd.DataFrame):
        result = result.to_string()
    formatted_prompt = analyse_prompt.format(question=question, data=result)  
    response = llm.invoke(formatted_prompt) 

    return response.content


