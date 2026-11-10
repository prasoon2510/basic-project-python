from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class ProductCreate(BaseModel):

    name: str = Field(min_length=2, max_length=150)

    description: str | None = None

    price: float = Field(gt=0)

    sku: str = Field(min_length=3, max_length=100)

    category_id: int = Field(gt=0)


class ProductUpdate(BaseModel):

    name: str | None = Field(default=None, min_length=2, max_length=150)

    description: str | None = None

    price: float | None = Field(default=None, gt=0)

    sku: str | None = Field(default=None, min_length=3, max_length=100)

    category_id: int | None = Field(default=None, gt=0)


class ProductResponse(BaseModel):

    id: int

    name: str

    description: str | None

    price: float

    sku: str

    category_id: int

    is_active: bool

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)