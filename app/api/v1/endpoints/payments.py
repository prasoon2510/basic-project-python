
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import (
    ROLE_PERMISSIONS,
    get_user_role,
)

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
)

from app.services.payment_service import (
    create_new_payment,
    fetch_payment,
    fetch_order_payments,
)

from app.repositories.payment_repository import (
    get_payment_by_id,
    get_order_payments,
)

from app.repositories.order_repository import get_order_by_id


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# GET ZITADEL USER ID
def get_zitadel_user_id(current_user: Any) -> str | None:

    if hasattr(current_user, "zitadel_user_id"):
        return current_user.zitadel_user_id

    if isinstance(current_user, dict):
        return (
            current_user.get("zitadel_user_id")
            or current_user.get("sub")
        )

    return getattr(current_user, "sub", None)


# GET PERMISSIONS FOR CURRENT USER
def get_current_permissions(
    current_user: Any,
) -> list[str]:

    role = get_user_role(current_user)

    return ROLE_PERMISSIONS.get(
        role,
        [],
    )


# CREATE PAYMENT
@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_payment_endpoint(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    permissions = get_current_permissions(current_user)

    if "payments:create" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create payments",
        )

    zitadel_user_id = get_zitadel_user_id(current_user)

    if not zitadel_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity not found",
        )

    try:
        return create_new_payment(
            db=db,
            payment_data=payment_data,
            zitadel_user_id=zitadel_user_id,
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except ValueError as error:

        message = str(error)
        message_lower = message.lower()

        if (
            message == "Order not found"
            or message == "User profile not found"
        ):
            error_status = status.HTTP_404_NOT_FOUND

        elif "amount" in message_lower:
            error_status = status.HTTP_400_BAD_REQUEST

        elif "pending orders" in message_lower:
            error_status = status.HTTP_400_BAD_REQUEST

        else:
            error_status = status.HTTP_409_CONFLICT

        raise HTTPException(
            status_code=error_status,
            detail=message,
        ) from error


# GET PAYMENT BY ID
@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def read_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    permissions = get_current_permissions(current_user)

    # STAFF CAN READ ANY PAYMENT
    if (
        "payments:read" in permissions
        or "payments:manage" in permissions
    ):

        payment = get_payment_by_id(
            db=db,
            payment_id=payment_id,
        )

        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        return payment

    # CUSTOMERS CAN READ THEIR OWN PAYMENTS
    if "payments:read_own" in permissions:

        zitadel_user_id = get_zitadel_user_id(current_user)

        if not zitadel_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User identity not found",
            )

        try:
            return fetch_payment(
                db=db,
                payment_id=payment_id,
                zitadel_user_id=zitadel_user_id,
            )

        except PermissionError as error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(error),
            ) from error

        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to read payments",
    )


# GET PAYMENTS FOR AN ORDER
@router.get(
    "/order/{order_id}",
    response_model=list[PaymentResponse],
)
def read_order_payments(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    permissions = get_current_permissions(current_user)

    # STAFF CAN READ PAYMENTS FOR ANY ORDER
    if (
        "payments:read" in permissions
        or "payments:manage" in permissions
    ):

        order = get_order_by_id(
            db=db,
            order_id=order_id,
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        return get_order_payments(
            db=db,
            order_id=order_id,
        )

    # CUSTOMERS CAN READ PAYMENTS FOR THEIR OWN ORDERS
    if "payments:read_own" in permissions:

        zitadel_user_id = get_zitadel_user_id(current_user)

        if not zitadel_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User identity not found",
            )

        try:
            return fetch_order_payments(
                db=db,
                order_id=order_id,
                zitadel_user_id=zitadel_user_id,
            )

        except PermissionError as error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(error),
            ) from error

        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to read payments",
    )
