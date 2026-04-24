from __future__ import annotations
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select, update

from shared.models import Admin

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AdminRepository:
    _session: "AsyncSession"

    def __init__(self, session: "AsyncSession") -> None:
        self._session = session

    async def list_all(self) -> list[Admin]:
        result = await self._session.execute(
            select(Admin).order_by(Admin.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, admin_id: int) -> Admin | None:
        result = await self._session.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Admin | None:
        result = await self._session.execute(
            select(Admin).where(Admin.username == username)
        )
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self._session.execute(select(Admin.id))
        return len(result.scalars().all())

    async def create(
        self,
        username: str,
        password_hash: str,
        must_change_password: bool = False,
    ) -> Admin:
        admin = Admin(
            username=username,
            password_hash=password_hash,
            must_change_password=must_change_password,
        )
        self._session.add(admin)
        await self._session.flush()
        await self._session.refresh(admin)
        return admin

    async def update_password(
        self,
        admin_id: int,
        password_hash: str,
        must_change_password: bool = False,
    ) -> None:
        await self._session.execute(
            update(Admin)
            .where(Admin.id == admin_id)
            .values(
                password_hash=password_hash,
                must_change_password=must_change_password,
            )
        )

    async def set_totp_secret(
        self,
        admin_id: int,
        secret: str | None,
        enabled: bool,
    ) -> None:
        await self._session.execute(
            update(Admin)
            .where(Admin.id == admin_id)
            .values(totp_secret=secret, is_totp_enabled=enabled)
        )

    async def increment_failed_logins(self, admin_id: int) -> int:
        result = await self._session.execute(
            update(Admin)
            .where(Admin.id == admin_id)
            .values(failed_login_count=Admin.failed_login_count + 1)
            .returning(Admin.failed_login_count)
        )
        row = result.one_or_none()
        return int(row[0]) if row else 0

    async def set_locked_until(
        self,
        admin_id: int,
        locked_until: datetime | None,
    ) -> None:
        await self._session.execute(
            update(Admin)
            .where(Admin.id == admin_id)
            .values(locked_until=locked_until)
        )

    async def reset_failed_logins(self, admin_id: int) -> None:
        await self._session.execute(
            update(Admin)
            .where(Admin.id == admin_id)
            .values(failed_login_count=0, locked_until=None)
        )

    async def update_last_login(self, admin_id: int) -> None:
        await self._session.execute(
            update(Admin)
            .where(Admin.id == admin_id)
            .values(last_login_at=datetime.now(tz=timezone.utc))
        )

    async def set_active(self, admin_id: int, is_active: bool) -> None:
        await self._session.execute(
            update(Admin)
            .where(Admin.id == admin_id)
            .values(is_active=is_active)
        )
