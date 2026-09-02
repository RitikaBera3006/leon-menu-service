"""MenuCategory model — mirrors leon-api's src/category/models.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import BaseModel

if TYPE_CHECKING:
    from src.food.models import CategoryProduct, Menu


class MenuCategory(BaseModel):
    """Category within a menu. Named 'menu_categories' to avoid conflict with
    the storefront's own 'categories' table."""

    __tablename__ = "menu_categories"

    store_id: Mapped[str] = mapped_column(
        String(256), ForeignKey("stores.original_id"), nullable=True, index=True
    )

    menu_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_combo_bucket: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    menu: Mapped[Menu] = relationship(back_populates="categories")
    product_links: Mapped[list[CategoryProduct]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CategoryProduct.sort_order",
    )

    __table_args__ = (
        Index(
            "ix_menu_categories_name_lower",
            "store_id",
            func.lower(func.trim(name)),
        ),
    )

    def __repr__(self) -> str:
        return f"<MenuCategory id={self.id} name={self.name!r}>"
