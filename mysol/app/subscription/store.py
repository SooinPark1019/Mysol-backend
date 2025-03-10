from fastapi import Depends
from sqlalchemy import select, func, case
from typing import List
from mysol.app.subscription.models import Subscription
from mysol.app.blog.models import Blog
from mysol.database.annotation import transactional
from mysol.database.connection import SESSION
from mysol.app.subscription.errors import (
    SubscriptionAlreadyExistsError,
    BlogNotFoundError,
    SubscriptionNotFoundError,
    SelfSubscriptionError
)


class SubscriptionStore:
    @transactional
    async def add_subscription(self, subscriber_id: int, subscribed_id: int) -> Subscription:
        """
        구독 추가 기능: 특정 블로그가 다른 블로그를 구독합니다.
        """
        #자기 자신을 구독할 경우 에러
        if subscribed_id==subscriber_id:
            raise SelfSubscriptionError
        # 구독할 블로그와 구독자가 존재하는지 확인
        subscriber_blog = await SESSION.scalar(select(Blog).filter(Blog.id == subscriber_id))
        subscribed_blog = await SESSION.scalar(select(Blog).filter(Blog.id == subscribed_id))

        if not subscriber_blog or not subscribed_blog:
            raise BlogNotFoundError

        # 이미 존재하는 구독 관계인지 확인
        existing_subscription_query = select(Subscription).filter(
            Subscription.subscriber_id == subscriber_id,
            Subscription.subscribed_id == subscribed_id,
        )
        existing_subscription = await SESSION.scalar(existing_subscription_query)
        if existing_subscription:
            raise SubscriptionAlreadyExistsError

        # 새로운 구독 생성
        subscription = Subscription(
            subscriber_id=subscriber_id,
            subscribed_id=subscribed_id,
        )
        SESSION.add(subscription)
        await SESSION.flush()
        await SESSION.refresh(subscription)

        return subscription
    
    @transactional
    async def delete_subscription(self, subscriber_id: int, subscribed_id: int) -> bool:
        """
        구독 관계 삭제
        """
        # 구독 관계 존재 여부 확인
        query = (
            select(Subscription)
            .filter(
                Subscription.subscriber_id == subscriber_id,
                Subscription.subscribed_id == subscribed_id
            )
        )
        subscription = await SESSION.scalar(query)
        if not subscription:
            raise SubscriptionNotFoundError

        # 구독 관계 삭제
        await SESSION.delete(subscription)
        await SESSION.flush()
        return True
    
    async def get_paginated_subscribed_blogs(self, subscriber_id: int, page: int, per_page: int) -> list[Blog]:
        """
        내가 구독 중인 블로그들의 정보 반환(페이지네이션)
        """
        offset_val = (page - 1) * per_page

        query=(
            select(Blog)
            .join(Subscription, Subscription.subscribed_id == Blog.id)
            .filter(Subscription.subscriber_id == subscriber_id)
            .offset(offset_val)
            .limit(per_page)
        )

        results = await SESSION.scalars(query)
        return list(results)
    
    async def get_paginated_subscriber_blogs(self, subscribed_id: int, page: int, per_page: int) -> list[Blog]:
        """
        나를 구독 중인 블로그들의 정보 반환(페이지네이션)
        """
        
        offset_val = (page - 1) * per_page

        query=(
            select(Blog)
            .join(Subscription, Subscription.subscriber_id == Blog.id)
            .filter(Subscription.subscribed_id == subscribed_id)
            .offset(offset_val)
            .limit(per_page)
        )

        results = await SESSION.scalars(query)
        return list(results)
    
    async def get_subscribed_blog_count(self, subscriber_id: int) -> int :
        query = (
            select(func.count(case((Subscription.subscriber_id == subscriber_id, 1))))
        )
        count = await SESSION.scalar(query)
        return count or 0
    
    async def get_subscriber_blog_count(self, subscribed_id: int) -> int :
        query = (
            select(func.count(case((Subscription.subscribed_id == subscribed_id, 1))))
        )
        count = await SESSION.scalar(query)
        return count or 0
    
    async def get_subscribed_blog_ids(self, subscriber_id: int) -> List[int]:
        """
        내가 구독 중인 블로그들의 아이디 반환
        """
        print(subscriber_id)
        query = (
            select(Blog.id)
            .join(Subscription, Subscription.subscribed_id == Blog.id)
            .filter(Subscription.subscriber_id == subscriber_id)
        )
        result = await SESSION.scalars(query)
        return result.all()  # 리스트로 반환
    
    async def get_subscriber_blog_ids(self, subscribed_id: int) -> List[int]:
        """
        나를 구독한 블로그들의 아이디 반환
        """
        query = (
            select(Blog.id)
            .join(Subscription, Subscription.subscriber_id == Blog.id)
            .filter(Subscription.subscribed_id == subscribed_id)
        )
        result = await SESSION.scalars(query)
        return result.all()  # 리스트로 반환
    
    async def get_subscription(self, subscriber_id: int, subscribed_id: int) -> Subscription | None:
        """
        특정 구독 관계 반환
        """
        query = select(Subscription).filter(
            Subscription.subscriber_id == subscriber_id,
            Subscription.subscribed_id == subscribed_id
        )
        return await SESSION.scalar(query)
