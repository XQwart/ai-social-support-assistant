from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel


class UserRepository:
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> UserModel | None:
        return await self._session.get(UserModel, user_id)

    async def get_by_bank_id(self, bank_id: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.bank_id == bank_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        bank_id: str,
        first_name: str,
        second_name: str,
        place_of_work: str | None,
        region_reg: str | None,
        region_current: str | None,
    ) -> UserModel:
        user = UserModel(
            bank_id=bank_id,
            first_name=first_name,
            second_name=second_name,
            place_of_work=place_of_work,
            region_reg=region_reg,
            region_current=region_current,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def reset_user_memory(self, user_id: int) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(region_current=None, persistent_memory=None)
        )
        await self._session.commit()

    async def update_user_memory(self, user: UserModel, **fields) -> None:
        for field, value in fields.items():
            setattr(user, field, value)

        await self._session.commit()
        await self._session.refresh(user)

    async def delete(self, user_id: int) -> bool:
        stmt = delete(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0
