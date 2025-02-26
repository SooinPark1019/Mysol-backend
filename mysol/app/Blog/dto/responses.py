from pydantic import BaseModel, Field
from datetime import datetime

class BlogDetailResponse(BaseModel):
    id: int
    blog_name: str = Field(serialization_alias="blog_name")
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    user_id : int

    class Config:
        from_attributes = True
        populate_by_name = True
        extra = "allow"
        exclude_none = False

class PaginatedBlogDetailResponse(BaseModel):
    page: int
    per_page: int
    total_count: int
    blogs: list[BlogDetailResponse]

    class Config:
        orm_mode = True