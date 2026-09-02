"""Initial menu schema — stores, menus, categories, products, modifier groups.

Revision ID: 0001_initial_menu_schema
Revises:
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_menu_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("area", sa.String(128), nullable=True),
        sa.Column("original_id", sa.String(64), nullable=True),
        sa.Column("status", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("original_id", name="uq_stores_original_id"),
    )
    op.create_index("ix_stores_area", "stores", ["area"])
    op.create_index("ix_stores_original_id", "stores", ["original_id"])

    op.create_table(
        "menus",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("store_id", sa.String(64), sa.ForeignKey("stores.original_id"), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("title", sa.String(256), nullable=False, server_default=""),
        sa.Column("subtitle", sa.String(256), nullable=False, server_default=""),
        sa.Column("pickup_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("delivery_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("pickup_price_level_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivery_price_level_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("modifier_pickup_price_level_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("modifier_delivery_price_level_id", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("store_id", "source_id", name="uq_menu_store_source"),
    )
    op.create_index("ix_menus_store_id", "menus", ["store_id"])
    op.create_index("ix_menus_source_id", "menus", ["source_id"])

    op.create_table(
        "menu_availability",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "menu_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("menus.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
    )
    op.create_index("ix_menu_availability_menu_id", "menu_availability", ["menu_id"])

    op.create_table(
        "menu_categories",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("store_id", sa.String(256), sa.ForeignKey("stores.original_id"), nullable=True),
        sa.Column(
            "menu_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("menus.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(2048), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_combo_bucket", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_menu_categories_store_id", "menu_categories", ["store_id"])
    op.create_index("ix_menu_categories_menu_id", "menu_categories", ["menu_id"])
    op.execute(
        "CREATE INDEX ix_menu_categories_name_lower ON menu_categories "
        "(store_id, lower(trim(name)))"
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("store_id", sa.String(64), sa.ForeignKey("stores.original_id"), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("plu", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("kcal", sa.Integer(), nullable=True),
        sa.Column("kj", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(2048), nullable=True),
        sa.Column("image_source_url", sa.String(2048), nullable=True),
        sa.Column("allergens", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column(
            "dietary_options", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"
        ),
        sa.Column("attributes", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_combo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("combo_standalone_total", sa.Numeric(10, 2), nullable=True),
        sa.Column("combo_savings", sa.Numeric(10, 2), nullable=True),
        sa.UniqueConstraint("store_id", "source_id", name="uq_product_store_source"),
    )
    op.create_index("ix_products_store_id", "products", ["store_id"])
    op.create_index("ix_products_source_id", "products", ["source_id"])
    op.create_index("ix_products_store_active", "products", ["store_id", "is_active"])
    op.create_index(
        "ix_products_allergens_gin", "products", ["allergens"], postgresql_using="gin"
    )
    op.create_index(
        "ix_products_dietary_options_gin", "products", ["dietary_options"], postgresql_using="gin"
    )
    op.create_index(
        "ix_products_attributes_gin", "products", ["attributes"], postgresql_using="gin"
    )

    op.create_table(
        "product_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("price_type", sa.String(32), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("pricing_net", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("price_level_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("default_tax_rate_id", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "product_id", "price_type", "price_level_id", name="uq_product_price_type_level"
        ),
    )
    op.create_index("ix_product_prices_product_id", "product_prices", ["product_id"])

    op.create_table(
        "category_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("menu_categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("category_id", "product_id", name="uq_category_product"),
    )
    op.create_index("ix_category_products_category_id", "category_products", ["category_id"])
    op.create_index("ix_category_products_product_id", "category_products", ["product_id"])

    op.create_table(
        "modifier_groups",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("min_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("show_expanded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pick_same_option", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_size_variant", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_modifier_groups_source_id", "modifier_groups", ["source_id"])

    op.create_table(
        "product_modifier_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "modifier_group_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("modifier_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_in_dish_extra", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("product_id", "modifier_group_id", name="uq_product_modifier_group"),
    )
    op.create_index(
        "ix_product_modifier_groups_product_id", "product_modifier_groups", ["product_id"]
    )
    op.create_index(
        "ix_product_modifier_groups_modifier_group_id",
        "product_modifier_groups",
        ["modifier_group_id"],
    )

    op.create_table(
        "modifier_group_options",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "modifier_group_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("modifier_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "modifier_group_id", "product_id", name="uq_modifier_group_option"
        ),
    )
    op.create_index(
        "ix_modifier_group_options_modifier_group_id",
        "modifier_group_options",
        ["modifier_group_id"],
    )
    op.create_index(
        "ix_modifier_group_options_product_id", "modifier_group_options", ["product_id"]
    )


def downgrade() -> None:
    op.drop_table("modifier_group_options")
    op.drop_table("product_modifier_groups")
    op.drop_table("modifier_groups")
    op.drop_table("category_products")
    op.drop_table("product_prices")
    op.drop_table("products")
    op.drop_table("menu_categories")
    op.drop_table("menu_availability")
    op.drop_table("menus")
    op.drop_table("stores")
