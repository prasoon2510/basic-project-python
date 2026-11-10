
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.order import Order
from app.models.user import User

from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
)


def create_payment(
    db: Session,
    payment_data: PaymentCreate,
    user_id: int,
) -> Payment:
    """
    Create a payment for an order owned by the given local user.
    """

    try:
        # Find the local MySQL user.
        user = db.get(User, user_id)

        if user is None:
            raise ValueError("User profile not found")

        # Lock the order to prevent concurrent payment creation.
        order = db.scalar(
            select(Order)
            .where(Order.id == payment_data.order_id)
            .with_for_update()
        )

        if order is None:
            raise ValueError("Order not found")

        # Verify order ownership.
        if order.user_id != user.id:
            raise ValueError(
                "You cannot pay for another user's order"
            )

        if order.status != "PENDING":
            raise ValueError(
                "Only pending orders can be paid"
            )

        # Always use the server-side order amount.
        payment_amount = Decimal(str(payment_data.amount))
        order_amount = Decimal(str(order.total_amount))

        if payment_amount <= Decimal("0.00"):
            raise ValueError("Payment amount must be positive")

        if payment_amount != order_amount:
            raise ValueError(
                "Payment amount does not match order total"
            )

        # Prevent duplicate pending or successful payments.
        existing_payment = db.scalar(
            select(Payment)
            .where(
                Payment.order_id == order.id,
                Payment.status.in_(["PENDING", "SUCCESS"]),
            )
            .with_for_update()
        )

        if existing_payment is not None:
            raise ValueError(
                "A pending or successful payment already exists"
            )

        payment = Payment(
            order_id=order.id,
            amount=order_amount,
            payment_method=payment_data.payment_method,
            status="PENDING",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment

    except Exception:
        db.rollback()
        raise


def get_payment_by_id(
    db: Session,
    payment_id: int,
) -> Payment | None:

    return db.get(Payment, payment_id)


def get_order_payments(
    db: Session,
    order_id: int,
) -> list[Payment]:

    statement = (
        select(Payment)
        .where(Payment.order_id == order_id)
        .order_by(Payment.created_at.desc())
    )

    return list(db.scalars(statement).all())


def update_payment(
    db: Session,
    payment_id: int,
    payment_data: PaymentUpdate,
) -> Payment | None:
    """
    Update a pending payment's status or transaction ID.
    """

    try:
        # First find the payment to identify its order.
        existing_payment = db.get(Payment, payment_id)

        if existing_payment is None:
            return None

        # Lock the order first to maintain a consistent
        # lock order with create_payment().
        order = db.scalar(
            select(Order)
            .where(Order.id == existing_payment.order_id)
            .with_for_update()
        )

        if order is None:
            raise ValueError("Associated order not found")

        # Now lock and reload the payment.
        payment = db.scalar(
            select(Payment)
            .where(Payment.id == payment_id)
            .with_for_update()
        )

        if payment is None:
            return None

        if payment.status != "PENDING":
            raise ValueError(
                "Only pending payments can be updated"
            )

        update_data = payment_data.model_dump(
            exclude_unset=True
        )

        allowed_fields = {
            "status",
            "transaction_id",
        }

        unexpected_fields = set(update_data) - allowed_fields

        if unexpected_fields:
            raise ValueError(
                "Unsupported payment update fields"
            )

        new_status = update_data.get(
            "status",
            payment.status,
        )

        allowed_statuses = {
            "PENDING",
            "SUCCESS",
            "FAILED",
            "CANCELLED",
        }

        if new_status not in allowed_statuses:
            raise ValueError("Invalid payment status")

        transaction_id = update_data.get("transaction_id")

        if transaction_id is not None:
            existing_transaction = db.scalar(
                select(Payment).where(
                    Payment.transaction_id == transaction_id,
                    Payment.id != payment_id,
                )
            )

            if existing_transaction is not None:
                raise ValueError(
                    "Transaction ID already exists"
                )

            payment.transaction_id = transaction_id

        # Update payment status.
        payment.status = new_status

        # Confirm the order only after successful payment.
        if new_status == "SUCCESS":
            if order.status != "PENDING":
                raise ValueError(
                    "Only pending orders can be confirmed"
                )

            order.status = "CONFIRMED"

        db.commit()
        db.refresh(payment)

        return payment

    except Exception:
        db.rollback()
        raise
