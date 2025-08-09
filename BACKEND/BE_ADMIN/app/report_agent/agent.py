from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from config.base_config import OpenAIConfig
from typing import Callable
from textwrap import dedent
from langchain.agents.agent_types import AgentType
import numpy as np
from .prompt import ANALYSE_PROMPT
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

def DataFrameAgent(question: str):
    df = import_data()
    data_summary = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'numerical_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
        'categorical_columns': df.select_dtypes(include=['object', 'category']).columns.tolist()
    }
    agent = create_pandas_dataframe_agent(
        llm, 
        df, 
        agent_type=AgentType.OPENAI_FUNCTIONS, 
        verbose=True, 
        allow_dangerous_code=True,
        prefix=dedent(ANALYSE_PROMPT.format(data_summary=data_summary)),
        include_df_in_prompt=True,
        max_iterations=10,
        early_stopping_method="generate"
    )
    response = agent.invoke({"input": question})
    return response.get('output') or response.get('result') or response

