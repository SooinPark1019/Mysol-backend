from datetime import datetime
from functools import cache
from typing import Annotated
from sqlalchemy import select

from mysol.app.User.models import User
from mysol.database.annotation import transactional
from mysol.database.connection import SESSION

from mysol.app.User.errors import EmailAlreadyExistsError, UserNameAlreadyExistsError, UserUnsignedError, InvalidPasswordError

class UserStore:
    @transactional
    async def add_user(self, email: str, password: str, username: str) -> User:
        if await self.get_user_by_email(email):
            raise EmailAlreadyExistsError()
        if await self.get_user_by_username(username):
            raise UserNameAlreadyExistsError()
        user = User(
            email=email,
            username=username,
            password=password,
        )
        SESSION.add(user)
        await SESSION.flush()
        return user
    
    async def get_user_by_id(self, id: int) -> User | None:
        return await SESSION.scalar(select(User).where(User.id == id))

    async def get_user_by_username(self, username: str) -> User | None:
        return await SESSION.scalar(select(User).where(User.username == username))
    
    async def get_user_by_email(self, email: str) -> User | None:
        return await SESSION.scalar(select(User).where(User.email == email))
    
    @transactional
    async def update_user(
        self,
        id: int,
        username: str | None,
        email: str | None,
        old_password: str,
        new_password: str | None,
    ) -> User:
        user = await self.get_user_by_id(id)
        if user is None:
            raise UserUnsignedError()
        
        if user.password != old_password:
            raise InvalidPasswordError()
        
        if email is not None:
            if await self.get_user_by_email(email):
                raise EmailAlreadyExistsError()
            user.email = email

        if username is not None:
            if await self.get_user_by_username(username):
                raise UserNameAlreadyExistsError()
            user.username = username

        if new_password is not None:
            user.password = new_password

        return user