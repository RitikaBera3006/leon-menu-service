# Leon Menu Service

A standalone FastAPI microservice extracted from `leon-api`'s menu domain
(`src/food`, `src/category`, `src/stores`). It follows the same project
layout and conventions as `leon-api` (config via `pydantic-settings`,
`AppException`-based error handling, async SQLAlchemy + Alembic, Scalar docs)
but is scoped to a single job: serving menus.

It owns **its own Postgres database** (see `alembic/versions/`) — a copy of
the store/menu/category/product shape leon-api's database carries, not a
live connection into leon-api's own Postgres. leon-api's `src/food` module
bundles two different concerns: menu structure (categories, products,
prices, modifier groups) and an AI ordering-agent search/cart-resolution
engine (embeddings, LLM tagging, session- and cart-bound endpoints). This
service replicates only the first — the POS-sync/ingestion pipeline
(`src/food/ingestion.py`, the write path in `db_adapter.py`) intentionally
stays leon-api's alone, since two services writing the same data would race.

## Endpoints

- `GET /api/v1/stores/{store_id}/menus` — all menus for a store.
- `GET /api/v1/stores/{store_id}/menus/{menu_id}` — a single menu (by the
  menu's `id`, as returned from the endpoint above) belonging to that store.

Both return 404 (`{"detail": "..."}`) if the store, or the menu, doesn't
exist. Each menu includes its categories, each category its products, and
each product its prices and modifier groups (with their options).

## Running locally

```bash
cp .env.example .env   # then set DATABASE_URL to your own Postgres
python -m venv .venv
.venv/Scripts/activate  # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements/dev.txt
alembic upgrade head     # creates stores/menus/products/... in your database
uvicorn src.main:app --reload
```

Or via Docker Compose:

```bash
docker compose up --build
```

## Project layout

```
alembic/                # migrations — this service's own schema
src/
  config.py        # Settings (env-driven)
  database.py       # async engine/session
  models.py          # BaseModel/TimestampMixin/UUIDMixin shared by all tables
  schemas.py         # shared response schemas
  exceptions.py       # AppException family + FastAPI exception handlers
  dependencies.py     # DBSession dependency
  core/logging.py     # structured logging setup
  api/v1/router.py    # API v1 router aggregation
  stores/models.py    # Store
  category/models.py  # MenuCategory
  food/                # the menu domain (named to match leon-api's src/food)
    menu_resolver.py    # store/menu lookups with the full eager-load chain
    models.py            # Menu, Product, ProductPrice, ModifierGroup, ...
    schemas.py
    service.py
    dependencies.py
    router.py             # the two endpoints
    exceptions.py
```
