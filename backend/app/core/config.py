from datetime import timedelta
from enum import Enum
from functools import lru_cache, cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client.models import Distance

from .constants import BASE_DIR, CERT_DIR


class AIProvider(str, Enum):
    POLZA = "polza"
    GIGACHAT = "gigachat"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parents[0] / ".env",
        extra="ignore",
    )

    log_level: str = "INFO"

    postgres_host: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int

    checkpointer_pool_max_conn: int = 20

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    redis_host: str
    redis_port: int

    @property
    def redis_url(self) -> str:
        return self._get_redis_url(0)

    qdrant_host: str
    qdrant_port: int = 6333

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    qdrant_collection: str = "chunk_collection"

    rag_distance: Distance = Distance.COSINE
    rag_top_k: int = 6
    rag_min_per_category: int = 2
    rag_score_threshold: float = 0.65

    sber_token_url: str = ""
    sber_authorize_url: str = "https://id-ift.sber.ru/CSAFront/oidc/authorize.do"
    sber_redirect_uri: str = ""
    sber_userinfo_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    sber_scopes: str = "openid name place_of_work"
    sber_application_name: str = "ИИ-помощник по социальной поддержке"

    rus_root_ca_cert_path: str = str(CERT_DIR / "russian_trusted_root_ca.cer")
    sber_ca_cert_path: str = str(CERT_DIR / "sber_ift_ca.pem")
    sber_client_cert_path: str = str(CERT_DIR / "sber_client_cert.crt")
    sber_client_key_path: str = str(CERT_DIR / "private.key")

    frontend_auth_redirect_url: str = ""

    jwt_access_secret: str
    jwt_refresh_secret: str
    jwt_access_token_expire: timedelta = timedelta(minutes=10)
    jwt_refresh_token_expire: timedelta = timedelta(days=7)
    code_ttl: timedelta = timedelta(seconds=30)
    oauth_ttl: timedelta = timedelta(minutes=10)

    llm_provider: AIProvider = AIProvider.GIGACHAT
    embedding_provider: AIProvider = AIProvider.GIGACHAT

    agent_max_tool_calls: int = 4
    agent_recursion_limit: int = 10

    polza_ai_api_key: str = ""
    polza_ai_base_url: str = "https://polza.ai/api/v1"
    polza_ai_model: str = "xiaomi/mimo-v2-flash"
    polza_ai_compress_model: str | None = None
    polza_ai_embedding_model: str = "text-embedding-3-large"
    polza_ai_embedding_vector_size: int = 3072

    gigachat_api_key: str = ""
    gigachat_scope: str = ""
    gigachat_model: str | None = None
    gigachat_compress_model: str | None = None
    gigachat_embedding_model: str = "EmbeddingsGigaR"
    gigachat_embedding_vector_size: int = 2560

    llm_source_text_limit: int = 3000
    llm_fallback_context_limit: int = 1000

    llm_generate_temperature: float = 0.3
    llm_generate_max_tokens: int = 2048
    llm_compress_temperature: float = 0.2
    llm_compress_max_tokens: int = 512

    llm_timeout: float = 60.0

    context_size: int = 64
    summary_limit: int = 10

    llm_summarization_tokens_trigger: int = 24000
    llm_summarization_messages_trigger: int = 60

    llm_summarization_tokens_keep: int = 8000

    llm_context_window_tokens: int = 128000
    llm_summary_trigger_ratio: float = 0.8
    llm_default_input_reserve_tokens: int = 800
    llm_reserve_history_size: int = 30

    @cached_property
    def llm_context_threshold(self) -> int:
        return int(self.llm_context_window_tokens * self.llm_summary_trigger_ratio)

    llm_recent_input_deltas_ttl: timedelta = timedelta(days=7)

    llm_summary_keep_recent_messages: int = 12

    def _get_redis_url(self, database_num: int) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{database_num}"


@lru_cache
def get_config():
    return Config()
