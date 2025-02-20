from typing import Optional
from sqlalchemy import select

from mysol.app.User.models import User
from mysol.database.annotation import transactional
from mysol.database.connection import SESSION
from mysol.app.User.hashing import Hasher

from mysol.app.User.errors import (
    EmailAlreadyExistsError,
    UserNameAlreadyExistsError,
    UserUnsignedError,
    InvalidPasswordError
)

class UserStore:
    @transactional
    async def add_user(self, email: str, password: str, username: str) -> User:
        if await self.get_user_by_field("email", email):
            raise EmailAlreadyExistsError()
        if await self.get_user_by_field("username", username):
            raise UserNameAlreadyExistsError()

        user = User(
            email=email,
            username=username,
            password=password,
        )

        SESSION.add(user)
        await SESSION.flush()
        return user

    async def get_user_by_id(self, id: int) -> Optional[User]:
        return await self.get_user_by_field("id", id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        return await self.get_user_by_field("username", username)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.get_user_by_field("email", email)

    async def get_user_by_field(self, field: str, value) -> Optional[User]:
        return await SESSION.scalar(select(User).where(getattr(User, field) == value))

    @transactional
    async def update_user(
        self,
        username: Optional[str],
        email: str,
        old_password: str,
        new_password: Optional[str],
    ) -> User:
        user = await self.get_user_by_email(email)
        if user is None:
            raise UserUnsignedError()

        if not self._check_password(user.password, old_password):
            raise InvalidPasswordError()

        if username and await self.get_user_by_field("username", username):
            raise UserNameAlreadyExistsError()
        if username:
            user.username = username

        if new_password:
            user.password = new_password

        return user

    def _check_password(self, stored_password: str, input_password: str) -> bool:
        return Hasher.verify_password(input_password, stored_password)
