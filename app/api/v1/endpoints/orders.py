
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import (
    ROLE_PERMISSIONS,
    get_user_role,
    require_permissions,
)

from app.schemas.order import (
    OrderCreate,
    OrderResponse,
)

from app.services.order_service import (
    create_new_order,
    fetch_order,
    fetch_all_orders,
    fetch_customer_orders,
    fetch_customer_order,
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


# GET ZITADEL USER ID FROM AUTHENTICATED USER
def get_zitadel_user_id(current_user: Any) -> str | None:

    # SQLAlchemy User object
    if hasattr(current_user, "zitadel_user_id"):
        return current_user.zitadel_user_id

    # Dictionary-based user
    if isinstance(current_user, dict):
        return (
            current_user.get("zitadel_user_id")
            or current_user.get("sub")
        )

    return None


# CREATE NEW ORDER
@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_order_endpoint(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permissions("orders:create")
    ),
):

    zitadel_user_id = get_zitadel_user_id(current_user)

    if not zitadel_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity not found",
        )

    try:
        return create_new_order(
            db=db,
            order_data=order_data,
            zitadel_user_id=zitadel_user_id,
        )

    except ValueError as error:

        error_message = str(error)

        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        ) from error


# GET ALL ORDERS
@router.get(
    "/",
    response_model=list[OrderResponse],
)
def read_all_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permissions("orders:read")
    ),
):

    try:
        return fetch_all_orders(
            db=db,
            skip=skip,
            limit=limit,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# GET LOGGED-IN CUSTOMER'S ORDERS
@router.get(
    "/my-orders",
    response_model=list[OrderResponse],
)
def read_my_orders(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permissions("orders:read_own")
    ),
):

    zitadel_user_id = get_zitadel_user_id(current_user)

    if not zitadel_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity not found",
        )

    try:
        return fetch_customer_orders(
            db=db,
            zitadel_user_id=zitadel_user_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


# GET ORDER BY ID
@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    role = get_user_role(current_user)

    permissions = ROLE_PERMISSIONS.get(role, [])

    # ADMIN / STAFF WITH orders:read
    if "orders:read" in permissions:

        try:
            return fetch_order(
                db=db,
                order_id=order_id,
            )

        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

    # CUSTOMER WITH orders:read_own
    if "orders:read_own" in permissions:

        zitadel_user_id = get_zitadel_user_id(
            current_user
        )

        if not zitadel_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User identity not found",
            )

        try:
            return fetch_customer_order(
                db=db,
                order_id=order_id,
                zitadel_user_id=zitadel_user_id,
            )

        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

        except PermissionError as error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(error),
            ) from error

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to read orders",
    )
