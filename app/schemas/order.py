from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):

    product_id: int = Field(gt=0)

    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):

    shipping_address: str = Field(
        min_length=5,
        max_length=500
    )

    items: list[OrderItemCreate] = Field(
        min_length=1
    )


class OrderUpdate(BaseModel):

    status: str = Field(
        min_length=3,
        max_length=50
    )


class OrderItemResponse(BaseModel):

    id: int

    product_id: int

    quantity: int

    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):

    id: int

    user_id: int

    total_amount: float

    status: str

    shipping_address: str

    created_at: datetime

    order_items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)