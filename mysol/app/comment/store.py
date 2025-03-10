from functools import cache
from typing import Annotated
from sqlalchemy.orm import selectinload
from sqlalchemy import select,and_,func, or_
from mysol.app.comment.errors import CommentNotFoundError,NotOwnerError, InvalidLevelError, ParentOtherSectionError,UserHasNoBlogError
from mysol.app.user.models import User
from mysol.database.annotation import transactional
from mysol.database.connection import SESSION
from mysol.app.blog.models import Blog
from mysol.app.article.models import Article
from mysol.app.comment.models import Comment

class CommentStore:
    async def get_comment_by_id(self,id:int)->Comment|None:
        get_comment_query = (
            select(Comment)
            .filter(Comment.id == id)
            .options(selectinload(Comment.user))  # user를 미리 로드하여 DetachedInstanceError 방지
        )
        comment=await SESSION.scalar(get_comment_query)
        return comment

    async def get_article_comments(
        self, article_id: int, page: int, per_page: int
    ) -> list[Comment]:
        offset_val = (page - 1) * per_page

        stmt = (
            select(Comment)
            .filter(Comment.article_id == article_id, Comment.level == 1)
            .options(
                selectinload(Comment.blog),
                selectinload(Comment.article),
                selectinload(Comment.user).selectinload(User.blogs),

                selectinload(Comment.children)
                    .options(
                        selectinload(Comment.user).selectinload(User.blogs),
                        selectinload(Comment.blog),
                        selectinload(Comment.article),
                    )
            )
            .offset(offset_val)
            .limit(per_page)
        )
        results = await SESSION.scalars(stmt)
        return list(results)

    async def get_article_comments_count(self, article_id: int) -> int:
        stmt = select(func.count(Comment.id)).filter(
            Comment.article_id == article_id
        )
        count = await SESSION.scalar(stmt)
        return count or 0


    async def get_guestbook_comments(
        self, blog_id: int, page: int, per_page: int
    ) -> list[Comment]:
        offset_val = (page - 1) * per_page

        stmt = (
            select(Comment)
            .filter(Comment.blog_id == blog_id, Comment.level == 1)
            .options(
                selectinload(Comment.blog),
                selectinload(Comment.article),
                selectinload(Comment.user).selectinload(User.blogs),

                selectinload(Comment.children)
                    .options(
                        selectinload(Comment.user).selectinload(User.blogs),
                        selectinload(Comment.blog),
                        selectinload(Comment.article),
                    )
            )
            .offset(offset_val)
            .limit(per_page)
        )
        results = await SESSION.scalars(stmt)
        return list(results)

    async def get_guestbook_comments_count(self, blog_id: int) -> int:
        stmt = select(func.count(Comment.id)).filter(
            Comment.blog_id == blog_id
        )
        count = await SESSION.scalar(stmt)
        return count or 0


    @transactional
    async def create_article_comment_1(
        self, content:str,secret:int,user:User,article_id:int
        )->Comment:
            if user.blogs is None:
                raise UserHasNoBlogError
            comment= Comment(
                content=content,
                level=1,
                secret=secret,
                user_id=user.id,
                user_name=user.username,
                article_id=article_id,
                parent_id=None,
                user_blog_id=user.blogs.id
                )
            SESSION.add(comment)
            print(comment)
            await SESSION.flush()
            await SESSION.refresh(comment)
            await SESSION.refresh(comment, ["user",  "blog", "article"])
            return comment
        
    @transactional
    async def create_article_comment_2(
        self, content: str, secret: int, user: User, article_id: int, parent_id: int
    ) -> Comment:
        if user.blogs is None:
            raise UserHasNoBlogError

        parent_comment = await self.get_comment_by_id(parent_id)  # 여기서 selectinload 사용됨

        if not parent_comment:
            raise CommentNotFoundError()

        if parent_comment.level == 2:
            raise InvalidLevelError()

        if parent_comment.article_id is None or parent_comment.article_id != article_id:
            raise ParentOtherSectionError()

        secret_here = secret
        if parent_comment.secret == 1:
            secret_here = 1

        comment = Comment(
            content=content,
            level=2,
            secret=secret_here,
            user_id=user.id,
            user_name=user.username,
            article_id=article_id,
            parent_id=parent_id,
            user_blog_id=user.blogs.id,
        )

        comment.parent = parent_comment  # 부모 댓글을 명확히 설정

        SESSION.add(comment)
        await SESSION.flush()
        await SESSION.refresh(comment)
        await SESSION.refresh(comment, ["user", "blog", "article"])  # 명확한 관계 로딩
        return comment

    @transactional
    async def create_guestbook_comment_1(
        self, content:str,secret:int,user:User,blog_id:int
        )->Comment:
            if user.blogs is None:
                raise UserHasNoBlogError
            print(content)
            print(user.username)
            print(secret)
            comment= Comment(
                content=content,
                level=1,
                secret=secret,
                user_id=user.id,
                user_name=user.username,
                blog_id=blog_id,
                parent_id=None,
                user_blog_id=user.blogs.id
                )
            SESSION.add(comment)
            print(comment)
            await SESSION.flush()
            await SESSION.refresh(comment)
            await SESSION.refresh(comment, ["user", "blog", "article"])
            return comment
        
    @transactional
    async def create_guestbook_comment_2(
        self, content:str,secret:int,user:User,blog_id:int,parent_id:int
        )->Comment:
            if user.blogs is None:
                raise UserHasNoBlogError
            parent_comment=await self.get_comment_by_id(parent_id)
            if not parent_comment:
                raise CommentNotFoundError()
            if parent_comment.level==2:
                raise InvalidLevelError()
            if parent_comment.blog_id==None or parent_comment.blog_id!=blog_id:
                raise ParentOtherSectionError()
            secret_here=secret
            if parent_comment.secret==1:
                secret_here=1
            comment= Comment(
                content=content,
                level=2,
                secret=secret_here,
                user_id=user.id,
                user_name=user.username,
                blog_id=blog_id,
                parent_id=parent_id,
                user_blog_id=user.blogs.id
            )
            comment.parent = parent_comment
            SESSION.add(comment)
            await SESSION.flush()
            await SESSION.refresh(comment)
            await SESSION.refresh(comment, ["user",  "blog", "article"])
            return comment


    @transactional
    async def update_comment(self, user: User, comment_id: int, content: str,secret:int) -> Comment:
        comment = await self.get_comment_by_id(comment_id)

        if comment is None:
            raise CommentNotFoundError()

        if comment.user_id != user.id:
            raise NotOwnerError()

        if content is not None:
            comment.content = content
        
        if secret is not None:
            comment.secret=secret

        await SESSION.flush()
        await SESSION.refresh(comment)  # 최신 상태로 업데이트
        await SESSION.refresh(comment, ["user",  "blog", "article"])
        return comment

    @transactional
    async def delete_comment(self, user: User, comment_id: int) -> None:
        comment = await self.get_comment_by_id(comment_id)

        if comment is None:
            raise CommentNotFoundError()

        
        if comment.user_id!=user.id:
            raise NotOwnerError()

        await SESSION.delete(comment)
        await SESSION.flush()

    # 답글이 달린 댓글 작성자들의 address_name을 반환
    async def get_replies_blog_address_name(self, address_name: str, parent_id: int, blog_address_name: str) -> list[str]:
        stmt = (
            select(Blog.address_name)
            .select_from(Comment)
            .join(User, User.id == Comment.user_id) # User와 Comment 조인
            .join(Blog, Blog.user_id == User.id) # User와 Blog 조인
            # .filter(or_(Comment.parent_id == parent_id, Comment.id == parent_id))  # parent_id 필터
            .where(
                (Comment.parent_id == parent_id) | (Comment.id == parent_id)
            )
            .distinct()  # 중복 제거
        )
        result = await SESSION.execute(stmt)
        replies = [reply[0] for reply in result.all()]

        if blog_address_name not in replies:
            replies.append(blog_address_name)

        return [reply for reply in replies if reply != address_name]