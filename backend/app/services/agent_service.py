from __future__ import annotations
from typing import TYPE_CHECKING, AsyncIterator
import logging

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import AIMessageChunk
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
from app.schemas.stream_events import (
    StreamActionKind,
    StreamEvent,
    StreamEventType,
    tool_kind,
)

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langgraph.checkpoint.base import BaseCheckpointSaver

    from app.core.config import Config
    from app.models import UserModel
    from app.services import (
        RegionService,
        RAGService,
        UserService,
        WebSearchService,
        PageFetchService,
    )
    from app.services.prompt_service import PromptService


logger = logging.getLogger(__name__)


class AgentService:
    _chat_llm: BaseChatModel
    _compress_llm: BaseChatModel
    _region_service: RegionService
    _rag_service: RAGService
    _user_service: UserService
    _web_search_service: WebSearchService
    _page_fetch_service: PageFetchService
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
        web_search_service: WebSearchService,
        page_fetch_service: PageFetchService,
        checkpointer: BaseCheckpointSaver,
        config: Config,
        prompt_service: PromptService,
    ) -> None:
        self._chat_llm = chat_llm
        self._compress_llm = compress_llm
        self._region_service = region_service
        self._rag_service = rag_service
        self._user_service = user_service
        self._web_search_service = web_search_service
        self._page_fetch_service = page_fetch_service
        self._checkpointer = checkpointer
        self._config = config
        self._prompt_service = prompt_service

    async def run(self, chat_id: int, user: UserModel, content: str) -> str:
        final_message = ""
        async for event in self.run_stream(chat_id=chat_id, user=user, content=content):
            if event["type"] == StreamEventType.ASSISTANT_MESSAGE.value:
                final_message = event["content"]

        return final_message

    async def run_stream(
        self, chat_id: int, user: UserModel, content: str
    ) -> AsyncIterator[StreamEvent]:
        graph = self._create_graph(user)
        config = {
            "configurable": {"thread_id": str(chat_id)},
            "recursion_limit": self._config.agent_recursion_limit,
        }

        state = await graph.aget_state(config)
        is_new_dialog = not state.values.get("messages")
        logger.info(
            "Запрос к ИИ (stream): user_id=%s, is_sber=%s, user_message='%s', is_new_dialog=%s",
            user.id,
            user.is_sber_employee,
            content[:100],
            is_new_dialog,
        )

        final_message = ""
        phase_run_buffers: dict[str, str] = {}

        try:
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
                async for out in self._translate_event(
                    event, phase_run_buffers
                ):
                    if out["type"] == StreamEventType.PHASE_END.value:
                        if out["role"] == "final":
                            final_message = phase_run_buffers.pop(out["phase_id"], "")
                        else:
                            phase_run_buffers.pop(out["phase_id"], None)
                    yield out

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
                cleaned = self._prompt_service.get("FALLBACK_EMPTY_RESPONSE")

            yield {
                "type": StreamEventType.ASSISTANT_MESSAGE.value,
                "content": cleaned,
            }

        except Exception:
            logger.exception("Критическая ошибка при обращении к ИИ (stream)")
            yield {
                "type": StreamEventType.ASSISTANT_MESSAGE.value,
                "content": self._prompt_service.get("FALLBACK_AI_UNAVAILABLE"),
            }

    async def _translate_event(
        self, event: dict, phase_buffers: dict[str, str]
    ) -> AsyncIterator[StreamEvent]:
        kind = event["event"]
        name = event.get("name", "")
        run_id = event.get("run_id", "")
        data = event.get("data") or {}

        match kind:
            case "on_chat_model_start":
                phase_buffers[run_id] = ""
                yield {
                    "type": StreamEventType.PHASE_START.value,
                    "phase_id": run_id,
                }

            case "on_chat_model_stream":
                chunk = data.get("chunk")
                delta = self._chunk_content(chunk)
                if not delta:
                    return
                phase_buffers[run_id] = phase_buffers.get(run_id, "") + delta
                yield {
                    "type": StreamEventType.TOKEN.value,
                    "phase_id": run_id,
                    "delta": delta,
                }

            case "on_chat_model_end":
                output = data.get("output")
                tool_calls = getattr(output, "tool_calls", None) if output else None
                role = "thinking" if tool_calls else "final"
                yield {
                    "type": StreamEventType.PHASE_END.value,
                    "phase_id": run_id,
                    "role": role,
                }

            case "on_tool_start":
                action_kind = tool_kind(name)
                if action_kind is StreamActionKind.OTHER:
                    return
                tool_input = data.get("input", {}) or {}
                yield {
                    "type": StreamEventType.ACTION_START.value,
                    "action_id": run_id,
                    "kind": action_kind.value,
                    "tool": name,
                    "input": self._summarize_input(action_kind, tool_input),
                }

            case "on_tool_end":
                action_kind = tool_kind(name)
                if action_kind is StreamActionKind.OTHER:
                    return
                output = data.get("output")
                ok = self._tool_succeeded(output)
                yield {
                    "type": StreamEventType.ACTION_END.value,
                    "action_id": run_id,
                    "kind": action_kind.value,
                    "tool": name,
                    "ok": ok,
                }

    @staticmethod
    def _chunk_content(chunk: object) -> str:
        if chunk is None:
            return ""
        if isinstance(chunk, AIMessageChunk):
            content = chunk.content
        else:
            content = getattr(chunk, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    text = part.get("text") or part.get("content") or ""
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)
        return ""

    @staticmethod
    def _summarize_input(
        action_kind: StreamActionKind, tool_input: dict
    ) -> dict[str, object]:
        match action_kind:
            case StreamActionKind.RAG:
                return {
                    "query": tool_input.get("query"),
                    "region": tool_input.get("region_name"),
                }
            case StreamActionKind.WEB_SEARCH:
                return {"query": tool_input.get("query")}
            case StreamActionKind.FETCH_PAGE:
                urls = tool_input.get("urls") or []
                if isinstance(urls, str):
                    urls = [urls]
                return {"urls": list(urls)}
            case StreamActionKind.MEMORY:
                return {}
            case _:
                return {}

    @staticmethod
    def _tool_succeeded(output: object) -> bool:
        content = getattr(output, "content", output)
        if not isinstance(content, str):
            return True
        lowered = content.strip().lower()
        return not (lowered.startswith("error") or "не удалось" in lowered)

    def _create_graph(self, user: UserModel):
        tools = create_user_tools(
            user,
            self._user_service,
            self._rag_service,
            self._region_service,
            self._web_search_service,
            self._page_fetch_service,
            self._config,
        )

        middleware = [
            ToolBudgetMiddleware(self._config.agent_max_tool_calls),
            ToolGuardMiddleware(
                max_rag_searches_per_turn=self._config.agent_max_rag_per_turn,
                max_web_search_per_turn=self._config.agent_max_web_search_per_turn,
                max_page_fetch_per_turn=self._config.agent_max_page_fetch_per_turn,
            ),
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
