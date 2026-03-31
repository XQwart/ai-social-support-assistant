from datetime import timedelta
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import BASE_DIR, CERT_DIR


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

    sber_token_url: str = ""
    sber_authorize_url: str = "https://id-ift.sber.ru/CSAFront/oidc/authorize.do"
    sber_redirect_uri: str = ""
    sber_userinfo_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    sber_scopes: str = "openid name"
    sber_application_name: str = "ИИ-помощник по социальной поддержке"

    sber_ca_cert_path: str = str(CERT_DIR / "sber_ift_ca.pem")
    sber_client_cert_path: str = str(CERT_DIR / "sber_client_cert.crt")
    sber_client_key_path: str = str(CERT_DIR / "private.key")

    frontend_url: str = ""

    jwt_access_secret: str
    jwt_refresh_secret: str
    jwt_access_token_expire: timedelta = timedelta(minutes=10)
    jwt_refresh_token_expire: timedelta = timedelta(days=7)
    code_ttl: timedelta = timedelta(seconds=30)
    oauth_ttl: timedelta = timedelta(minutes=10)

    polza_ai_api_key: str = ""
    polza_ai_base_url: str = "https://polza.ai/api/v1"
    polza_ai_model: str = "xiaomi/mimo-v2-flash"

    context_size: int = 64
    summary_limit: int = 10

    def _get_redis_url(self, database_num: int) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{database_num}"


@lru_cache
def get_config():
    return Config()
