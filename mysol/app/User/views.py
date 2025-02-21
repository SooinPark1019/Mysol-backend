from fastapi import APIRouter, Depends
from typing import Annotated
from starlette.status import HTTP_200_OK, HTTP_201_CREATED
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from mysol.database.settings import PW_SETTINGS
from mysol.app.User.dto.requests import UserSignupRequest, UserSigninRequest
from mysol.app.User.dto.reponses import UserSignupResponse, UserSigninResponse, MyProfileResponse
from mysol.app.User.service import UserService
from mysol.app.User.models import User
from mysol.app.User.errors import InvalidTokenError



user_router = APIRouter()

security = HTTPBearer()

async def login_with_header(
    user_service: Annotated[UserService, Depends()],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    token = credentials.credentials
    email = user_service.validate_access_token(token)
    user = await user_service.get_user_by_email(email)
    if not user:
        raise InvalidTokenError()
    return user

@user_router.post("/signup", response_model=UserSignupResponse, status_code=HTTP_201_CREATED)
async def signup(
    signup_request: UserSignupRequest, user_service: Annotated[UserService, Depends()]
) -> UserSignupResponse:
    user = await user_service.add_user(
        email=signup_request.email, username=signup_request.username, password=signup_request.password
    )
    return UserSignupResponse(email=user.email, username=user.username)

@user_router.post("/signin", status_code=HTTP_200_OK)
async def signin(
    user_service: Annotated[UserService, Depends()],
    signin_request: UserSigninRequest,
):
    access_token, refresh_token = await user_service.signin(
        signin_request.email, signin_request.password
    )
    return UserSigninResponse(access_token=access_token, refresh_token=refresh_token)

@user_router.get("/refresh", status_code=HTTP_200_OK)
async def refresh(
    user_service: Annotated[UserService, Depends()],
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    refresh_token = credentials.credentials
    access_token, new_refresh_token = await user_service.reissue_tokens(refresh_token)
    return UserSigninResponse(access_token=access_token, refresh_token=new_refresh_token)

@user_router.get("/me", status_code=HTTP_200_OK)
async def me(user: Annotated[User, Depends(login_with_header)]) -> MyProfileResponse:
    return MyProfileResponse.from_user(user)
