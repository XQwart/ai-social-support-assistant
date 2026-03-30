from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import UserModel


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
        self, bank_id: str, first_name: str, second_name: str
    ) -> UserModel:
        user = UserModel(
            bank_id=bank_id, first_name=first_name, second_name=second_name
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete(self, user_id: int) -> bool:
        stmt = delete(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0
