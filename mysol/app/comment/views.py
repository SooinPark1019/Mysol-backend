from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK, HTTP_201_CREATED,HTTP_204_NO_CONTENT

from mysol.app.user.models import User
comment_router = APIRouter()
from mysol.app.user.views import get_current_user_from_header
from mysol.app.comment.service import CommentService
from mysol.app.comment.dto.requests import CommentCreateRequest, CommentUpdateRequest
from mysol.app.comment.dto.responses import CommentDetailResponse,CommentListResponse,PaginatedCommentListResponse

@comment_router.post("/article/{article_id}", status_code=HTTP_201_CREATED)
async def create(
    user:Annotated[User,Depends(get_current_user_from_header)],
    comment_service: Annotated[CommentService, Depends()],
    comment_request: CommentCreateRequest,
    article_id:int,
)-> CommentDetailResponse:
    return await comment_service.create_article_comment(
        content=comment_request.content,
        level=comment_request.level,
        secret=comment_request.secret,
        user=user,
        article_id=article_id,
        parent_id=comment_request.parent_id
    )

@comment_router.post("/guestbook/{blog_id}", status_code=HTTP_201_CREATED)
async def create(
    user:Annotated[User,Depends(get_current_user_from_header)],
    comment_service: Annotated[CommentService, Depends()],
    comment_request: CommentCreateRequest,
    blog_id:int,
)-> CommentDetailResponse:
    return await comment_service.create_guestbook_comment(
        content=comment_request.content,
        level=comment_request.level,
        secret=comment_request.secret,
        user=user,
        blog_id=blog_id,
        parent_id=comment_request.parent_id
    )


@comment_router.patch("/{comment_id}", status_code=HTTP_200_OK)
async def update(
    user:Annotated[User,Depends(get_current_user_from_header)],
    comment_id:int,
    comment_service: Annotated[CommentService,Depends()],
    comment_request: CommentUpdateRequest
)-> CommentDetailResponse:
    return await comment_service.update_comment(
        user=user, 
        comment_id=comment_id,
        content=comment_request.content,
        secret=comment_request.secret
    )

@comment_router.delete("/{comment_id}", status_code=HTTP_204_NO_CONTENT)
async def delete(
    user:Annotated[User,Depends(get_current_user_from_header)],
    comment_service: Annotated[CommentService,Depends()],
    comment_id:int,
)-> None:
    await comment_service.delete_comment(
        user=user,
        comment_id=comment_id
    )

@comment_router.get("/article/{article_id}/{page}", status_code=HTTP_200_OK)
async def get_article_comment_list(
    article_id: int,
    page: int,
    comment_service: Annotated[CommentService, Depends()],
    user: Optional[User] = Depends(get_current_user_from_header),  # 여기가 포인트
):
    per_page = 10
    
    return await comment_service.get_article_list_pagination(
        article_id=article_id,
        page=page,
        per_page=per_page,
        current_user=user 
        )

@comment_router.get("/guestbook/{blog_id}/{page}", status_code=HTTP_200_OK)
async def get_guestbook_comment_list(
    blog_id: int,
    page: int,
    comment_service: Annotated[CommentService, Depends()],
    user: Optional[User] = Depends(get_current_user_from_header)
) -> PaginatedCommentListResponse:
    per_page = 10  # 페이지당 10개(혹은 쿼리 파라미터로 받아도 됨)
    return await comment_service.get_guestbook_list_pagination(
        blog_id=blog_id,
        page=page,
        per_page=per_page,
        current_user=user
    )

