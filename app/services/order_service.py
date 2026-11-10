
from sqlalchemy.orm import Session

from app.repositories.order_repository import (
    create_order,
    get_order_by_id,
    get_all_orders,
    get_user_orders,
)

from app.repositories.user_repository import (
    get_user_by_zitadel_id,
)

from app.schemas.order import OrderCreate


# CREATE NEW ORDER
def create_new_order(
    db: Session,
    order_data: OrderCreate,
    zitadel_user_id: str,
):
    # Resolve ZITADEL identity to local MySQL user.
    user = get_user_by_zitadel_id(
        db,
        zitadel_user_id,
    )

    if user is None:
        raise ValueError(
            "User profile not found. Register your profile first."
        )

    # Repository uses the local MySQL user ID.
    return create_order(
        db=db,
        order_data=order_data,
        user_id=user.id,
    )


# GET ORDER BY ID
def fetch_order(
    db: Session,
    order_id: int,
):
    order = get_order_by_id(
        db=db,
        order_id=order_id,
    )

    if order is None:
        raise ValueError("Order not found")

    return order


# GET ALL ORDERS
def fetch_all_orders(
    db: Session,
    skip: int = 0,
    limit: int = 10,
):
    if skip < 0:
        raise ValueError("Skip cannot be negative")

    if limit < 1 or limit > 100:
        raise ValueError(
            "Limit must be between 1 and 100"
        )

    return get_all_orders(
        db=db,
        skip=skip,
        limit=limit,
    )


# GET LOGGED-IN CUSTOMER'S ORDERS
def fetch_customer_orders(
    db: Session,
    zitadel_user_id: str,
):
    user = get_user_by_zitadel_id(
        db,
        zitadel_user_id,
    )

    if user is None:
        raise ValueError("User profile not found")

    return get_user_orders(
        db=db,
        user_id=user.id,
    )


# GET CUSTOMER ORDER BY ID
def fetch_customer_order(
    db: Session,
    order_id: int,
    zitadel_user_id: str,
):
    # Resolve authenticated user first.
    user = get_user_by_zitadel_id(
        db,
        zitadel_user_id,
    )

    if user is None:
        raise ValueError("User profile not found")

    # Retrieve the requested order.
    order = get_order_by_id(
        db=db,
        order_id=order_id,
    )

    if order is None:
        raise ValueError("Order not found")

    # Verify ownership using local MySQL IDs.
    if order.user_id != user.id:
        raise PermissionError(
            "You cannot access another customer's order"
        )

    return order
