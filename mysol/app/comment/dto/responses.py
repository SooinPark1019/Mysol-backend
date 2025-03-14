from pydantic import BaseModel
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime
from mysol.app.comment.models import Comment

if TYPE_CHECKING:
    from mysol.app.user.models import User
    
class CommentDetailResponse(BaseModel):
    id: int
    user_name: str
    content: str
    created_at: datetime
    updated_at: datetime
    secret: int
    user_blog_id:int
    blog_main_img:Optional[str]
    @staticmethod
    def from_comment(comment: Comment, current_user: Optional["User"]) -> "CommentDetailResponse":
        content_to_show = comment.content

        if comment.secret == 1:
            # 비밀 댓글 → 권한 체크
            if not current_user:
                # 로그인 안 함 → 무조건 "비밀 댓글입니다"
                content_to_show = "비밀 댓글입니다"
            else:
                is_author = (comment.user_id == current_user.id)

                # 블로그 주인 or 게시글(Article) 주인 판별
                is_resource_owner = False
                if hasattr(comment, "article") and comment.article:
                    if comment.article.blog_id == current_user.blogs.id:
                        is_resource_owner = True
                if hasattr(comment, "blog") and comment.blog:
                    if comment.blog.user_id == current_user.id:
                        is_resource_owner = True
                # 최종 체크
                if not (is_author or is_resource_owner):
                    content_to_show = "비밀 댓글입니다"
        blog_main_img = (
            comment.user.blogs.main_image_url  # 단일 Blog 객체로 접근
            if comment.user and comment.user.blogs else None
        )
        return CommentDetailResponse(
            id=comment.id,
            user_name=comment.user_name,
            content=content_to_show,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            secret=comment.secret,
            user_blog_id=comment.user_blog_id,
            blog_main_img=blog_main_img
        )


class CommentListResponse(BaseModel):
    id: int
    user_name: str
    content: str
    created_at: datetime
    updated_at: datetime
    secret: int
    user_blog_id:int
    blog_main_img:Optional[str]
    children: List["CommentDetailResponse"] = []
    class Config:
        orm_mode = True

    @staticmethod
    def from_comment(comment: Comment, current_user: Optional["User"]) -> "CommentListResponse":
        content_to_show = comment.content

        if comment.secret == 1:
            if not current_user:
                content_to_show = "비밀 댓글입니다"
            else:
                is_author = (comment.user_id == current_user.id)

                is_resource_owner = False
                if comment.blog and comment.blog.user_id == current_user.id:
                    is_resource_owner = True
                elif comment.article and comment.article.blog_id == current_user.blogs.id:
                    is_resource_owner = True

                if not (is_author or is_resource_owner):
                    content_to_show = "비밀 댓글입니다"
        blog_main_img = (
            comment.user.blogs.main_image_url  # 단일 Blog 객체로 접근
            if comment.user and comment.user.blogs else None
        )
        children_responses = [
            CommentDetailResponse.from_comment(child, current_user)
            for child in comment.children
        ]

        return CommentListResponse(
            id=comment.id,
            user_name=comment.user_name,
            content=content_to_show,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            secret=comment.secret,
            user_blog_id=comment.user_blog_id,
            blog_main_img=blog_main_img,
            children=children_responses
        )

class PaginatedCommentListResponse(BaseModel):
    page: int
    per_page: int
    total_count: int
    comments: List[CommentListResponse]