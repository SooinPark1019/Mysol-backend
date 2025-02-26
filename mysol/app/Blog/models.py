from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, UniqueConstraint, DateTime, func, Integer
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mysol.database.common import Base, intpk

if TYPE_CHECKING:
    from mysol.app.User.models import User

class Blog(Base):
    __tablename__ = "blog"
    __table_args__ = (
        UniqueConstraint("user_id", name="unique_user_blog"),
    )

    id: Mapped[intpk]
    blog_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="blogs")