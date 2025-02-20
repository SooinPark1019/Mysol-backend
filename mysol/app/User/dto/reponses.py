from pydantic import BaseModel, EmailStr

class UserSignupResponse(BaseModel):
    email: EmailStr
    username: str