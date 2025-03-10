from pydantic import BaseModel, Field
from datetime import datetime

class BlogDetailResponse(BaseModel):
    id: int
    blog_name: str = Field(serialization_alias="blog_name")
    description: str | None = None  # 선택적 설명 필드
    created_at: datetime
    updated_at: datetime
    main_image_url: str | None = None  # 메인 이미지 URL 필드 추가
    user_id : int
    default_category_id : int | None

    class Config:
        from_attributes = True  # SQLAlchemy 모델에서 데이터를 가져올 때 변환 지원
        populate_by_name = True  # 필드 이름을 기반으로 데이터 채우기
        extra = "allow"  # 모델에 없는 필드 허용
        exclude_none = False  # None 값도 포함

class PaginatedBlogDetailResponse(BaseModel):
    page: int
    per_page: int
    total_count: int
    blogs: list[BlogDetailResponse]

    class Config:
        orm_mode = True  # SQLAlchemy ORM 모델을 지원하도록 설정
