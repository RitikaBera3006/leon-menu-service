from src.schemas import BaseSchema


class ProductPriceResponse(BaseSchema):
    price_type: str
    price: float
    tax_rate: float
    pricing_net: bool
    price_level_id: int


class ModifierOptionResponse(BaseSchema):
    """A selectable option within a modifier group — itself a product (e.g. 'Extra cheese')."""

    id: str
    source_id: int
    name: str
    prices: list[ProductPriceResponse]


class ModifierGroupResponse(BaseSchema):
    id: str
    name: str
    min_count: int
    max_count: int
    show_expanded: bool
    pick_same_option: bool
    is_size_variant: bool
    options: list[ModifierOptionResponse]


class MenuProductResponse(BaseSchema):
    id: str
    source_id: int
    plu: int
    name: str
    description: str
    kcal: int | None
    kj: int | None
    image_url: str | None
    allergens: list[str]
    dietary_options: list[str]
    is_active: bool
    is_combo: bool
    prices: list[ProductPriceResponse]
    modifier_groups: list[ModifierGroupResponse]


class MenuCategoryResponse(BaseSchema):
    id: str
    name: str
    description: str | None
    image_url: str | None
    sort_order: int
    is_combo_bucket: bool
    products: list[MenuProductResponse]


class MenuAvailabilityResponse(BaseSchema):
    day_of_week: int
    start_time: str
    end_time: str


class MenuResponse(BaseSchema):
    id: str
    store_id: str
    source_id: int
    name: str
    title: str
    subtitle: str
    pickup_enabled: bool
    delivery_enabled: bool
    availability: list[MenuAvailabilityResponse]
    categories: list[MenuCategoryResponse]


class StoreMenusResponse(BaseSchema):
    store_id: str
    count: int
    menus: list[MenuResponse]
