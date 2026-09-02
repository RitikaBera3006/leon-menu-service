from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    id: str


class BaseResponseSchema(IDSchema, TimestampSchema):
    pass


class MessageResponse(BaseModel):
    message: str


class DetailResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    version: str


class DataResponse(BaseModel, Generic[T]):
    data: T
    message: str | None = None
