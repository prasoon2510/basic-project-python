
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

from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
)

from app.repositories.category_repository import (
    create_category,
    get_all_categories,
    get_category_by_id,
    delete_category,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


# CREATE CATEGORY
@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "STAFF")
    ),
):

    return create_category(
        db,
        category_data,
    )


# GET ALL CATEGORIES
@router.get(
    "/",
    response_model=list[CategoryResponse],
)
def read_all_categories(
    db: Session = Depends(get_db),
):

    return get_all_categories(db)


# GET CATEGORY BY ID
@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def read_category(
    category_id: int,
    db: Session = Depends(get_db),
):

    category = get_category_by_id(
        db,
        category_id,
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


# DELETE CATEGORY
@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
):

    deleted = delete_category(
        db,
        category_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return None
