from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from worker.core.constants import BASE_DIR, CERT_DIR


class LLMProvider(str, Enum):
    POLZA = "polza"
    GIGACHAT = "gigachat"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parents[0] / ".env",
        extra="ignore",
    )

    log_level: str = "INFO"

    redis_host: str = "redis"
    redis_port: int = 6973

    postgres_host: str = ""
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_db: str = ""
    postgres_port: int = 3939

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_celery_url(self) -> str:
        return self._get_redis_url(1)

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    qdrant_host: str = "qdrant"
    qdrant_port: str = "6333"
    chunks_collection_name: str = "chunk_collection"
    questions_collection_name: str = "question_collection"

    embedding_provider: str = "gigachat"
    polza_ai_api_key: str = ""
    polza_ai_base_url: str = "https://polza.ai/api/v1"
    polza_ai_faq_model: str = "xiaomi/mimo-v2-flash"
    polza_ai_embedding_model: str = "text-embedding-3-large"
    polza_ai_vector_size: int = 3072

    default_timeout: int = 5
    rus_root_ca_cert_path: str = str(CERT_DIR / "russian_trusted_root_ca.cer")
    gigachat_api_key: str = ""
    gigachat_quest_model: str = "GigaChat-2"
    gigachat_embedding_model: str = "EmbeddingsGigaR"
    gigachat_vector_size: int = 2560
    gigachat_scope: str = "GIGACHAT_API_B2B"

    llm_timeout: float = 60.0

    def _get_redis_url(self, database_num: int) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{database_num}"


@lru_cache
def get_config():
    return Config()
