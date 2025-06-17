"""Define the configurable parameters for the agent."""

from __future__ import annotations

from typing import Annotated, Dict, Literal, Optional, Type, TypeVar, Union, cast

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_core.utils import from_env, secret_from_env
from pydantic import BaseModel, Field, SecretStr, model_validator
from typing_extensions import Self

from utils.utils import get_value_from_dict

from .config_loader import CONFIG

# Only load environment variables once
_env_loaded = False

def ensure_env_loaded():
    """Ensure environment variables are loaded only once."""
    global _env_loaded
    if not _env_loaded:
        load_dotenv(override=True)
        _env_loaded = True

class EmbeddingConfig(BaseModel):
    api_key: SecretStr = Field(default_factory=lambda: ensure_env_loaded() or secret_from_env("OPENAI_API_KEY"))
    model: Optional[str] = Field(default="text-embedding-3-small")
    kwargs: Dict = Field(default={})

class RedisConfig(BaseModel):
    host: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("REDIS_HOST")())[1])
    password: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("REDIS_PASS")())[1])
class MongoDBConfig(BaseModel):
    url: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("MONGO_URL", default="mongodb+srv://nguyentrantrung2504:NBg7vdR1KSDlW1E3@cluster0.hpkg9.mongodb.net/admin?retryWrites=true&w=majority&appName=Cluster0")())[1])
class OpenAIConfig(BaseModel):
    api_key: SecretStr = Field(default_factory=lambda: ensure_env_loaded() or secret_from_env("OPENAI_API_KEY"))
    model: Optional[str] = Field(default="gpt-4o-mini")
    kwargs: Dict = Field(default_factory=dict)
    
class KeyBERTConfig(BaseModel):
    model: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("KEYBERT_MODEL")())[1])

class DynamoDBConfig(BaseModel):
    aws_access_key_id: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("AWS_ACCESS_KEY_ID")())[1])
    aws_secret_access_key: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("AWS_SECRET_ACCESS_KEY")())[1])
    table_name: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("TABLE_NAME")())[1])
    region_name: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("AWS_REGION")())[1])

class SearchConfig(BaseModel):
    api_key: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("TAVILY_API_KEY")())[1])

class SQLConfig(BaseModel):
    server: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SQL_SERVER")())[1])
    database: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SQL_DATABASE")())[1])
class EmailConfig(BaseModel):
    server: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SMTP_SERVER")())[1])
    email: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("EMAIL_USER")())[1])
    password: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("EMAIL_PASSWORD")())[1])
    
class PolicyConfig(BaseModel):
    url: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("QDRANT_URL")())[1])
    api_key: SecretStr = Field(default_factory=lambda: (ensure_env_loaded(), secret_from_env("QDRANT_API_KEY")())[1])
    collection_name: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("POLICY")())[1])

class RecommendConfig(BaseModel):
    url: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("QDRANT_URL")())[1])
    api_key: SecretStr = Field(default_factory=lambda: (ensure_env_loaded(), secret_from_env("QDRANT_API_KEY")())[1])
    collection_name: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("STORAGE")())[1])
    
    
class AuthenConfig(BaseModel):
    key: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("SECRET_KEY")())[1])
    algorithm: str = Field(default_factory=lambda: (ensure_env_loaded(), from_env("ALGORITHM")())[1])


