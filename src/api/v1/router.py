from fastapi import APIRouter

from src.food.router import router as menu_router

api_router = APIRouter()

api_router.include_router(menu_router)
