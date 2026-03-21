from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
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
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    sber_token_url: str
    sber_redirect_uri: str
    sber_userinfo_url: str
    client_id: str
    client_secret: str
    token_endpoint_auth_method: str = "client_secret_post"

    sber_ca_path: str = str(
        Path(__file__).resolve().parents[2] / "cert" / "sber_ift_ca.pem"
    )

    frontend_success_login_url: str

    jwt_access_secret: str
    jwt_refresh_secret: str
    jwt_access_token_expire: timedelta = timedelta(minutes=10)
    jwt_refresh_token_expire: timedelta = timedelta(days=7)
    code_ttl: timedelta = timedelta(seconds=30)
    oauth_ttl: timedelta = timedelta(minutes=10)


@lru_cache
def get_config():
    return Config()
