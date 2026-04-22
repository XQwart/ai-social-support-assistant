from __future__ import annotations
from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_gigachat import GigaChat, GigaChatEmbeddings

from .config import AIProvider


if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.embeddings.embeddings import Embeddings
    from .config import Config


def _get_gigachat_params(config: Config) -> dict:
    return {
        "credentials": config.gigachat_api_key,
        "ca_bundle_file": config.rus_root_ca_cert_path,
        "scope": config.gigachat_scope,
        "timeout": config.llm_timeout,
        "temperature": config.llm_generate_temperature,
        "max_tokens": config.llm_generate_max_tokens,
    }


def _get_polza_params(config: Config) -> dict:
    return {
        "base_url": config.polza_ai_base_url,
        "api_key": config.polza_ai_api_key,
        "timeout": config.llm_timeout,
        # "temperature": config.llm_generate_temperature,
    }


def create_llm_clients(config: Config) -> tuple[BaseChatModel, BaseChatModel]:
    match config.llm_provider:
        case AIProvider.GIGACHAT:
            params = _get_gigachat_params(config)

            chat_client = GigaChat(model=config.gigachat_model, **params)
            compress_client = (
                GigaChat(model=config.gigachat_compress_model, **params)
                if config.gigachat_compress_model
                else chat_client
            )

            return chat_client, compress_client

        case AIProvider.POLZA:
            params = _get_polza_params(config)

            chat_client = ChatOpenAI(model=config.polza_ai_model, **params)
            compress_client = (
                ChatOpenAI(model=config.polza_ai_compress_model, **params)
                if config.polza_ai_compress_model
                else chat_client
            )

            return chat_client, compress_client


def create_embedding_client(config: Config) -> tuple[Embeddings, int]:
    match config.embedding_provider:
        case AIProvider.GIGACHAT:
            params = _get_gigachat_params(config)

            embedding_client = GigaChatEmbeddings(
                model=config.gigachat_embedding_model, **params
            )

            return embedding_client, config.gigachat_embedding_vector_size

        case AIProvider.POLZA:
            params = _get_polza_params(config)

            embedding_client = OpenAIEmbeddings(
                model=config.polza_ai_embedding_model, **params
            )

            return embedding_client, config.gigachat_embedding_vector_size
