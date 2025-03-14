from functools import cache
from fastapi import Depends
from typing import Annotated, Sequence, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import Select, select, or_, and_, func, update, cast, String, text
from sqlalchemy.orm import joinedload, aliased, Mapped
from sqlalchemy.sql.elements import ClauseElement
from sqlalchemy.sql.expression import func
from sqlalchemy.dialects.mysql import JSON

from mysol.app.article.models import Article
from mysol.app.blog.models import Blog
from mysol.app.like.models import Like
from mysol.app.comment.models import Comment
from mysol.app.subscription.models import Subscription
from mysol.database.annotation import transactional
from mysol.database.connection import SESSION
from mysol.app.article.dto.responses import ArticleSearchInListResponse, PaginatedArticleListResponse, ArticleInformationResponse
from mysol.app.user.models import User
from mysol.app.image.models import Image
from mysol.app.image.store import ImageStore
from mysol.app.image.dto.requests import ImageCreateRequest
from mysol.app.article.errors import NoAuthoriztionError, ArticleNotFoundError
from mysol.app.user.models import User


class ArticleStore :
    def __init__(
        self,
        image_store : Annotated[ImageStore, Depends()],

    ) :
        self.image_store = image_store

    def get_access_condition(self, user: User, show_secret: int = 1) -> ClauseElement:
        """
        공개 글 또는 작성자인 경우 접근 권한을 확인하는 조건 생성
        """
        if show_secret==0:
            return and_(
                Article.secret==0,
                Article.protected==0
            )
        
        return or_(
            Article.secret == 0,  # 공개 글
            Blog.user_id == user.id  # 작성자인 경우
        )

    def build_base_query(self, access_condition: ClauseElement | None = None) -> Select:
        query = (
            select(
                Article,
                func.count(func.distinct(Like.id)).label("likes"),
                func.count(func.distinct(Comment.id)).label("comments"),
                Blog.blog_name.label("blog_name"),
                Blog.main_image_url.label("blog_main_image_url")
            )
            .join(Blog, Blog.id == Article.blog_id)
            .join(Like, Like.article_id == Article.id, isouter=True)
            .join(Comment, Comment.article_id == Article.id, isouter=True)
            .options(joinedload(Article.blog))
            .group_by(Article.id, Blog.blog_name, Blog.main_image_url)
        )

        if access_condition is not None:
            query = query.filter(access_condition)

        return query

        
    @transactional
    async def create_article(
        self, 
        article_title : str, 
        article_content: str, 
        article_description: str, 
        main_image_url : str | None,
        blog_id : int, 
        category_id : int, 
        images : List[ImageCreateRequest],
        problem_numbers : Optional[list[int]] = None,
        secret : int = 0,
        protected: int = 0,
        comments_enabled : int = 1,
        password: Optional[str] = None
    ) -> Article :
        
        problem_numbers = problem_numbers or []
        
        article = Article(
            title=article_title, 
            content=article_content, 
            description=article_description, 
            main_image_url=main_image_url,
            blog_id=blog_id, 
            category_id=category_id, 
            secret=secret,
            protected=protected,
            password=password,
            comments_enabled=comments_enabled,
            problem_numbers=problem_numbers
        )
        
        SESSION.add(article)
        await SESSION.flush()
        await SESSION.refresh(article)

        """
        # main_image 에 대응되는 객체 생성
        if main_image_url :
            await self.image_store.create_image(
                file_url = main_image_url,
                article_id = article.id,
                is_main = True
            )
        """
        # article 내부에 존재하는 객체 생성
        for image_request in images:
            await self.image_store.create_image(
                file_url = image_request.file_url,
                article_id = article.id
            )
        return article
    
    @transactional
    async def update_article(
        self, 
        article: Article,
        category_id: int,
        images: List[ImageCreateRequest],
        problem_numbers : Optional[list[int]] = None,
        article_title: Optional[str] = None,
        article_content: Optional[str] = None,
        article_description: Optional[str] = None,
        main_image_url: Optional[str] = None,
        secret: Optional[int] = None,
        protected: Optional[int] = None,
        password: Optional[str] = None,
        comments_enabled: Optional[int]=None,
    ) -> Article:
        if article_title is not None:
            article.title = article_title
        if article_content is not None:
            article.content = article_content
        if article_content is not None:
            article.description = article_description
        if secret is not None:
            article.secret=secret
        if protected is not None:
            if protected == 0 and article.protected==1:
                article.password = None
            article.protected = protected
        if password is not None:
            article.password = password
        if comments_enabled is not None:
            article.comments_enabled = comments_enabled
        if category_id is not None:
            article.category_id = category_id
        if problem_numbers is not None:
            article.problem_numbers = problem_numbers


        if main_image_url != article.main_image_url :
            previous_main_image = await self.image_store.get_image_of_article_by_url(article.id, article.main_image_url)
            print("previous main image URL : ",article.main_image_url)
            print("after_main_image_url : ", main_image_url)
            # 기존의 main image 가 content 내부에 들어있지 않는 조건
            if not previous_main_image :
                print("A")

                # 기존의 main image 가 null 이나 "" 의 값이 아닐 조건               
                if await self.image_store.image_exists_in_S3(article.main_image_url):
                    await self.image_store.delete_image_in_S3(article.main_image_url)

            print("A main_image_url :", article.main_image_url)

            """
            if main_image_url :
                
                print("B main_image_url :", main_image_url)
                await self.image_store.create_image(
                    file_url = main_image_url, 
                    article_id = article.id,
                    is_main = True
                )
            """
        
        article.main_image_url = main_image_url


        # 기존 이미지 목록 가져오기(단, main_image 는 제외)
        existing_images = await SESSION.execute(
            select(Image).where(Image.article_id == article.id, Image.is_main == False)
        )
        existing_images = existing_images.scalars().all()
        
        # 기존 이미지 URL 리스트
        existing_image_urls = {img.file_url for img in existing_images}
        # 업데이트 요청에 포함된 이미지 URL
        new_image_urls = {img.file_url for img in images}

        # 삭제할 이미지 찾기 (기존에는 있었지만, 새 데이터에는 없는 이미지)
        images_to_delete = [img for img in existing_images if img.file_url not in new_image_urls]
        for img in images_to_delete:
            if article.main_image_url != img.file_url:
                await self.image_store.delete_image(img)

        # 추가할 이미지 찾기 (기존에는 없었지만, 새 데이터에 있는 이미지)
        for img in images : 
            if img.file_url not in existing_image_urls :
                await self.image_store.create_image(
                    file_url = img.file_url, 
                    article_id = article.id
                )

        await SESSION.merge(article)
        await SESSION.flush()
        return article
    

    @transactional
    async def delete_article(self, article: Article) -> None:
        if await self.image_store.image_exists_in_S3(article.main_image_url):
            await self.image_store.delete_image_in_S3(article.main_image_url)
        await SESSION.delete(article)
        await SESSION.flush()   

    @transactional
    async def increment_article_views(self, article_id: int) -> None:
        stmt = (
            update(Article)
            .where(Article.id == article_id)
            .values(views=Article.views + 1)
        )
        await SESSION.execute(stmt)
        await SESSION.flush()

    @transactional
    async def get_article_by_id(self, article_id: int) -> Article | None:
        stmt = select(Article).options(joinedload(Article.blog)).where(Article.id == article_id)
        result = await SESSION.execute(stmt)
        return result.scalar_one_or_none()

    @transactional
    async def get_article_information_by_id(
        self,
        article_id: int,
        user: Optional[User],
        password: Optional[str] = None
    ) -> ArticleInformationResponse:
        base_query = self.build_base_query()
        stmt = base_query.filter(Article.id == article_id)
        
        result = await SESSION.execute(stmt)
        row = result.one_or_none()
        if row is None:
            raise ArticleNotFoundError()
        article = row.Article
        blog = await SESSION.get(Blog, article.blog_id)
        
        # secret 게시글은 로그인하지 않았거나 작성자가 아닌 경우 열람 불가
        if article.secret == 1:
            if not user or blog.user_id != user.id:
                raise NoAuthoriztionError("비밀글은 작성자만 열람할 수 있습니다.")
        
        # 보호글은 작성자가 아닌 경우 반드시 올바른 비밀번호가 필요
        if article.protected == 1 and (not user or blog.user_id != user.id):
            if not password or article.password != password:
                raise NoAuthoriztionError("보호된 게시글은 올바른 비밀번호가 필요합니다.")
        
        article_response = ArticleInformationResponse.from_article(
            article=article,
            blog_name=row.blog_name,
            blog_main_image_url=row.blog_main_image_url,
            article_likes=row.likes,
            article_comments=row.comments,
        )
        
        if article_response.category_id == blog.default_category_id:
            article_response.category_id = 0

        return article_response

    
    
    @transactional
    async def get_articles_by_ids(self, article_ids: list[int], user: User) -> Sequence[Article]:
        access_condition = self.get_access_condition(user)
        article_list_query = (
            select(Article)
            .options(joinedload(Article.blog))  # Blog 관계 미리 로드
            .where(
                and_(
                    Article.id.in_(article_ids),  # 특정 article_ids에 속한 글
                    access_condition             # 접근 권한 확인
                )
            )
        )
        result = await SESSION.scalars(article_list_query)  # await 추가
        return result.all()
    
    @transactional
    async def get_today_most_viewed(
        self,
        user: User,
    ) -> PaginatedArticleListResponse:
        # 정렬 기준: 조회수 내림차순
        sort_column = Article.views.desc()
        per_page = 5  # 페이지당 기사 수 (1개로 설정)

        # 오늘 날짜의 시작과 끝 계산
        today_start = datetime.now(timezone(timedelta(hours=9))).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        access_condition = self.get_access_condition(user, 0)
        base_query = self.build_base_query(access_condition)
        stmt = (
            base_query
            .filter(
                Article.created_at >= today_start,  # 오늘 시작 시간 이후
                Article.created_at < today_end   # 오늘 끝 시간 이전
            )
            .order_by(sort_column)  # 조회수 기준 정렬       
            .limit(per_page)        # 페이지당 제한 (1개)
        )

        result = await SESSION.execute(stmt)
        rows = result.all()

        # Pydantic 모델로 변환하여 반환 데이터 생성
        articles = [
            ArticleSearchInListResponse.from_article(
                article=row.Article,
                blog_name = row.blog_name,
                blog_main_image_url = row.blog_main_image_url,
                article_likes=row.likes,
                article_comments=row.comments,
                user=user
            )
            for row in rows
        ]

        return PaginatedArticleListResponse(
            page=1,
            per_page=per_page,  # 1페이지에 1개
            total_count=len(articles),
            articles=articles
        )

    @transactional
    async def get_weekly_most_viewed(
        self,
        user: User  # 사용자 정보 추가
    ) -> PaginatedArticleListResponse:
        access_condition = self.get_access_condition(user, 0)  # 접근 권한 조건 추가
        # 정렬 기준: 조회수 내림차순
        sort_column = Article.views.desc()
        per_page = 5  # 페이지당 기사 수

        # 일주일 전과 오늘 날짜 계산
        week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        access_condition = self.get_access_condition(user, 0)
        base_query = self.build_base_query(access_condition)
        stmt = (
            base_query
            .filter(
                Article.created_at >= week_start,  # 오늘 시작 시간 이후
                Article.created_at < today_end   # 오늘 끝 시간 이전
            )
            .order_by(sort_column)  # 조회수 기준 정렬       
            .limit(per_page)        # 페이지당 제한 (1개)
        )
        # 쿼리 실행
        result = await SESSION.execute(stmt)
        rows = result.all()

        # Pydantic 모델로 변환하여 반환 데이터 생성
        articles = [
            ArticleSearchInListResponse.from_article(
                article=row.Article,
                blog_name=row.blog_name,
                blog_main_image_url=row.blog_main_image_url,
                article_likes=row.likes,
                article_comments=row.comments,
                user=user
            )
            for row in rows
        ]

        return PaginatedArticleListResponse(
            page=1,
            per_page=per_page,
            total_count=len(articles),
            articles=articles
        )

    
    @transactional
    async def get_articles_in_blog(
        self, blog_id: int, page: int, per_page: int, user: User
    ) -> PaginatedArticleListResponse:
        offset_val = (page - 1) * per_page

        # 접근 조건 생성
        access_condition = self.get_access_condition(user)
        base_query = self.build_base_query(access_condition)
        stmt = (
            base_query
            .filter(Article.blog_id == blog_id)
            .order_by(Article.created_at.desc())
            .offset(offset_val)
            .limit(per_page)
        )

        result = await SESSION.execute(stmt)
        rows = result.all()

        # Pydantic 모델로 변환하여 필요한 데이터만 반환
        articles = [
            ArticleSearchInListResponse.from_article(
                article=row.Article,
                blog_name=row.blog_name,
                blog_main_image_url=row.blog_main_image_url,
                article_likes=row.likes,
                article_comments=row.comments,
                user=user
            )
            for row in rows
        ]

        # 전체 개수 계산
        total_count_stmt = (
            select(func.count(func.distinct(Article.id)))
            .join(Blog, Blog.id == Article.blog_id) 
            .filter(
                Article.blog_id == blog_id,
                access_condition  # 접근 조건 필터
            )
        )
        total_count = await SESSION.scalar(total_count_stmt)

        return PaginatedArticleListResponse(
            page=page,
            per_page=per_page,
            total_count=total_count or 0,
            articles=articles,
        )

    
    @transactional
    async def get_top_articles_in_blog(
        self,
        blog_id: int,
        user: User,
        sort_by: str = "views",  # 기본 정렬 기준은 "views"
        top_n: int = 20          # 기본 상위 20개 가져오기
    ) -> PaginatedArticleListResponse:
        # 정렬 기준 설정
        if sort_by == "likes":
            sort_column = func.count(Like.id).desc()
        elif sort_by == "comments":
            sort_column = func.count(Comment.id).desc()
        elif sort_by == "views":
            sort_column = Article.views.desc()  # 조회수를 기준으로 정렬
        else:
            raise ValueError("Invalid sort_by value. Use 'likes', 'comments', or 'views'.")

        # 접근 조건 생성
        access_condition = self.get_access_condition(user, 0)
        base_query = self.build_base_query(access_condition)
        stmt = (
            base_query
            .filter(Article.blog_id == blog_id)
            .order_by(sort_column)  # 좋아요, 댓글, 조회수 기준으로 정렬
            .limit(top_n)           # 상위 N개 제한
        )

        result = await SESSION.execute(stmt)
        rows = result.all()

        # Pydantic 모델로 변환하여 필요한 데이터만 반환
        articles = [
            ArticleSearchInListResponse.from_article(
                article=row.Article,
                blog_name=row.blog_name,
                blog_main_image_url=row.blog_main_image_url,
                article_likes=row.likes,
                article_comments=row.comments,
                user=user
            )
            for row in rows
        ]

        return PaginatedArticleListResponse(
            page=1,  # 인기글은 페이지 구분 없이 한 번에 반환
            per_page=top_n,
            total_count=len(articles),
            articles=articles,
        )

        
    @transactional
    async def get_articles_in_blog_in_category(
        self,
        category_id: int,
        blog_id: int,
        user: User,
        page: int,
        per_page: int
    ) -> PaginatedArticleListResponse:

        # category_id가 0일 경우, blog의 default_category_id로 설정
        if category_id == 0:
            blog = await SESSION.get(Blog, blog_id)
            category_id = blog.default_category_id

        offset_val = (page - 1) * per_page

        # 접근 조건 생성
        access_condition = self.get_access_condition(user)
        base_query = self.build_base_query(access_condition)
        stmt = (
            base_query
            .filter(
                Article.category_id == category_id,  # category_id 필터
                Article.blog_id == blog_id
            ) 
            .offset(offset_val)
            .limit(per_page)           # 상위 N개 제한
        )
        
        # 쿼리 실행
        result = await SESSION.execute(stmt)
        rows = result.all()

        # Pydantic 모델로 변환
        articles = [
            ArticleSearchInListResponse.from_article(
                article=row.Article,
                blog_name=row.blog_name,
                blog_main_image_url=row.blog_main_image_url,
                article_likes=row.likes,
                article_comments=row.comments,
                user=user
            )
            for row in rows
        ]
        # 전체 개수 계산
        total_count_stmt = (
            select(func.count(func.distinct(Article.id)))
            .join(Blog, Blog.id == Article.blog_id)
            .filter(
                Article.category_id == category_id,
                Article.blog_id == blog_id,
                access_condition  # 접근 조건 필터 추가
            )
        )
        

        total_count = await SESSION.scalar(total_count_stmt)

        return PaginatedArticleListResponse(
            page=page,
            per_page=per_page,
            total_count=total_count or 0,
            articles=articles,
        )
  
    
    @transactional
    async def get_articles_by_words_and_blog_id(
        self,
        user: User | None,  # 이제 Optional[User]
        searching_words: str | None = None,
        blog_id: int | None = None,
        page: int = 1,
        per_page: int = 10,
        sort_by: str = "latest"   # 정렬 조건 추가: "latest", "likes", "views"
    ) -> PaginatedArticleListResponse:
        # 검색어가 없으면 빈 결과 반환
        if not searching_words:
            return PaginatedArticleListResponse(
                page=page,
                per_page=per_page,
                total_count=0,
                articles=[]
            )

        # 검색어를 공백으로 분리
        words = searching_words.split()
        search_conditions = [
            or_(
                Article.title.ilike(f"%{word}%"),
                Article.description.ilike(f"%{word}%")
            )
            for word in words
        ]
        if blog_id is not None:
            search_conditions.append(Article.blog_id == blog_id)

        offset_val = (page - 1) * per_page

        # 로그인 여부에 따른 접근 조건 설정
        if user:
            # 기존 get_access_condition()를 사용 (예: 작성자 본인의 비밀글은 포함)
            if blog_id is None:
                access_condition = self.get_access_condition(user, 0)
            else:
                access_condition = self.get_access_condition(user)
        else:
            # 로그인하지 않은 경우, 모든 비밀글(secret=1)은 제외
            access_condition = (Article.secret == 0)

        base_query = self.build_base_query(access_condition)

        # 정렬 조건에 따른 ORDER BY 절 구성
        if sort_by == "latest":
            order_clause = Article.created_at.desc()
        elif sort_by == "likes":
            # build_base_query()에서 'likes' 집계 컬럼이 함께 선택되었다고 가정
            order_clause = text("likes DESC")
        elif sort_by == "views":
            order_clause = Article.views.desc()
        else:
            order_clause = Article.created_at.desc()

        stmt = (
            base_query
            .where(and_(*search_conditions))
            .order_by(order_clause)
            .offset(offset_val)
            .limit(per_page)
        )

        result = await SESSION.execute(stmt)
        rows = result.all()

        articles = [
            ArticleSearchInListResponse.from_article(
                article=row.Article,
                blog_name=row.blog_name,
                blog_main_image_url=row.blog_main_image_url,
                article_likes=row.likes,
                article_comments=row.comments,
                user=user  # user가 없을 수도 있음; DTO 내부에서 비밀글 처리 로직이 작동해야 함
            )
            for row in rows
        ]

        total_count_stmt = (
            select(func.count(func.distinct(Article.id)))
            .join(Blog, Blog.id == Article.blog_id)
            .filter(access_condition)
            .where(and_(*search_conditions))
        )
        total_count = await SESSION.scalar(total_count_stmt)

        return PaginatedArticleListResponse(
            page=page,
            per_page=per_page,
            total_count=total_count or 0,
            articles=articles,
        )
    
    @transactional
    async def get_articles_of_subscriptions(
        self, user: User, user_blog: Blog, page: int, per_page: int
    ) -> PaginatedArticleListResponse:
        offset_val = (page - 1) * per_page

        # 구독한 블로그 ID 가져오기
        subscribed_blogs_stmt = (
            select(Subscription.subscribed_id)
            .filter(Subscription.subscriber_id == user_blog.id)  # 사용자의 블로그 ID를 기준으로 필터링
        )
        subscribed_ids_result = await SESSION.scalars(subscribed_blogs_stmt)
        subscribed_ids = subscribed_ids_result.all()

        if not subscribed_ids:
            # 구독한 블로그가 없으면 빈 결과 반환
            return PaginatedArticleListResponse(
                page=page,
                per_page=per_page,
                total_count=0,
                articles=[]
            )

        # 접근 조건 추가
        access_condition = self.get_access_condition(user, 0)
        base_query = self.build_base_query(access_condition)
        stmt = (
            base_query
            .filter(
                Article.blog_id.in_(subscribed_ids))            
            .order_by(Article.created_at.desc())
            .offset(offset_val)
            .limit(per_page)           # 상위 N개 제한
        )

        result = await SESSION.execute(stmt)
        rows = result.all()

        # Pydantic 모델로 변환하여 필요한 데이터만 반환
        articles = [
            ArticleSearchInListResponse.from_article(
                article=row.Article,
                blog_name=row.blog_name,
                blog_main_image_url=row.blog_main_image_url,
                article_likes=row.likes,
                article_comments=row.comments,
                user=user
            )
            for row in rows
        ]

        # 전체 개수 계산
        total_count_stmt = (
            select(func.count(func.distinct(Article.id)))
            .join(Blog, Blog.id == Article.blog_id) 
            .filter(
                Article.blog_id.in_(subscribed_ids),  # 구독한 블로그의 Article만 필터
                access_condition  # 접근 조건 필터링 추가
            )
        )
        total_count = await SESSION.scalar(total_count_stmt)

        return PaginatedArticleListResponse(
            page=page,
            per_page=per_page,
            total_count=total_count or 0,
            articles=articles,
        )

    @transactional
    async def get_articles_by_problem_number(
        self,
        problem_number: int,
        user: User | None,  # Optional 사용자
        page: int = 1,
        per_page: int = 10,
        sort_by: str = "latest"
    ) -> PaginatedArticleListResponse:
        offset_val = (page - 1) * per_page

        if user:
            access_condition = self.get_access_condition(user, 0)
        else:
            access_condition = (Article.secret == 0)

        base_query = self.build_base_query(access_condition)

        if sort_by == "latest":
            order_clause = Article.created_at.desc()
        elif sort_by == "likes":
            order_clause = text("likes DESC")
        elif sort_by == "views":
            order_clause = Article.views.desc()
        else:
            order_clause = Article.created_at.desc()

        stmt = (
            base_query
            .filter(
                func.json_contains(func.ifnull(Article.problem_numbers, '[]'), str(problem_number))
            )
            .order_by(order_clause)
            .offset(offset_val)
            .limit(per_page)
        )

        result = await SESSION.execute(stmt)
        rows = result.all()

        articles = [
            ArticleSearchInListResponse.from_article(
                article=row.Article,
                blog_name=row.blog_name,
                blog_main_image_url=row.blog_main_image_url,
                article_likes=row.likes,
                article_comments=row.comments,
                user=user
            )
            for row in rows
        ]

        total_count_stmt = (
            select(func.count(func.distinct(Article.id)))
            .join(Blog, Blog.id == Article.blog_id)
            .filter(
                func.json_contains(func.ifnull(Article.problem_numbers, '[]'), str(problem_number)),
                access_condition
            )
        )
        total_count = await SESSION.scalar(total_count_stmt)

        return PaginatedArticleListResponse(
            page=page,
            per_page=per_page,
            total_count=total_count or 0,
            articles=articles,
        )
