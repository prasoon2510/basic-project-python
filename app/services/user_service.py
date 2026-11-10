from sqlalchemy.orm import Session

from app.repositories.user_repository import (
    create_user,
    get_user_by_id,
    get_user_by_zitadel_id,
    get_user_by_email,
    get_all_users,
)

from app.schemas.user import UserCreate


def register_user(
    db: Session,
    user_data: UserCreate,
):
    # Check ZITADEL identity
    existing_user = get_user_by_zitadel_id(
        db,
        user_data.zitadel_user_id,
    )

    if existing_user:
        raise ValueError("User is already registered")

    # Check email
    existing_email = get_user_by_email(
        db,
        str(user_data.email),
    )

    if existing_email:
        raise ValueError("Email is already registered")

    # Always assign the default role during self-registration
    safe_user_data = UserCreate(
        zitadel_user_id=user_data.zitadel_user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        role="CUSTOMER",
    )

    return create_user(
        db,
        safe_user_data,
    )


def fetch_user(
    db: Session,
    user_id: int,
):
    user = get_user_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found")

    return user


def fetch_user_by_zitadel_id(
    db: Session,
    zitadel_user_id: str,
):
    user = get_user_by_zitadel_id(
        db,
        zitadel_user_id,
    )

    if user is None:
        raise ValueError("User profile not found")

    return user


def fetch_all_users(
    db: Session,
    skip: int = 0,
    limit: int = 10,
):
    if skip < 0:
        raise ValueError("Skip cannot be negative")

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")

    return get_all_users(
        db,
        skip=skip,
        limit=limit,
    )