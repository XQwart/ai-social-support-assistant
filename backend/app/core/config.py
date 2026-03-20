from functools import lru_cache
from datetime import timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redirect_uri: str
    userinfo_url: str
    client_id: str
    client_secret: str
    token_endpoint_auth_method: str = "client_secret_post"
    jwt_refresh_token_expire: timedelta = timedelta(days=7)
    code_ttl: timedelta = timedelta(seconds=30)
    oauth_ttl: timedelta = timedelta(minutes=10)


@lru_cache
def get_config():
    return Config()
