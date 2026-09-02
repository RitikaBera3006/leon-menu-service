"""Normalized SQLAlchemy models for the menu domain.

This service owns its own copy of these tables (menus, menu_availability,
menu_categories, category_products, products, product_prices,
modifier_groups, product_modifier_groups, modifier_group_options) in its own
database, migrated by alembic/versions/0001_initial_menu_schema.py — it is
not reading leon-api's Postgres. The shape mirrors leon-api's `src/food`
models (src/food/models.py there) minus the search-only columns (embedding,
search_vector, concept_tags, popularity) leon-api uses for its AI
ordering-agent product search, which is a different concern from serving a
menu's structure.
"""

from __future__ import annotations

from sqlalchemy import (
    ARRAY,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.category.models import MenuCategory
from src.database import Base
from src.models import BaseModel

# Import Store so SQLAlchemy registers the stores table before Menu/Product FK resolution.
from src.stores.models import Store  # noqa: F401


class Menu(BaseModel):
    __tablename__ = "menus"

    store_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("stores.original_id"), nullable=False, index=True
    )
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    subtitle: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    pickup_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    delivery_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    availability: Mapped[list[MenuAvailability]] = relationship(
        back_populates="menu", cascade="all, delete-orphan", lazy="selectin"
    )
    categories: Mapped[list[MenuCategory]] = relationship(
        back_populates="menu",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="MenuCategory.sort_order",
    )

    __table_args__ = (UniqueConstraint("store_id", "source_id", name="uq_menu_store_source"),)

    def __repr__(self) -> str:
        return f"<Menu id={self.id} name={self.name!r} store={self.store_id}>"


class MenuAvailability(Base):
    __tablename__ = "menu_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[str] = mapped_column(Time, nullable=False)
    end_time: Mapped[str] = mapped_column(Time, nullable=False)

    menu: Mapped[Menu] = relationship(back_populates="availability")

    def __repr__(self) -> str:
        return f"<MenuAvailability menu={self.menu_id} day={self.day_of_week}>"


class Product(BaseModel):
    __tablename__ = "products"

    store_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("stores.original_id"), nullable=False, index=True
    )
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    plu: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    kcal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kj: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    allergens: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    dietary_options: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_combo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    prices: Mapped[list[ProductPrice]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )
    modifier_group_links: Mapped[list[ProductModifierGroup]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductModifierGroup.sort_order",
    )

    __table_args__ = (
        UniqueConstraint("store_id", "source_id", name="uq_product_store_source"),
        Index(
            "ix_products_store_active_role",
            "store_id",
            "is_active",
            postgresql_where=(is_active.is_(True)),
        ),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} source_id={self.source_id} name={self.name!r}>"


class ProductPrice(Base):
    __tablename__ = "product_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price_type: Mapped[str] = mapped_column(String(32), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    pricing_net: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    price_level_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped[Product] = relationship(back_populates="prices")

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "price_type",
            "price_level_id",
            name="uq_product_price_type_level",
        ),
    )


class CategoryProduct(Base):
    """Through-table: which products appear in which categories."""

    __tablename__ = "category_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("menu_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    category: Mapped[MenuCategory] = relationship(back_populates="product_links")
    product: Mapped[Product] = relationship(lazy="selectin")

    __table_args__ = (UniqueConstraint("category_id", "product_id", name="uq_category_product"),)


class ModifierGroup(BaseModel):
    __tablename__ = "modifier_groups"

    source_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    min_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    show_expanded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pick_same_option: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_size_variant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    option_links: Mapped[list[ModifierGroupOption]] = relationship(
        back_populates="modifier_group",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ModifierGroupOption.sort_order",
    )

    def __repr__(self) -> str:
        return f"<ModifierGroup id={self.id} name={self.name!r}>"


class ProductModifierGroup(Base):
    """Through-table: which modifier groups are attached to which products."""

    __tablename__ = "product_modifier_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    modifier_group_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("modifier_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_in_dish_extra: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    product: Mapped[Product] = relationship(back_populates="modifier_group_links")
    modifier_group: Mapped[ModifierGroup] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("product_id", "modifier_group_id", name="uq_product_modifier_group"),
    )


class ModifierGroupOption(Base):
    """Through-table: which products are options within a modifier group."""

    __tablename__ = "modifier_group_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    modifier_group_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("modifier_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    modifier_group: Mapped[ModifierGroup] = relationship(back_populates="option_links")
    product: Mapped[Product] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("modifier_group_id", "product_id", name="uq_modifier_group_option"),
    )
