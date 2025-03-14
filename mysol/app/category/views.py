from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED,HTTP_204_NO_CONTENT

from mysol.app.category.dto.requests import CategoryUpdateRequest,CategoryCreateRequest
from mysol.app.category.dto.responses import CategoryDetailResponse,CategoryListResponse,CategoryFinalResponse
from mysol.app.category.models import Category
from mysol.app.category.service import CategoryService
from mysol.app.user.models import User
category_router = APIRouter()
from mysol.app.user.views import get_current_user_from_header

#카테고리를 생성하는 API
@category_router.post("/create", status_code=HTTP_201_CREATED)
async def create(
    user:Annotated[User,Depends(get_current_user_from_header)],
    category_create_request:CategoryCreateRequest,
    category_service: Annotated[CategoryService, Depends()],
)-> CategoryDetailResponse:
    return await category_service.create_category(
        user=user,
        categoryname=category_create_request.categoryname, 
        categorylevel=category_create_request.categoryLevel,
        parentId=category_create_request.parent_id
    )
@category_router.get("/{category_id}", status_code=HTTP_201_CREATED)
async def create(
    category_id:int,
    category_service: Annotated[CategoryService, Depends()],
)-> CategoryDetailResponse:
    return await category_service.get_category(
        category_id=category_id
    )

#현재 유저가 지니고 있는 카테고리들을 불러오는 API
@category_router.get("/list/user", status_code=HTTP_200_OK)
async def get_list(
    user:Annotated[User,Depends(get_current_user_from_header)],
    category_service:Annotated[CategoryService,Depends()],
)-> CategoryFinalResponse:
    return await category_service.list_categories(user)

@category_router.get("/list/{blog_id}", status_code=HTTP_200_OK)
async def get_list_by_blog(
    blog_id:int,
    category_service:Annotated[CategoryService,Depends()],
)-> CategoryFinalResponse:
    return await category_service.list_categories_by_blog(blog_id)

#특정 카테고리의 이름을 바꾸는 API
@category_router.patch("/{category_id}", status_code=HTTP_200_OK)
async def update_category(
    user: Annotated[User, Depends(get_current_user_from_header)],
    category_id:int,
    update_request: CategoryUpdateRequest,
    category_service: Annotated[CategoryService, Depends()],
)-> CategoryDetailResponse:
    return await category_service.update_category(
        user=user,
        category_id=category_id,
        new_category_name=update_request.categoryname
    )

@category_router.delete("/{category_id}",status_code=HTTP_204_NO_CONTENT)
async def delete_category(
    user:Annotated[User,Depends(get_current_user_from_header)],
    category_id:int,
    category_service:Annotated[CategoryService,Depends()],
)-> None:
    await category_service.delete_category(user,category_id)
    
