from typing import Optional
from pydantic import BaseModel, field_validator
from mysol.common.errors import InvalidFieldFormatError

class BlogCreateRequest(BaseModel):
    blog_name: Optional[str]
    description: Optional[str] = None

    @field_validator("blog_name")
    @classmethod
    def validate_blog_name(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and (len(value) < 3 or len(value) > 20):
            raise InvalidFieldFormatError("블로그 이름은 3자 이상 20자 이하여야 합니다.")
        return value

class BlogUpdateRequest(BaseModel):
    blog_name: Optional[str] = None
    description: Optional[str] = None

    @field_validator("blog_name")
    @classmethod
    def validate_blog_name(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and (len(value) < 3 or len(value) > 20):
            raise InvalidFieldFormatError("블로그 이름은 3자 이상 20자 이하여야 합니다.")
        return value
