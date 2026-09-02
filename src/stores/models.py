"""Store model.

This service owns its own `stores` table (see alembic/versions/
0001_initial_menu_schema.py) in its own database — a copy of the store
identity leon-api's `stores` table carries, not a live read against leon-api's
Postgres. It intentionally excludes leon-api's Centegra POS credential columns
(centegra_site_id / centegra_till_id / centegra_till_secure_key): those are a
POS-integration/sync concern that belongs solely to leon-api, not to a
menu-serving microservice.
"""

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import BaseModel


class Store(BaseModel):
    __tablename__ = "stores"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    area: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    original_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
