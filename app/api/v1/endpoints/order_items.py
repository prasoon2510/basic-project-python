
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

from app.models.user import User

from app.schemas.order_item import (
    OrderItemUpdate,
    OrderItemResponse,
)

from app.repositories.order_item_repository import (
    get_order_items,
    get_order_item_by_id,
    update_order_item,
    delete_order_item,
)

from app.repositories.order_repository import (
    get_order_by_id,
)


router = APIRouter(
    prefix="/order-items",
    tags=["Order Items"],
)


# GET ROLE FROM USER OBJECT OR TEST DICTIONARY
def get_current_user_role(current_user) -> str:

    if isinstance(current_user, dict):
        role = current_user.get("role")
    else:
        role = getattr(current_user, "role", None)

    if not role:
        return "CUSTOMER"

    return str(role).strip().upper()


# GET LOCAL DATABASE USER ID
def get_local_user_id(
    db: Session,
    current_user,
) -> int | None:

    # PRODUCTION: SQLALCHEMY USER OBJECT
    if isinstance(current_user, User):
        return current_user.id

    # TESTING: DICTIONARY RETURNED BY AUTH OVERRIDE
    if isinstance(current_user, dict):

        # USE LOCAL USER ID IF PROVIDED
        user_id = current_user.get("id")

        if user_id is not None:
            return user_id

        # OTHERWISE FIND USER USING ZITADEL SUBJECT
        zitadel_user_id = current_user.get("sub")

        if not zitadel_user_id:
            return None

        user = db.scalar(
            select(User).where(
                User.zitadel_user_id == zitadel_user_id
            )
        )

        if user is None:
            return None

        return user.id

    return None


# CHECK WHETHER THE USER CAN ACCESS OR MANAGE AN ORDER
def check_order_access(
    db: Session,
    order_id: int,
    current_user,
    manage: bool = False,
):

    role = get_current_user_role(current_user)

    # ADMIN AND STAFF CAN ACCESS ALL ORDERS
    if role in {"ADMIN", "STAFF"}:

        order = get_order_by_id(
            db,
            order_id,
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        return order

    # CUSTOMERS CAN ACCESS ONLY THEIR OWN ORDERS
    if role == "CUSTOMER":

        order = get_order_by_id(
            db,
            order_id,
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        local_user_id = get_local_user_id(
            db,
            current_user,
        )

        if local_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not registered in this application",
            )

        if order.user_id != local_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another customer's order",
            )

        return order

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this order",
    )


# GET ALL ITEMS IN AN ORDER
@router.get(
    "/order/{order_id}",
    response_model=list[OrderItemResponse],
)
def read_order_items(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    order = get_order_by_id(
        db,
        order_id,
    )

    # RETURN EMPTY LIST WHEN ORDER DOES NOT EXIST
    if order is None:
        return []

    check_order_access(
        db=db,
        order_id=order_id,
        current_user=current_user,
    )

    return get_order_items(
        db,
        order_id,
    )


# GET ORDER ITEM BY ID
@router.get(
    "/{item_id}",
    response_model=OrderItemResponse,
)
def read_order_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    item = get_order_item_by_id(
        db,
        item_id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found",
        )

    check_order_access(
        db=db,
        order_id=item.order_id,
        current_user=current_user,
    )

    return item


# UPDATE ORDER ITEM QUANTITY
@router.put(
    "/{item_id}",
    response_model=OrderItemResponse,
)
def update_existing_order_item(
    item_id: int,
    item_data: OrderItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    item = get_order_item_by_id(
        db,
        item_id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found",
        )

    check_order_access(
        db=db,
        order_id=item.order_id,
        current_user=current_user,
        manage=True,
    )

    try:

        updated_item = update_order_item(
            db=db,
            item_id=item_id,
            quantity=item_data.quantity,
        )

        if updated_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order item not found",
            )

        return updated_item

    except ValueError as error:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# DELETE ORDER ITEM
@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_order_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    item = get_order_item_by_id(
        db,
        item_id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found",
        )

    check_order_access(
        db=db,
        order_id=item.order_id,
        current_user=current_user,
        manage=True,
    )

    try:

        deleted = delete_order_item(
            db,
            item_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order item not found",
            )

        return None

    except ValueError as error:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
