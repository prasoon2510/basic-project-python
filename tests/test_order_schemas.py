
import pytest

from pydantic import ValidationError

from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.payment import PaymentCreate


def test_valid_order():

    order = OrderCreate(
        shipping_address="Hyderabad, India",
        items=[
            OrderItemCreate.model_validate({
                "product_id": 1,
                "quantity": 2
            })
        ]
    )

    assert len(order.items) == 1


def test_invalid_order_quantity():

    with pytest.raises(ValidationError):

        OrderCreate(
            shipping_address="Hyderabad, India",
            items=[
                OrderItemCreate.model_validate({
                    "product_id": 1,
                    "quantity": 0
                })
            ]
        )


def test_valid_payment():

    payment = PaymentCreate(
        order_id=1,
        amount=50000,
        payment_method="UPI"
    )

    assert payment.amount == 50000
