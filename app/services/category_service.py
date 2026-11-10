from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate

from app.repositories.category_repository import (
    create_category,
    get_category_by_id,
    get_all_categories,
    search_categories,
    delete_category,
)


def create_new_category(
    db: Session,
    category_data: CategoryCreate,
):
    # Check for duplicate category names
    existing_category = db.scalar(
        select(Category).where(
            Category.name == category_data.name
        )
    )

    if existing_category:
        raise ValueError("Category name already exists")

    return create_category(db, category_data)


def fetch_category(
    db: Session,
    category_id: int,
):
    category = get_category_by_id(db, category_id)

    if category is None:
        raise ValueError("Category not found")

    return category


def fetch_all_categories(
    db: Session,
):
    return get_all_categories(db)


def search_category(
    db: Session,
    search_term: str,
):
    if not search_term.strip():
        raise ValueError("Search term cannot be empty")

    return search_categories(db, search_term)


def remove_category(
    db: Session,
    category_id: int,
):
    category = get_category_by_id(db, category_id)

    if category is None:
        raise ValueError("Category not found")

    try:
        return delete_category(db, category_id)

    except ValueError:
        raise

    except Exception:
        db.rollback()
        raise