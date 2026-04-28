from __future__ import annotations
import asyncio
import logging
from typing import TYPE_CHECKING

from app.agent.prompts import DEFAULT_PROMPTS
from app.repositories.prompt_repository import PromptRepository

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


logger = logging.getLogger(__name__)


# Redis pub/sub channel used by the admin panel to invalidate cached
# prompts. The message body is the key of the prompt that was updated
# (e.g. ``SYSTEM_PROMPT_ROLE``); listeners refresh just that row.
PROMPT_INVALIDATION_CHANNEL = "prompts:invalidate"


# How often we do a full reconcile against the DB even without any
# invalidation notifications. Guards against a dropped pub/sub message
# or a restarted Redis instance missing a notify.
_RECONCILE_INTERVAL_SECONDS = 300.0


class PromptService:
    """In-process cache of LLM prompts with Redis-driven invalidation.

    The cache is a ``dict[key, (version, body)]``. It is warmed once on
    startup and then kept fresh by two mechanisms:

    1. A background task subscribes to ``prompts:invalidate`` on Redis.
       Whenever the admin panel publishes a key to that channel, the
       subscriber refreshes that single row from Postgres.
    2. The same task runs a periodic reconcile (every 5 minutes) that
       compares the DB ``version`` column against the cached version
       for each key, re-fetching any drift. This is a safety net, not
       the primary path.

    If the DB is unreachable or a key is missing from both the cache
    and the DB, :meth:`get` falls back to the module-level default in
    :mod:`app.agent.prompts`. A DB outage therefore degrades the admin
    panel (no edits possible) but does **not** take chat down.
    """

    _session_maker: async_sessionmaker[AsyncSession]
    _redis: Redis
    _cache: dict[str, tuple[int, str]]
    _subscriber_task: asyncio.Task[None] | None

    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        self._session_maker = session_maker
        self._redis = redis
        self._cache = {}
        self._subscriber_task = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, key: str) -> str:
        """Return the current body of ``key``, falling back to default."""
        cached = self._cache.get(key)
        if cached is not None:
            return cached[1]

        default = DEFAULT_PROMPTS.get(key)
        if default is None:
            logger.warning("PromptService: no prompt for key=%s", key)
            return ""
        return default

    async def start(self) -> None:
        """Warm the cache and start the background subscriber."""
        await self._warm_cache()
        self._subscriber_task = asyncio.create_task(
            self._run_subscriber(), name="prompt-service-subscriber"
        )
        logger.info(
            "PromptService started: %d prompts cached", len(self._cache)
        )

    async def stop(self) -> None:
        if self._subscriber_task is not None:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
            self._subscriber_task = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _warm_cache(self) -> None:
        try:
            async with self._session_maker() as session:
                repo = PromptRepository(session)
                rows = await repo.get_all()
            self._cache = {row.key: (row.version, row.body) for row in rows}
        except Exception:  # noqa: BLE001
            logger.exception(
                "PromptService: failed to warm cache; running on defaults"
            )

    async def _refresh_one(self, key: str) -> None:
        try:
            async with self._session_maker() as session:
                repo = PromptRepository(session)
                row = await repo.get_one(key)
            if row is None:
                self._cache.pop(key, None)
                logger.info("PromptService: key=%s removed from cache", key)
                return
            self._cache[key] = (row.version, row.body)
            logger.info(
                "PromptService: refreshed key=%s (version=%d)", key, row.version
            )
        except Exception:  # noqa: BLE001
            logger.exception("PromptService: failed to refresh key=%s", key)

    async def _reconcile_all(self) -> None:
        """Re-fetch any key whose DB version differs from the cache."""
        try:
            async with self._session_maker() as session:
                repo = PromptRepository(session)
                versions = await repo.get_versions()
                stale = [
                    key
                    for key, db_version in versions.items()
                    if self._cache.get(key, (0, ""))[0] != db_version
                ]
                if not stale:
                    return
                for key in stale:
                    row = await repo.get_one(key)
                    if row is not None:
                        self._cache[key] = (row.version, row.body)
            if stale:
                logger.info(
                    "PromptService: reconciled %d drifted key(s): %s",
                    len(stale),
                    stale,
                )
        except Exception:  # noqa: BLE001
            logger.exception("PromptService: reconcile failed")

    async def _run_subscriber(self) -> None:
        """Listen for Redis invalidations + periodic reconcile."""
        while True:
            try:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(PROMPT_INVALIDATION_CHANNEL)
                logger.info(
                    "PromptService: subscribed to %s", PROMPT_INVALIDATION_CHANNEL
                )
                reconcile_deadline = (
                    asyncio.get_event_loop().time() + _RECONCILE_INTERVAL_SECONDS
                )
                try:
                    while True:
                        timeout = max(
                            1.0,
                            reconcile_deadline - asyncio.get_event_loop().time(),
                        )
                        message = await pubsub.get_message(
                            ignore_subscribe_messages=True,
                            timeout=timeout,
                        )
                        if message is not None:
                            key = message.get("data")
                            if isinstance(key, bytes):
                                key = key.decode("utf-8")
                            if key:
                                await self._refresh_one(key)
                        now = asyncio.get_event_loop().time()
                        if now >= reconcile_deadline:
                            await self._reconcile_all()
                            reconcile_deadline = (
                                now + _RECONCILE_INTERVAL_SECONDS
                            )
                finally:
                    try:
                        await pubsub.unsubscribe(PROMPT_INVALIDATION_CHANNEL)
                        await pubsub.close()
                    except Exception:  # noqa: BLE001
                        pass
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                logger.exception(
                    "PromptService: subscriber crashed; retrying in 5s"
                )
                await asyncio.sleep(5)
