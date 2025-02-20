from fastapi import APIRouter, Depends
from typing import Annotated
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from mysol.app.User.dto.requests import UserSignupRequest
from mysol.app.User.dto.reponses import UserSignupResponse
from mysol.app.User.service import UserService

user_router = APIRouter()

@user_router.post("/signup", response_model=UserSignupResponse, status_code=HTTP_201_CREATED)
async def signup(
    signup_request: UserSignupRequest, user_service: Annotated[UserService, Depends()]
) -> UserSignupResponse:
    user = await user_service.add_user(
        email=signup_request.email, username=signup_request.username, password=signup_request.password
    )
    return UserSignupResponse(email=user.email, username=user.username)