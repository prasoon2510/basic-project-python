
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

from app.schemas.user import (
    UserCreate,
    UserResponse,
)

from app.repositories.user_repository import (
    create_user,
    get_user_by_id,
    get_all_users,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# REGISTER NEW USER
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
):

    try:
        return create_user(db, user_data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


# GET ALL USERS
@router.get(
    "/",
    response_model=list[UserResponse],
)
def read_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
):

    return get_all_users(db)


# GET USER BY ID
@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
):

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
