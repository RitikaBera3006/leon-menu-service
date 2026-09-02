from typing import Annotated

from fastapi import Depends

from src.dependencies import DBSession
from src.food.service import MenuService


def get_menu_service(db: DBSession) -> MenuService:
    return MenuService(db)


MenuServiceDep = Annotated[MenuService, Depends(get_menu_service)]
