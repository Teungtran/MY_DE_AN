from langchain_core.tools import tool
from pydantic import BaseModel, Field
import pandas as pd
from app.report_agent.parse_file import import_data
from .analyse_tool import analyze_tool
class AnalyseInput(BaseModel):
    user_input: str = Field(
        ...,
        description=(
            "User's question asking for specific data analysis "
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "what is the peak hour in that day?"
            }
        }

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

def get_data():
    """Lazy load data only when needed"""
    try:
        df = import_data()
        df_time = convert_any_datetime(df)
        return df_time
    except ValueError as e:
        # No data file uploaded yet
        return None

@tool("analyze_agent",
    description="Analyzes data and answers questions about datasets."
                "Call this tool first when users ask about data analysis, statistics, "
                "or insights from the data. Uses directly injected data or cached data.",
                args_schema=AnalyseInput)
def analyze_agent(user_input: str):
    df_time = get_data()
    if df_time is None:
        return "No data file has been uploaded yet. Please upload a CSV or Excel file first."
    response = analyze_tool(user_input=user_input, df=df_time)
    return str(response) if response is not None else "I couldn't generate a response. Please try again."

