from __future__ import annotations

from gigachat import GigaChat

from worker.core.config import Config


def build_gigachat_client(config: Config) -> GigaChat:
    if not config.gigachat_api_key:
        raise ValueError("GIGACHAT_API_KEY is not set")

    return GigaChat(
        credentials=config.gigachat_api_key,
        scope=config.gigachat_scope,
        ca_bundle_file=config.rus_root_ca_cert_path,
    )
