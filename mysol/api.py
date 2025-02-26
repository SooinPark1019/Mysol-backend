from fastapi import APIRouter

from mysol.app.User.views import user_router
from mysol.app.Blog.views import blog_router

api_router = APIRouter()

api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(blog_router, prefix="/blogs", tags=["blogs"])