class BaseConfiguration(BaseModel):
    """Configuration class for indexing and retrieval operations.

    This class defines the parameters needed for configuring the indexing and
    retrieval processes, including embedding model selection, retriever provider choice, and search parameters.
    """

    top_k: int = Field(
        default_factory=lambda: get_value_from_dict("chat_model_config.top_k", CONFIG, default=10),
        description="The number of documents to re-rank. It also is the number of document use as context.",
    )

    search_type: Annotated[
        Literal["similarity", "mmr"],
        {"__template_metadata__": {"kind": "search"}},
    ] = Field(
        default_factory=lambda: get_value_from_dict("retrieval_config.search_type", CONFIG, default="similarity"),
        description="Type of search",
    )

    search_kwargs: Dict = Field(
        default_factory=lambda: get_value_from_dict("retrieval_config.kwargs", CONFIG, default={}),
        description="Additional keyword arguments to pass to the search function of the retriever.",
    )

    rrf_k: int = Field(
        default_factory=lambda: get_value_from_dict("retrieval_config.rrf_k", CONFIG, default=60),
        description="The parameter that controls the influence of each rank position.",
    )

    # Lazy-loaded configurations
    _chat_model_config = None
    _key_bert_config = None
    _embedding_model_config = None
    _vector_store_config = None
    _recommend_config = None
    _dynamo_config = None
    _embedding_config = None
    _redis_config = None
    _mongo_config = None
    _search_config = None
    _sql_config = None
    _auth_config = None
    _email_config = None
    @property
    def chat_model_config(self) -> Union[OpenAIConfig]:
        if self._chat_model_config is None:
            self._chat_model_config = OpenAIConfig()
        return self._chat_model_config
    @property
    def sql_config(self) -> Union[SQLConfig]:
        if self._sql_config is None:
            self._sql_config = SQLConfig()
        return self._sql_config
    @property
    def email_config(self) -> Union[EmailConfig]:
        if self._email_config is None:
            self._email_config = EmailConfig()
        return self._email_config
    @property
    def search_config(self) -> Union[SearchConfig]:
        if self._search_config is None:
            self._search_config = SearchConfig()
        return self._search_config
    @property
    def key_bert_config(self) -> Union[KeyBERTConfig]:
        if self._key_bert_config is None:
            self._key_bert_config = KeyBERTConfig()
        return self._key_bert_config
        
    @property
    def embedding_model_config(self) -> Union[EmbeddingConfig]:
        if self._embedding_model_config is None:
            self._embedding_model_config = EmbeddingConfig()
        return self._embedding_model_config
        
    @property
    def vector_store_config(self) -> Union[PolicyConfig]:
        if self._vector_store_config is None:
            self._vector_store_config = PolicyConfig()
        return self._vector_store_config
        
    @property
    def recommend_config(self) -> Union[RecommendConfig]:
        if self._recommend_config is None:
            self._recommend_config = RecommendConfig()
        return self._recommend_config
        
    @property
    def dynamo_config(self) -> Union[DynamoDBConfig]:
        if self._dynamo_config is None:
            self._dynamo_config = DynamoDBConfig()
        return self._dynamo_config
    @property
    def redis_config(self) -> Union[RedisConfig]:
        if self._redis_config is None:
            self._redis_config = RedisConfig()
        return self._redis_config
    @property
    def mongo_config(self) -> Union[MongoDBConfig]:
        if self._mongo_config is None:
            self._mongo_config = MongoDBConfig()
        return self._mongo_config   
    @property
    def auth_config(self) -> Union[AuthenConfig]:
        if self._auth_config is None:
            self._auth_config = AuthenConfig()
        return self._auth_config
        
    @property
    def embedding_config(self) -> Union[EmbeddingConfig]:
        if self._embedding_config is None:
            self._embedding_config = EmbeddingConfig()
        return self._embedding_config

    @model_validator(mode="after")
    def validate_provider(self) -> Self:
        """Load environment variables based on the provider."""
        ensure_env_loaded()
        
        chat_model_provider = get_value_from_dict("chat_model_config.provider", CONFIG)()
        embedding_provider = get_value_from_dict("embedding_model_config.provider", CONFIG)()
        retriever_provider = get_value_from_dict("retrieval_config.provider", CONFIG)()

        def get_provider_config(provider_dict: Dict, provider_name: str):
            try:
                return provider_dict[provider_name]()
            except KeyError:
                raise KeyError(f"'{provider_name}' is not supported! Supported: {list(provider_dict.keys())}.")

        def get_model_config(model_type, provider, config_key_prefix):
            model_config = get_provider_config(model_type, provider)
            model_config.model = get_value_from_dict(
                f"{config_key_prefix}.deployment_name", CONFIG, default={}
            )()
            model_config.kwargs = get_value_from_dict(f"{config_key_prefix}.kwargs", CONFIG, default={})()
            return model_config

        self._chat_model_config = get_model_config(AVAILABLE_CHAT_MODEL, chat_model_provider, "chat_model_config")
        self._embedding_model_config = get_model_config(
            AVAILABLE_EMBEDDING_MODEL, embedding_provider, "embedding_model_config"
        )

        self._vector_store_config = get_provider_config(AVAILABLE_RETRIEVER, retriever_provider)

        return self

    @classmethod
    def from_runnable_config(cls: Type[T], config: Optional[RunnableConfig] = None) -> T:
        """Create an IndexConfiguration instance from a RunnableConfig object.

        Args:
            cls (Type[T]): The class itself.
            config (Optional[RunnableConfig]): The configuration object to use.

        Returns:
            T: An instance of IndexConfiguration with the specified configuration.
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        return cast(T, update_config(configurable, cls))


def update_config(val, cls):
    if isinstance(val, Dict) and not isinstance(val, cls):
        _fields = {
            f_name: f_info.annotation
            for f_name, f_info in cls.model_fields.items()
            if f_info.init or f_info.init is None
        }
        return cls(**{k: update_config(v, _fields[k]) for k, v in val.items() if k in _fields.keys()})
    return val


AVAILABLE_CHAT_MODEL = {"openai": OpenAIConfig}

AVAILABLE_EMBEDDING_MODEL = {"openai": EmbeddingConfig}

AVAILABLE_RETRIEVER = {"qdrant": PolicyConfig}

# Lazy-loaded singleton instance
_APP_CONFIG = None

def get_app_config():
    """Get the singleton instance of BaseConfiguration."""
    global _APP_CONFIG
    if _APP_CONFIG is None:
        _APP_CONFIG = BaseConfiguration()
    return _APP_CONFIG

# For backward compatibility
APP_CONFIG = get_app_config()

T = TypeVar("T", bound=BaseConfiguration)
