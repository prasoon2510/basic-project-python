
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.payment_repository import (
    create_payment,
    get_payment_by_id,
    get_order_payments,
    update_payment,
)

from app.repositories.order_repository import (
    get_order_by_id,
)

from app.repositories.user_repository import (
    get_user_by_zitadel_id,
)

from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
)


# CREATE PAYMENT
def create_new_payment(
    db: Session,
    payment_data: PaymentCreate,
    zitadel_user_id: str,
):
    # 1. Resolve ZITADEL identity to local MySQL user.
    user = get_user_by_zitadel_id(
        db,
        zitadel_user_id,
    )

    if user is None:
        raise ValueError("User profile not found")

    # 2. Find the order.
    order = get_order_by_id(
        db,
        payment_data.order_id,
    )

    if order is None:
        raise ValueError("Order not found")

    # 3. Verify order ownership.
    if order.user_id != user.id:
        raise PermissionError(
            "You cannot make payment for another customer's order"
        )

    # 4. Only pending orders can be paid.
    if order.status != "PENDING":
        raise ValueError(
            "Only pending orders can be paid"
        )

    # 5. Validate payment amount against order total.
    expected_amount = Decimal(
        str(order.total_amount)
    )

    received_amount = Decimal(
        str(payment_data.amount)
    )

    if received_amount != expected_amount:
        raise ValueError(
            "Payment amount must match the order total"
        )

    # 6. Create payment using the local MySQL user ID.
    return create_payment(
        db=db,
        payment_data=payment_data,
        user_id=user.id,
    )


# GET PAYMENT BY ID (CUSTOMER)
def fetch_payment(
    db: Session,
    payment_id: int,
    zitadel_user_id: str,
):
    payment = get_payment_by_id(
        db,
        payment_id,
    )

    if payment is None:
        raise ValueError("Payment not found")

    order = get_order_by_id(
        db,
        payment.order_id,
    )

    if order is None:
        raise ValueError("Associated order not found")

    user = get_user_by_zitadel_id(
        db,
        zitadel_user_id,
    )

    if user is None:
        raise ValueError("User profile not found")

    if order.user_id != user.id:
        raise PermissionError(
            "You cannot access another customer's payment"
        )

    return payment


# GET PAYMENTS FOR AN ORDER (CUSTOMER)
def fetch_order_payments(
    db: Session,
    order_id: int,
    zitadel_user_id: str,
):
    order = get_order_by_id(
        db,
        order_id,
    )

    if order is None:
        raise ValueError("Order not found")

    user = get_user_by_zitadel_id(
        db,
        zitadel_user_id,
    )

    if user is None:
        raise ValueError("User profile not found")

    if order.user_id != user.id:
        raise PermissionError(
            "You cannot access another customer's payments"
        )

    return get_order_payments(
        db,
        order_id,
    )


# UPDATE PAYMENT (AUTHORIZED STAFF)
def update_existing_payment(
    db: Session,
    payment_id: int,
    payment_data: PaymentUpdate,
):
    payment = get_payment_by_id(
        db,
        payment_id,
    )

    if payment is None:
        raise ValueError("Payment not found")

    return update_payment(
        db=db,
        payment_id=payment_id,
        payment_data=payment_data,
    )
