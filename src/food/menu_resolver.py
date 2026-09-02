"""Menu resolution helpers for store-scoped queries.

Replicated from leon-api's src/food/menu_resolver.py — only the two lookups
this service's endpoints need (the original also has helpers for resolving a
Centegra menu_source_id and reading price-level ids, both tied to leon-api's
ordering/pricing flow and out of scope here).

Both queries below spell out the full eager-load chain explicitly via
selectinload() rather than relying on each relationship's mapper-level
``lazy="selectin"`` default. The object graph has a cycle (Product ->
modifier_group_links -> modifier_group -> option_links -> product), and
SQLAlchemy's automatic default-eager-load cascading stops at a cycle to avoid
infinite recursion — silently leaving that last ``product`` hop un-loaded.
Under AsyncSession that surfaces as a MissingGreenlet error the first time
something (e.g. Pydantic's model_validate) touches the attribute outside the
original await. Spelling out the chain forces that specific hop to load too.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.food.models import (
    CategoryProduct,
    Menu,
    MenuCategory,
    ModifierGroup,
    ModifierGroupOption,
    Product,
    ProductModifierGroup,
)

_MENU_LOAD_OPTIONS = (
    selectinload(Menu.availability),
    selectinload(Menu.categories)
    .selectinload(MenuCategory.product_links)
    .selectinload(CategoryProduct.product)
    .selectinload(Product.modifier_group_links)
    .selectinload(ProductModifierGroup.modifier_group)
    .selectinload(ModifierGroup.option_links)
    .selectinload(ModifierGroupOption.product),
)


async def get_menu_by_source_id_for_store(
    session: AsyncSession, store_id: str, menu_source_id: int
) -> Menu | None:
    """Look up a menu by its small integer `source_id` (the Centegra menu
    number, e.g. 1, 2, 3 — not the internal UUID `id`), scoped to store_id.

    Returns None (surfaced by the caller as 404) both when the menu doesn't
    exist and when it exists but belongs to a different store — a
    menu_source_id from another store is not this store's data, so it isn't
    found here.
    """
    result = await session.execute(
        select(Menu)
        .where(Menu.source_id == menu_source_id, Menu.store_id == store_id)
        .options(*_MENU_LOAD_OPTIONS)
    )
    return result.unique().scalar_one_or_none()


async def get_menus_for_store(session: AsyncSession, store_id: str) -> list[Menu]:
    """Return every menu belonging to a store, ordered by source_id, each fully
    loaded (categories, products, modifier groups, prices, availability)."""
    result = await session.execute(
        select(Menu)
        .where(Menu.store_id == store_id)
        .order_by(Menu.source_id)
        .options(*_MENU_LOAD_OPTIONS)
    )
    return list(result.unique().scalars().all())
