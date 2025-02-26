from typing import Annotated
from fastapi import Depends

from mysol.app.Blog.models import Blog
from mysol.app.User.models import User
from mysol.app.Blog.store import BlogStore
from mysol.app.Blog.dto.responses import BlogDetailResponse, PaginatedBlogDetailResponse
from mysol.app.Blog.errors import (
    BlogNotFoundError,
    BlognameAlreadyExistsError,
    BlogAlreadyExistsError
)
from mysol.app.Blog.errors import BlogNotFoundError
from mysol.app.User.store import UserStore

class BlogService:
    def __init__(self, blog_store: Annotated[BlogStore, Depends()], user_store: Annotated[UserStore, Depends()]) -> None:
        self.blog_store = blog_store
        self.user_store = user_store

    async def create_blog(
        self,
        user_id : int,
        blog_name: str,
        description: str|None,
    ) -> BlogDetailResponse:
        
        if await self.blog_store.get_blog_by_name(blog_name):
            raise BlognameAlreadyExistsError()
        if await self.blog_store.get_blog_of_user(user_id=user_id):
            raise BlogAlreadyExistsError
        
        blog=await self.blog_store.add_blog(user_id=user_id, blog_name=blog_name, description=description)

        return BlogDetailResponse.model_validate(blog, from_attributes=True)
    
    async def update_blog(
        self,
        user_id: int,
        new_blog_name : str | None,
        new_description : str |None,
    ) -> BlogDetailResponse:
        
        blog=self.blog_store.get_blog_of_user(user_id=user_id)

        if blog is None:
            raise BlogNotFoundError()
        
        if new_blog_name is not None and new_blog_name!=blog.blog_name:
            if await self.get_blog_by_name(new_blog_name):
                raise BlognameAlreadyExistsError()
        
        updated_blog = await self.blog_store.update_blog(
            blog_id=blog.id,
            new_blog_name=new_blog_name,
            new_description=new_description,
        )
        return BlogDetailResponse.model_validate(updated_blog, from_attributes=True)
    
    async def get_blog_by_user(self, user_id: int) -> BlogDetailResponse:
        # 유저의 블로그 조회
        blog = await self.blog_store.get_blog_of_user(user_id=user_id)
        if not blog:
            raise BlogNotFoundError()

        return BlogDetailResponse.model_validate(blog, from_attributes=True)
    
    async def get_blog_by_id(self, blog_id : int) -> BlogDetailResponse:
        blog=await self.blog_store.get_blog_by_id(blog_id)
        if blog is None:
            raise BlogNotFoundError
        return BlogDetailResponse.model_validate(blog, from_attributes=True)
    
    async def search_blog_by_keywords(self, keywords: str, page: int, per_page: int) -> PaginatedBlogDetailResponse:
        # 검색된 블로그와 총 개수를 반환
        blogs = await self.blog_store.search_blogs_by_keywords(keywords, page, per_page)
        total_count = await self.blog_store.count_search_result_by_keywords(keywords)

        # 블로그 목록을 DTO로 변환
        blog_responses = [
            BlogDetailResponse.model_validate(blog, from_attributes=True) for blog in blogs
        ]

        # 페이지네이션 응답 생성
        return PaginatedBlogDetailResponse(
            page=page,
            per_page=per_page,
            total_count=total_count,
            blogs=blog_responses,
        )
    



