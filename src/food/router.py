"""Menu router — the service's two endpoints: all menus for a store, and one menu by id."""

import logging

from fastapi import APIRouter

from src.food.dependencies import MenuServiceDep
from src.food.schemas import MenuResponse, StoreMenusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stores/{store_id}/menus", tags=["Menu"])


@router.get(
    "",
    response_model=StoreMenusResponse,
    summary="Get all menus for a store",
    description="Returns every menu configured for the given store id, each with its "
    "categories and products.",
)
async def get_store_menus(store_id: str, menu_service: MenuServiceDep) -> StoreMenusResponse:
    return await menu_service.get_store_menus(store_id)


@router.get(
    "/{menu_id}",
    response_model=MenuResponse,
    summary="Get a single menu for a store",
    description="Returns one menu belonging to the given store id, identified by its "
    "small integer `source_id` (e.g. 1, 2, 3 — the Centegra menu number, also shown as "
    "`source_id` on each menu returned by the list endpoint), with its categories and "
    "products.",
)
async def get_store_menu(
    store_id: str, menu_id: int, menu_service: MenuServiceDep
) -> MenuResponse:
    return await menu_service.get_menu(store_id, menu_id)
