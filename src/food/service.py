"""Menu service — read-only queries over the shared leon-api menu tables.

Serialization walks the object graph loaded by `src.food.menu_resolver`
(menu -> categories -> products -> modifier groups -> options), which spells
out its eager-load chain explicitly to work around a relationship cycle — see
that module's docstring.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.food.exceptions import MenuNotFoundException, StoreNotFoundException
from src.food.menu_resolver import get_menu_by_source_id_for_store, get_menus_for_store
from src.food.models import CategoryProduct, Menu, ModifierGroup, ModifierGroupOption, Product
from src.food.schemas import (
    MenuAvailabilityResponse,
    MenuCategoryResponse,
    MenuProductResponse,
    MenuResponse,
    ModifierGroupResponse,
    ModifierOptionResponse,
    ProductPriceResponse,
    StoreMenusResponse,
)
from src.stores.models import Store

logger = logging.getLogger(__name__)


def _serialize_modifier_option(option: ModifierGroupOption) -> ModifierOptionResponse:
    return ModifierOptionResponse(
        id=option.product.id,
        source_id=option.product.source_id,
        name=option.product.name,
        prices=[ProductPriceResponse.model_validate(p) for p in option.product.prices],
    )


def _serialize_modifier_group(group: ModifierGroup) -> ModifierGroupResponse:
    return ModifierGroupResponse(
        id=group.id,
        name=group.name,
        min_count=group.min_count,
        max_count=group.max_count,
        show_expanded=group.show_expanded,
        pick_same_option=group.pick_same_option,
        is_size_variant=group.is_size_variant,
        options=[_serialize_modifier_option(link) for link in group.option_links],
    )


def _serialize_product(product: Product) -> MenuProductResponse:
    return MenuProductResponse(
        id=product.id,
        source_id=product.source_id,
        plu=product.plu,
        name=product.name,
        description=product.description,
        kcal=product.kcal,
        kj=product.kj,
        image_url=product.image_url,
        allergens=product.allergens,
        dietary_options=product.dietary_options,
        is_active=product.is_active,
        is_combo=product.is_combo,
        prices=[ProductPriceResponse.model_validate(p) for p in product.prices],
        modifier_groups=[
            _serialize_modifier_group(link.modifier_group) for link in product.modifier_group_links
        ],
    )


def _serialize_product_link(link: CategoryProduct) -> MenuProductResponse:
    return _serialize_product(link.product)


def _serialize_menu(menu: Menu) -> MenuResponse:
    return MenuResponse(
        id=menu.id,
        store_id=menu.store_id,
        source_id=menu.source_id,
        name=menu.name,
        title=menu.title,
        subtitle=menu.subtitle,
        pickup_enabled=menu.pickup_enabled,
        delivery_enabled=menu.delivery_enabled,
        availability=[MenuAvailabilityResponse.model_validate(a) for a in menu.availability],
        categories=[
            MenuCategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                image_url=category.image_url,
                sort_order=category.sort_order,
                is_combo_bucket=category.is_combo_bucket,
                products=[
                    _serialize_product_link(link)
                    for link in category.product_links
                    if link.product.is_active
                ],
            )
            for category in menu.categories
        ],
    )


class MenuService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_store_or_raise(self, store_id: str) -> Store:
        result = await self.db.execute(select(Store).where(Store.original_id == store_id))
        store = result.scalar_one_or_none()
        if store is None:
            raise StoreNotFoundException(store_id)
        return store

    async def get_store_menus(self, store_id: str) -> StoreMenusResponse:
        """Return every menu configured for `store_id`, ordered by source_id."""
        await self._get_store_or_raise(store_id)

        menus = await get_menus_for_store(self.db, store_id)

        logger.info("[FOOD] get-store-menus store_id=%s count=%d", store_id, len(menus))
        return StoreMenusResponse(
            store_id=store_id,
            count=len(menus),
            menus=[_serialize_menu(menu) for menu in menus],
        )

    async def get_menu(self, store_id: str, menu_source_id: int) -> MenuResponse:
        """Return the single menu identified by `menu_source_id`, scoped to `store_id`."""
        await self._get_store_or_raise(store_id)

        menu = await get_menu_by_source_id_for_store(self.db, store_id, menu_source_id)
        if menu is None:
            raise MenuNotFoundException(menu_source_id, store_id)

        logger.info("[FOOD] get-menu store_id=%s menu_source_id=%s", store_id, menu_source_id)
        return _serialize_menu(menu)
