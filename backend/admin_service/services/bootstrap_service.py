from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from app.agent.prompts import DEFAULT_PROMPTS, PROMPT_DESCRIPTIONS

from admin_service.core.security import hash_password

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    from admin_service.core.config import AdminConfig


logger = logging.getLogger(__name__)


class BootstrapService:
    """One-shot startup tasks for the admin service.

    Idempotent — safe to call on every container start.
    """

    _session_maker: "async_sessionmaker[AsyncSession]"
    _config: "AdminConfig"

    def __init__(
        self,
        session_maker: "async_sessionmaker[AsyncSession]",
        config: "AdminConfig",
    ) -> None:
        self._session_maker = session_maker
        self._config = config

    async def run(self) -> None:
        await self._seed_prompts()
        await self._seed_initial_admin()

    async def _seed_prompts(self) -> None:
        from admin_service.repositories.prompt_repository import (
            AdminPromptRepository,
        )

        try:
            async with self._session_maker() as session:
                repo = AdminPromptRepository(session)
                inserted = 0
                for key, body in DEFAULT_PROMPTS.items():
                    description = PROMPT_DESCRIPTIONS.get(key)
                    if await repo.seed_if_missing(key, body, description=description):
                        inserted += 1
                if inserted:
                    await session.commit()
                    logger.info(
                        "BootstrapService: seeded %d missing prompts", inserted
                    )
        except Exception:  # noqa: BLE001
            logger.exception("BootstrapService: failed to seed prompts")

    async def _seed_initial_admin(self) -> None:
        username = self._config.initial_admin_username
        password = self._config.initial_admin_password
        if not username or not password:
            return

        from admin_service.repositories.admin_repository import AdminRepository

        try:
            async with self._session_maker() as session:
                repo = AdminRepository(session)
                if await repo.count() > 0:
                    return
                await repo.create(
                    username=username,
                    password_hash=hash_password(password),
                    must_change_password=True,
                )
                await session.commit()
                logger.warning(
                    "BootstrapService: created initial admin '%s' "
                    "(must change password on first login)",
                    username,
                )
        except Exception:  # noqa: BLE001
            logger.exception("BootstrapService: failed to seed initial admin")
