from __future__ import annotations
from typing import TYPE_CHECKING

from app.repositories import UserRepository
from app.exceptions.base_exceptions import NotFoundError

if TYPE_CHECKING:
    from app.models import UserModel


class UserService:
    _user_rep: UserRepository

    def __init__(self, user_rep: UserRepository) -> None:
        self._user_rep = user_rep

    async def get_by_id(self, user_id: int) -> UserModel:
        user = await self._user_rep.get_by_id(user_id=user_id)
        if user is None:
            raise NotFoundError("User not found")

        return user

    async def get_by_bank_id(self, bank_id: str) -> UserModel:
        user = await self._user_rep.get_by_bank_id(bank_id=bank_id)
        if user is None:
            raise NotFoundError("User not found")

        return user

    async def get_or_create_by_bank_id(
        self,
        bank_id: str,
        first_name: str = "",
        second_name: str = "",
        place_of_work: str | None = None,
    ) -> UserModel:
        user = await self._user_rep.get_by_bank_id(bank_id)

        if user is None:
            user = await self._user_rep.create(
                bank_id=bank_id,
                first_name=first_name,
                second_name=second_name,
                place_of_work=place_of_work,
            )

        return user
