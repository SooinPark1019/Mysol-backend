from typing import Annotated, Optional
from fastapi import Depends

from mysol.app.User.models import User
from mysol.app.User.store import UserStore
from mysol.app.User.hashing import Hasher

class UserService:
    def __init__(self, user_store: Annotated[UserStore, Depends()]) -> None:
        self.user_store = user_store

    async def add_user(self, email: str, password: str, username: str) -> User:
        hash_password = Hasher.hash_password(password)
        return await self.user_store.add_user(email=email, password=hash_password, username=username)

    async def get_user_by_id(self, id: int) -> User | None:
        return await self.user_store.get_user_by_id(id)

    async def get_user_by_username(self, username: str) -> User | None:
        return await self.user_store.get_user_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.user_store.get_user_by_email(email)
    
    async def update_user(
        self,
        username: Optional[str],
        email: str,
        old_password: str,
        new_password: Optional[str],
    ) -> User:
        hashed_new_password = Hasher.hash_password(new_password) if new_password else None
        return await self.user_store.update_user(username=username, email=email, old_password=old_password, new_password=hashed_new_password)
