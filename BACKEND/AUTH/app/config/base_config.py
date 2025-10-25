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
    host: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("POSTGRES_HOST", default="db.qwuepayeumnefnspnjmg.supabase.co")())[1])
    port: int = Field(default_factory=lambda: (ensure_env_loaded(), from_env("POSTGRES_PORT", default="5432")())[1])
    database: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("POSTGRES_DB", default="postgres")())[1])
    user: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("POSTGRES_USER", default="postgres")())[1])
    password: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("POSTGRES_PASSWORD", default="lilchong2504")())[1])

class EmailConfig(BaseModel):
    server: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SMTP_SERVER")())[1])
    email: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("EMAIL_USER")())[1])
    password: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("EMAIL_PASSWORD")())[1])

class AuthenConfig(BaseModel):
    key: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SECRET_KEY")())[1])
    algorithm: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("ALGORITHM")())[1])
