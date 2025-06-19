"""Define the configurable parameters for the agent."""

from __future__ import annotations

from typing import Dict, Literal, Optional, Type, TypeVar, Union, cast

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_core.utils import from_env, secret_from_env
from pydantic import BaseModel, Field, SecretStr, model_validator
from typing_extensions import Self

from utils.utils import get_value_from_dict

from .config_loader import CONFIG

load_dotenv()


class EmbeddingConfig(BaseModel):
    api_key: SecretStr = Field(default_factory=secret_from_env("OPENAI_API_KEY"))
    model: Optional[str] = Field(default="text-embedding-3-small")
    kwargs: Dict = Field(default={})
    
class OpenAIConfig(BaseModel):
    api_key: SecretStr = Field(default_factory=secret_from_env("OPENAI_API_KEY"))
    model: Optional[str] = Field(default="gpt-4o-mini")
    kwargs: Dict = Field(default_factory=dict)
    
class RecommendConfig(BaseModel):
    url: str = Field(default_factory=from_env("QDRANT_URL"))
    api_key: SecretStr = Field(default_factory=secret_from_env("QDRANT_API_KEY"))
    collection_name: str = Field(default_factory=from_env("STORAGE"))
    
class PolicyConfig(BaseModel):
    url: str = Field(default_factory=from_env("QDRANT_URL"))
    api_key: SecretStr = Field(default_factory=secret_from_env("QDRANT_API_KEY"))
    collection_name: str = Field(default_factory=from_env("POLICY"))

class ChunkingMethodConfig(BaseModel):
    chunking_method: Literal["table"] = get_value_from_dict("chunking_method_config.method", CONFIG, default="table")()
    chunk_size: int = get_value_from_dict("chunking_method_config.chunk_size", CONFIG, default=512)()
    chunk_overlap: int = get_value_from_dict("chunking_method_config.chunk_overlap", CONFIG, default=100)()
    chunking_kwargs: Dict = get_value_from_dict("chunking_method_config.kwargs", CONFIG, default={})()


class WebhookConfig(BaseModel):
    url: str = Field(default_factory=from_env("WEBHOOK_URL"))
    rag_processed_endpoint: str = Field(default="/internal/callback/rag_processed")
    recommend_processed_endpoint: str = Field(default="/internal/callback/recommend_process")

class S3Config(BaseModel):
    bucket_name: str = Field(default_factory=from_env("BUCKET_NAME"))
    region_name: str = Field(default_factory=from_env("AWS_REGION"))
    access_key_id: SecretStr = Field(default_factory=secret_from_env("AWS_ACCESS_KEY_ID"))
    secret_access_key: SecretStr = Field(default_factory=secret_from_env("AWS_SECRET_ACCESS_KEY"))

class URLCrawlConfig(BaseModel):
    docintel_endpoint: str = Field(default_factory=from_env("DOCINTEL_ENDPOINT"))
    base_url: str = Field(default_factory=from_env("BASE_URL"))

class BaseConfiguration(BaseModel):
    """Configuration class for indexing and retrieval operations.

    This class defines the parameters needed for configuring the indexing and including embedding model selection.
    """

    prep_output_folder: str = Field(  # TODO: Need to use to store the tmp file
        default_factory=get_value_from_dict(
            "preprocessing_config.output_folder", CONFIG, default="preprocessing_output"
        ),
        description="Path of folder to store images, doc from preprocessing pipeline.",
    )

    chunking_method_config: Union[ChunkingMethodConfig] = ChunkingMethodConfig()
    s3config: Union[S3Config] = S3Config()
    webhook_config: WebhookConfig = WebhookConfig()
    embedding_model_config: Union[EmbeddingConfig] = EmbeddingConfig()
    chat_model_config: Union[OpenAIConfig] = OpenAIConfig()

    crawl_config: Union[URLCrawlConfig] = URLCrawlConfig()
    vector_store_config: Union[PolicyConfig] = PolicyConfig()
    recommend_config: Union[RecommendConfig] = RecommendConfig()

    @model_validator(mode="after")
    def validate_provider(self) -> Self:
        """Load environment variables based on the provider."""
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
                f"{config_key_prefix}.model", CONFIG, default=model_config.model
            )()
            model_config.kwargs = get_value_from_dict(f"{config_key_prefix}.kwargs", CONFIG, default={})()
            return model_config

        self.embedding_model_config = get_model_config(
            AVAILABLE_EMBEDDING_MODEL, embedding_provider, "embedding_model_config"
        )

        self.vector_store_config = get_provider_config(AVAILABLE_RETRIEVER, retriever_provider)

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

APP_CONFIG = BaseConfiguration()

T = TypeVar("T", bound=BaseConfiguration)
