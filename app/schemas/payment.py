from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):

    order_id: int = Field(gt=0)

    amount: float = Field(gt=0)

    payment_method: str = Field(
        min_length=3,
        max_length=50
    )


class PaymentUpdate(BaseModel):

    status: str = Field(
        min_length=3,
        max_length=50
    )

    transaction_id: str | None = None


class PaymentResponse(BaseModel):

    id: int

    order_id: int

    amount: float

    payment_method: str

    transaction_id: str | None

    status: str

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)