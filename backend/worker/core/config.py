from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from worker.core.constants import BASE_DIR


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parents[0] / ".env",
        extra="ignore",
    )

    log_level: str = "INFO"

    redis_host: str = ""
    redis_port: int = 6973

    postgres_host_1: str = ""
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_db: str = ""
    postgres_port: int = 3939

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host_1}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_celery_url(self) -> str:
        return self._get_redis_url(1)

    qdrant_url: str = ""
    qdrant_collection: str = "chunk_collection"

    polza_ai_api_key: str = ""
    polza_ai_base_url: str = "https://polza.ai/api/v1"
    polza_ai_faq_model: str = "xiaomi/mimo-v2-flash"
    polza_ai_embedding_model: str = "text-embedding-3-large"
    default_timeout: int = 30

    def _get_redis_url(self, database_num: int) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{database_num}"


@lru_cache
def get_config():
    return Config()
