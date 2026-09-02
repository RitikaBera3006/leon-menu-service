from src.exceptions import NotFoundException


class StoreNotFoundException(NotFoundException):
    def __init__(self, store_id: str) -> None:
        super().__init__(detail=f"Store '{store_id}' not found.")


class MenuNotFoundException(NotFoundException):
    def __init__(self, menu_source_id: int, store_id: str) -> None:
        super().__init__(detail=f"Menu '{menu_source_id}' not found for store '{store_id}'.")
