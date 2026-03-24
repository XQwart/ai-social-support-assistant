from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import BASE_DIR


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parents[0] / ".env",
        extra="ignore",
    )

    log_level: str = "INFO"

    redis_host: str
    redis_port: int

    @property
    def redis_celery_url(self) -> str:
        return self._get_redis_url(1)

    polza_ai_api_key: str = ""
    polza_ai_base_url: str = "https://polza.ai/api/v1"
    polza_ai_model: str = "xiaomi/mimo-v2-flash"
    batch_size: int = 5
    default_timeout: int = 30

    def _get_redis_url(self, database_num: int) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{database_num}"


@lru_cache
def get_config():
    return Config()
