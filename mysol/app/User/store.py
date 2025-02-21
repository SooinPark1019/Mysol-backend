from typing import Optional
from sqlalchemy import select
from datetime import datetime

from mysol.app.User.models import User, BlockedToken
from mysol.database.annotation import transactional
from mysol.database.connection import SESSION
from mysol.app.User.hashing import Hasher

class UserStore:
    @transactional
    async def add_user(self, email: str, password: str, username: str) -> User:
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
        self, user: User, username: Optional[str], email: Optional[str], new_password: Optional[str]
    ) -> User:
        if username:
            user.username = username
        if email:
            user.email = email
        if new_password:
            user.password = new_password
        return user

    @transactional
    async def block_token(self, token_id: str, expired_at: datetime) -> None:
        blocked_token = BlockedToken(token_id=token_id, expired_at=expired_at)
        SESSION.add(blocked_token)

    async def is_token_blocked(self, token_id: str) -> bool:
        return (
            await SESSION.scalar(
                select(BlockedToken).where(BlockedToken.token_id == token_id)
            )
            is not None
        )
