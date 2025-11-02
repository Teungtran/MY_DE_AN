from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from app.config.base_config import OpenAIConfig
from typing import Callable
from textwrap import dedent
from langchain.agents.agent_types import AgentType
import pandas as pd
from app.workflow.prompt import ANALYSE_PROMPT
from app.report_agent.parse_file import import_data
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

def convert_any_datetime(df):
    datetime_columns = []

    for col in df.columns:
        if "id" in col.lower():
            continue

        sample_values = df[col].dropna().astype(str).head(5)

        if sample_values.str.fullmatch(r"\d{4}").all():
            datetime_columns.append((col, "%Y"))
            continue

        looks_like_date = sample_values.str.contains(r"[-/:.]").any()
        if not looks_like_date:
            continue

        parsed = pd.to_datetime(sample_values, errors='coerce', utc=True)
        success_rate = parsed.notna().mean()

        if success_rate > 0.8:
            datetime_columns.append((col, None))  

    for col, fmt in datetime_columns:
        if fmt:
            df[col] = pd.to_datetime(df[col], format=fmt, errors='coerce', utc=True)
        else:
            df[col] = pd.to_datetime(df[col], format="mixed", errors='coerce', utc=True)

    return df
def DataFrameAgent(question: str):
    df = import_data()
    df_time = convert_any_datetime(df)
    data_summary = {
        'data_info': df_time.info()
        }
    agent = create_pandas_dataframe_agent(
        llm, 
        df_time, 
        agent_type=AgentType.OPENAI_FUNCTIONS, 
        verbose=True, 
        allow_dangerous_code=True,
        return_intermediate_steps = True,
        prefix=dedent(ANALYSE_PROMPT.format(data_summary=data_summary)),
        include_df_in_prompt=True,
        max_iterations=10
        )
    response = agent.invoke({"input": question})
    # Extract the output string from the response
    output = response.get('output') or response.get('result')
    if output is None:
        # If no output/result, convert the entire response to string
        output = str(response)
    # Ensure we return a string
    return str(output) if output is not None else "I couldn't generate a response. Please try again."

