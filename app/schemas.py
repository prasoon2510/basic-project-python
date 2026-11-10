
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LoanCreate(BaseModel):

    customer_id: str

    loan_amount: float = Field(gt=0)

    interest_rate: float = Field(ge=0)

    loan_duration_months: int = Field(gt=0)

    loan_type: str


class LoanResponse(BaseModel):

    loan_id: str

    customer_id: str

    loan_amount: float

    interest_rate: float

    loan_duration_months: int

    loan_type: str

    status: str

    created_by: str

    created_at: datetime


class LoanUpdate(BaseModel):

    loan_amount: Optional[float] = Field(
        default=None,
        gt=0
    )

    interest_rate: Optional[float] = Field(
        default=None,
        ge=0
    )

    loan_duration_months: Optional[int] = Field(
        default=None,
        gt=0
    )

    status: Optional[str] = None
