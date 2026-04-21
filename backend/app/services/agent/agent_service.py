from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages.human import HumanMessage

from app.agent.tools import create_user_tools
from .prompts import (
    build_system_prompt,
    COMPRESS_CONTEXT_SYSTEM,
    FALLBACK_AI_UNAVAILABLE,
)

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langgraph.graph.state import CompiledStateGraph
    from langgraph.checkpoint.base import BaseCheckpointSaver

    from app.core.config import Config
    from app.models import UserModel
    from app.services import RegionService, RAGService, UserService


logger = logging.getLogger(__name__)


class AgentService:
    _chat_llm: BaseChatModel
    _compress_llm: BaseChatModel
    _region_service: RegionService
    _rag_service: RAGService
    _user_service: UserService
    _checkpointer: BaseCheckpointSaver
    _config: Config

    def __init__(
        self,
        chat_llm: BaseChatModel,
        compress_llm: BaseChatModel,
        region_service: RegionService,
        rag_service: RAGService,
        user_service: UserService,
        checkpointer: BaseCheckpointSaver,
        config: Config,
    ) -> None:
        self._llm = chat_llm
        self._compress_llm = compress_llm
        self._region_service = region_service
        self._rag_service = rag_service
        self._user_service = user_service
        self._checkpointer = checkpointer
        self._config = config

    async def run(self, chat_id: int, user: UserModel, content: str) -> str:
        logger.info(
            "Запрос к ИИ: user_id=%s, is_sber=%s, user_message='%s'",
            user.id,
            user.is_sber_employee,
            content[:100],
        )

        graph = self._create_graph(user)
        try:
            response = await graph.ainvoke(
                {"messages": [HumanMessage(content=content)]},
                config={"configurable": {"thread_id": str(chat_id)}},
            )
            print(response.keys())

            return response["messages"][-1].content
        except Exception:
            logger.exception("Критическая ошибка при обращении к ИИ")

            return FALLBACK_AI_UNAVAILABLE

    def _create_graph(self, user: UserModel) -> CompiledStateGraph:
        tools = create_user_tools(
            user, self._user_service, self._rag_service, self._region_service
        )

        middleware = [
            SummarizationMiddleware(
                model=self._compress_llm,
                trigger=[
                    ("tokens", self._config.llm_summarization_tokens_trigger),
                    ("messages", self._config.llm_summarization_messages_trigger),
                ],
                keep=("tokens", self._config.llm_summarization_tokens_keep),
                summary_prompt=COMPRESS_CONTEXT_SYSTEM,
            )
        ]

        return create_agent(
            model=self._llm,
            tools=tools,
            middleware=middleware,
            checkpointer=self._checkpointer,
            system_prompt=build_system_prompt(user),
        )
