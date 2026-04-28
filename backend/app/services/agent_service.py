from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages.human import HumanMessage

from app.agent.state import SOCAgentState, UserContext
from app.agent.tools import create_user_tools
from app.agent.middlewares import (
    build_dunamic_prompt,
    MemoryToolStateMiddleware,
    ToolBudgetMiddleware,
    ToolGuardMiddleware,
)
from app.agent.response_sanitizer import sanitize_final_message

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langgraph.checkpoint.base import BaseCheckpointSaver

    from app.core.config import Config
    from app.models import UserModel
    from app.services import RegionService, RAGService, UserService
    from app.services.prompt_service import PromptService


logger = logging.getLogger(__name__)


class AgentService:
    _chat_llm: BaseChatModel
    _compress_llm: BaseChatModel
    _region_service: RegionService
    _rag_service: RAGService
    _user_service: UserService
    _checkpointer: BaseCheckpointSaver
    _config: Config
    _prompt_service: PromptService

    def __init__(
        self,
        chat_llm: BaseChatModel,
        compress_llm: BaseChatModel,
        region_service: RegionService,
        rag_service: RAGService,
        user_service: UserService,
        checkpointer: BaseCheckpointSaver,
        config: Config,
        prompt_service: PromptService,
    ) -> None:
        self._chat_llm = chat_llm
        self._compress_llm = compress_llm
        self._region_service = region_service
        self._rag_service = rag_service
        self._user_service = user_service
        self._checkpointer = checkpointer
        self._config = config
        self._prompt_service = prompt_service

    async def run(self, chat_id: int, user: UserModel, content: str) -> str:
        graph = self._create_graph(user)
        config = {
            "configurable": {"thread_id": str(chat_id)},
            "recursion_limit": self._config.agent_recursion_limit,
        }

        state = await graph.aget_state(config)
        is_new_dialog = not state.values.get("messages")
        logger.info(
            "Запрос к ИИ: user_id=%s, is_sber=%s, user_message='%s', is_new_dialog=%s",
            user.id,
            user.is_sber_employee,
            content[:100],
            is_new_dialog,
        )

        try:
            final_message = ""

            async for event in graph.astream_events(
                {
                    "messages": [HumanMessage(content=content)],
                    "user_profile": {
                        "region_current": user.region_current,
                        "persistent_memory": user.persistent_memory,
                    },
                },
                config=config,
                context=UserContext(
                    first_name=user.first_name,
                    region_reg=user.region_reg,
                    is_sber_employee=user.is_sber_employee,
                    is_new_dialog=is_new_dialog,
                ),
                version="v2",
            ):
                kind = event["event"]
                name = event.get("name", "")

                match kind:
                    case "on_chain_start":
                        logger.debug("Старт узла: %s", name)

                    case "on_chat_model_start":
                        logger.debug("LLM думает: %s", name)

                    case "on_tool_start":
                        tool_input = event["data"].get("input", {})
                        logger.info(
                            "Вызов инструмента: %s | input: %s", name, tool_input
                        )

                    case "on_tool_end":
                        tool_output = event["data"].get("output", "")
                        logger.info(
                            "Инструмент завершён: %s | output: %s",
                            name,
                            str(tool_output)[:200],
                        )

                    case "on_chat_model_end":
                        output = event["data"].get("output")
                        if output and output.content:
                            tool_calls = getattr(output, "tool_calls", [])
                            if not tool_calls:
                                final_message = output.content
                                logger.debug(
                                    "LLM финальный ответ: %s", final_message[:100]
                                )
                            else:
                                logger.debug(
                                    "LLM вызывает инструменты: %s",
                                    [tc["name"] for tc in tool_calls],
                                )

                    case "on_chain_end":
                        logger.debug("Узел завершён: %s", name)

            if not final_message:
                state = await graph.aget_state(config)
                messages = state.values.get("messages") or []
                final_message = messages[-1].content if messages else ""

            cleaned = sanitize_final_message(final_message)
            if not cleaned:
                logger.warning(
                    "Пустой ответ ИИ после санитизации (длина до=%s)",
                    len(final_message or ""),
                )
                return self._prompt_service.get("FALLBACK_EMPTY_RESPONSE")

            if cleaned != final_message:
                logger.info(
                    "Ответ ИИ очищен от служебных строк: %s → %s символов",
                    len(final_message),
                    len(cleaned),
                )

            return cleaned

        except Exception:
            logger.exception("Критическая ошибка при обращении к ИИ")

            return self._prompt_service.get("FALLBACK_AI_UNAVAILABLE")

    def _create_graph(self, user: UserModel):
        tools = create_user_tools(
            user, self._user_service, self._rag_service, self._region_service
        )

        middleware = [
            ToolBudgetMiddleware(self._config.agent_max_tool_calls),
            ToolGuardMiddleware(self._config.agent_max_rag_per_turn),
            build_dunamic_prompt(self._prompt_service.get),
            MemoryToolStateMiddleware(),
            SummarizationMiddleware(
                model=self._compress_llm,
                trigger=[
                    ("tokens", self._config.llm_summarization_tokens_trigger),
                    ("messages", self._config.llm_summarization_messages_trigger),
                ],
                keep=("tokens", self._config.llm_summarization_tokens_keep),
                summary_prompt=self._prompt_service.get("COMPRESS_CONTEXT_SYSTEM"),
            ),
        ]

        return create_agent(
            model=self._chat_llm,
            tools=tools,
            middleware=middleware,
            checkpointer=self._checkpointer,
            context_schema=UserContext,
            state_schema=SOCAgentState,
        )
