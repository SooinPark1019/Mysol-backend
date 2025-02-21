import jwt
from typing import Annotated, Optional
from fastapi import Depends
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum

from mysol.app.User.models import User
from mysol.app.User.store import UserStore
from mysol.app.User.hashing import Hasher
from mysol.database.settings import PW_SETTINGS
from mysol.app.User.errors import (
    EmailAlreadyExistsError,
    UserNameAlreadyExistsError,
    InvalidPasswordError,
    UserUnsignedError,
    UserNotFoundError,
    ExpiredSignatureError,
    InvalidTokenError,
    BlockedTokenError
)

class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"

class UserService:
    def __init__(self, user_store: Annotated[UserStore, Depends()]) -> None:
        self.user_store = user_store

    async def add_user(self, email: str, password: str, username: str) -> User:
        if await self.user_store.get_user_by_field("email", email):
            raise EmailAlreadyExistsError("이미 사용 중인 이메일입니다.")
        if await self.user_store.get_user_by_field("username", username):
            raise UserNameAlreadyExistsError("이미 사용 중인 사용자 이름입니다.")
        
        hashed_password = Hasher.hash_password(password)
        return await self.user_store.add_user(email=email, password=hashed_password, username=username)

    async def get_user_by_id(self, id: int) -> User:
        user = await self.user_store.get_user_by_id(id)
        if not user:
            raise UserUnsignedError("존재하지 않는 사용자입니다.")
        return user

    async def get_user_by_username(self, username: str) -> User:
        user = await self.user_store.get_user_by_username(username)
        if not user:
            raise UserUnsignedError("존재하지 않는 사용자입니다.")
        return user

    async def get_user_by_email(self, email: str) -> User:
        user = await self.user_store.get_user_by_email(email)
        if not user:
            raise UserUnsignedError("존재하지 않는 사용자입니다.")
        return user

    async def update_user(
        self,
        user: User,
        username: Optional[str],
        email: Optional[str],
        old_password: str,
        new_password: Optional[str],
    ) -> User:
        if not self._check_password(user.password, old_password):
            raise InvalidPasswordError()

        if username and await self.user_store.get_user_by_field("username", username):
            raise UserNameAlreadyExistsError()

        if email and await self.user_store.get_user_by_field("email", email):
            raise EmailAlreadyExistsError()
        
        hashed_new_password = Hasher.hash_password(new_password) if new_password else None
        return await self.user_store.update_user(
            user=user, username=username, email=email, new_password=hashed_new_password
        )

    def _check_password(self, stored_password: str, input_password: str) -> bool:
        return Hasher.verify_password(input_password, stored_password)

    
    async def signin(self, email: str, password: str) -> tuple[str, str]:
        user = await self.get_user_by_email(email)

        if user is None :
            raise UserNotFoundError()
    
        if Hasher.verify_password(password, user.password) == False:
            raise InvalidPasswordError()
        return self.issue_tokens(user.email)
    
    
    def issue_tokens(self, email: str) -> tuple[str, str]:
        access_payload = {
            "sub": email,
            "exp": datetime.now() + timedelta(minutes=10),
            "typ": TokenType.ACCESS.value,
        }
        access_token = jwt.encode(access_payload, PW_SETTINGS.secret_for_jwt, algorithm="HS256")

        refresh_payload = {
            "sub": email,
            "jti": uuid4().hex,
            "exp": datetime.now() + timedelta(days=7),
            "typ": TokenType.REFRESH.value,
        }
        refresh_token = jwt.encode(refresh_payload, PW_SETTINGS.secret_for_jwt, algorithm="HS256")
        return access_token, refresh_token

    def validate_access_token(self, token: str) -> str:
        """
        access_token을 검증하고, username을 반환합니다.
        """
        try:
            payload = jwt.decode(
                token, PW_SETTINGS.secret_for_jwt, algorithms=["HS256"], options={"require": ["sub"]}
            )
            if payload["typ"] != TokenType.ACCESS.value:
                raise InvalidTokenError()
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise ExpiredSignatureError()
        except jwt.InvalidTokenError:
            raise InvalidTokenError()

    async def validate_refresh_token(self, token: str) -> str:
        """
        refresh_token을 검증하고, username을 반환합니다.
        """
        try:
            payload = jwt.decode(
                token,
                PW_SETTINGS.secret_for_jwt,
                algorithms=["HS256"],
                options={"require": ["sub"]},
            )
        except jwt.ExpiredSignatureError:
            raise ExpiredSignatureError()
        except jwt.InvalidTokenError:
            raise InvalidTokenError()
        if payload["typ"] != TokenType.REFRESH.value:
            raise InvalidTokenError()
        if await self.user_store.is_token_blocked(payload["jti"]):
            raise BlockedTokenError()
        return payload["sub"]


    async def reissue_tokens(self, refresh_token: str) -> tuple[str, str]:
        username = await self.validate_refresh_token(refresh_token)
        await self.user_store.block_token(refresh_token, datetime.now())
        return self.issue_tokens(username)
