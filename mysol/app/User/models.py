from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mysol.database.common import Base, intpk

if TYPE_CHECKING:
    from mysol.app.Blog.models import Blog

class User(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    blogs: Mapped["Blog"] = relationship(
        "Blog",
        lazy="selectin", 
        back_populates="user", 
        cascade="all, delete-orphan",
        uselist=False
        )

class BlockedToken(Base):
    __tablename__ = "blocked_tokens"

    token_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
