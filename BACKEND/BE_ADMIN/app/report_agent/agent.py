from langchain_core.tools import tool
from pydantic import BaseModel, Field
import pandas as pd
from app.report_agent.parse_file import import_data
from .analyse_tool import analyze_tool
from functools import lru_cache
import os
from pathlib import Path
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

# Global cache for loaded data
_data_cache = {
    'df': None,
    'mtime': None,
    'file_path': None
}

def get_artifact_file_info():
    """Get the most recent artifact file path and modification time"""
    artifact_dir = Path(__file__).parent / "artifact"
    if not artifact_dir.exists():
        return None, None
    
    supported_extensions = ['.csv', '.txt', '.xlsx', '.xls']
    files = [f for f in artifact_dir.iterdir() if f.suffix.lower() in supported_extensions]
    
    if not files:
        return None, None
    
    newest_file = max(files, key=lambda f: f.stat().st_mtime)
    return str(newest_file), newest_file.stat().st_mtime

def get_data():
    """
    Load data with caching to avoid redundant file reads.
    Cache is invalidated when a new file is uploaded.
    """
    try:
        current_file, current_mtime = get_artifact_file_info()
        
        if current_file is None:
            # No data file uploaded yet
            _data_cache['df'] = None
            _data_cache['mtime'] = None
            _data_cache['file_path'] = None
            return None
        
        # Check if cache is valid
        if (_data_cache['df'] is not None and 
            _data_cache['file_path'] == current_file and 
            _data_cache['mtime'] == current_mtime):
            # Return cached data
            return _data_cache['df']
        
        # Load fresh data
        df = import_data()
        df_time = convert_any_datetime(df)
        
        # Update cache
        _data_cache['df'] = df_time
        _data_cache['mtime'] = current_mtime
        _data_cache['file_path'] = current_file
        
        return df_time
    except ValueError as e:
        # No data file uploaded yet
        _data_cache['df'] = None
        _data_cache['mtime'] = None
        _data_cache['file_path'] = None
        return None

def clear_data_cache():
    """Clear the data cache (useful when data is updated)"""
    _data_cache['df'] = None
    _data_cache['mtime'] = None
    _data_cache['file_path'] = None

@tool("analyze_agent",args_schema=AnalyseInput)
def analyze_agent(user_input: str):
    """
    Analyzes data and answers questions about datasets. 
    Call this tool first when users ask about the dataset given
    """
    df_time = get_data()
    if df_time is None:
        return "No data file has been uploaded yet. Please upload a CSV or Excel file first."
    response = analyze_tool(user_input=user_input, df=df_time)
    return str(response) if response is not None else "I couldn't generate a response. Please try again."

