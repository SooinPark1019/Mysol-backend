from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, String, UniqueConstraint, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mysol.database.common import Base, intpk

if TYPE_CHECKING:
    from mysol.app.blog.models import Blog
    from mysol.app.article.models import Article


class Category(Base):
    __tablename__ = "category"
    __table_args__ = (
        CheckConstraint("level IN (1, 2)", name="valid_category_level"),       # level은 1(상위) 또는 2(하위)만 허용
    )

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(50), index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    blog_id: Mapped[int] = mapped_column(ForeignKey("blog.id"))
    

    blog: Mapped["Blog"] = relationship("Blog", back_populates="categories")
    articles : Mapped[list["Article"]] = relationship("Article", back_populates="category")

    # 양방향 관계 설정
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id"), nullable=True)
    parent: Mapped["Category"] = relationship(
        "Category",
        back_populates="children",
        remote_side="Category.id"  # 충돌 방지를 위해 명시
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )


    