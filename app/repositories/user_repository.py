from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    """Create a local user profile."""

    existing_user = db.scalar(
        select(User).where(
            User.zitadel_user_id == user_data.zitadel_user_id
        )
    )

    if existing_user:
        raise ValueError("User already exists")

    existing_email = db.scalar(
        select(User).where(
            User.email == str(user_data.email)
        )
    )

    if existing_email:
        raise ValueError("Email is already registered")

    user = User(
        **user_data.model_dump()
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    """Retrieve a user by local database ID."""

    return db.get(User, user_id)


def get_user_by_zitadel_id(
    db: Session,
    zitadel_user_id: str,
) -> User | None:
    """Retrieve a user by ZITADEL subject ID."""

    statement = select(User).where(
        User.zitadel_user_id == zitadel_user_id
    )

    return db.scalar(statement)


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    """Retrieve a user by email."""

    statement = select(User).where(
        User.email == email
    )

    return db.scalar(statement)


def get_all_users(
    db: Session,
    skip: int = 0,
    limit: int = 10,
) -> list[User]:
    """Retrieve users with pagination."""

    statement = (
        select(User)
        .order_by(User.id)
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())