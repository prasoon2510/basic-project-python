
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

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)

from app.repositories.product_repository import (
    create_product,
    get_all_products,
    get_product_by_id,
    update_product,
    delete_product,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# CREATE PRODUCT
@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):

    return create_product(
        db,
        product_data,
    )


# GET ALL PRODUCTS
@router.get(
    "/",
    response_model=list[ProductResponse],
)
def read_all_products(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):

    return get_all_products(
        db,
        skip,
        limit,
    )


# GET PRODUCT BY ID
@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
):

    product = get_product_by_id(
        db,
        product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


# UPDATE PRODUCT
@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_existing_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):

    product = update_product(
        db,
        product_id,
        product_data,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


# DELETE PRODUCT
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
):

    deleted = delete_product(
        db,
        product_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return None
