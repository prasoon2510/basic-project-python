
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles

from app.models.user import User

from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
)

from app.repositories.inventory_repository import (
    create_inventory,
    get_all_inventory,
    get_inventory_by_id,
    get_inventory_by_product_id,
    get_available_quantity,
    update_inventory,
)


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


# CREATE INVENTORY
@router.post(
    "/",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_inventory(
    inventory_data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):
    try:
        return create_inventory(
            db,
            inventory_data,
        )

    except ValueError as error:
        message = str(error)

        if message == "Product not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from error

        if "already exists" in message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from error


# GET ALL INVENTORY
@router.get(
    "/",
    response_model=list[InventoryResponse],
)
def read_all_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):
    return get_all_inventory(db)


# GET INVENTORY BY PRODUCT ID
@router.get(
    "/product/{product_id}",
    response_model=InventoryResponse,
)
def read_inventory_by_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):
    inventory = get_inventory_by_product_id(
        db,
        product_id,
    )

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found for this product",
        )

    return inventory


# GET AVAILABLE STOCK BY PRODUCT ID
@router.get(
    "/available/{product_id}",
)
def read_available_stock(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):
    available_quantity = get_available_quantity(
        db,
        product_id,
    )

    return {
        "product_id": product_id,
        "available_quantity": available_quantity,
    }


# GET INVENTORY BY INVENTORY ID
@router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
)
def read_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):
    inventory = get_inventory_by_id(
        db,
        inventory_id,
    )

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found",
        )

    return inventory


# UPDATE INVENTORY
@router.put(
    "/{inventory_id}",
    response_model=InventoryResponse,
)
def update_existing_inventory(
    inventory_id: int,
    inventory_data: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):
    try:
        inventory = update_inventory(
            db,
            inventory_id,
            inventory_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found",
        )

    return inventory
