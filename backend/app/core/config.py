from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    redirect_uri: str
    userinfo_url: str
    client_id: str
    client_secret: str
    token_endpoint_auth_method: str = "client_secret_post"



@lru_cache
def get_config():
    return Config()
