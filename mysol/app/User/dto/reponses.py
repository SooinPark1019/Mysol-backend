from pydantic import BaseModel, EmailStr

from mysol.app.User.models import User

class UserSignupResponse(BaseModel):
    email: EmailStr
    username: str

class UserSigninResponse(BaseModel):
    access_token: str
    refresh_token: str
    username: str

class MyProfileResponse(BaseModel):
    username: str
    email: str

    @staticmethod
    def from_user(user: User) -> "MyProfileResponse":
        return MyProfileResponse(
            username=user.username,
            email=user.email,
        )