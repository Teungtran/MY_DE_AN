from __future__ import annotations

from dotenv import load_dotenv
from langchain_core.utils import from_env
from pydantic import BaseModel, Field

# Only load environment variables once
_env_loaded = False

def ensure_env_loaded():
    """Ensure environment variables are loaded only once."""
    global _env_loaded
    if not _env_loaded:
        load_dotenv(override=True)
        _env_loaded = True

class SQLConfig(BaseModel):
    server: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SQL_SERVER")())[1])
    database: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SQL_DATABASE")())[1])

class EmailConfig(BaseModel):
    server: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SMTP_SERVER")())[1])
    email: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("EMAIL_USER")())[1])
    password: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("EMAIL_PASSWORD")())[1])

class AuthenConfig(BaseModel):
    key: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SECRET_KEY")())[1])
    algorithm: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("ALGORITHM")())[1])
