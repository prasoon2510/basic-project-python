from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate


def create_category(
    db: Session,
    category_data: CategoryCreate,
) -> Category:
    """Create a new category."""

    category = Category(
        **category_data.model_dump()
    )

    try:
        db.add(category)
        db.commit()
        db.refresh(category)

        return category

    except Exception:
        db.rollback()
        raise


def get_category_by_id(
    db: Session,
    category_id: int,
) -> Category | None:
    """Retrieve a category by ID."""

    return db.get(Category, category_id)


def get_all_categories(
    db: Session,
) -> list[Category]:
    """Retrieve all categories."""

    statement = select(Category).order_by(Category.id)

    return list(db.scalars(statement).all())


def search_categories(
    db: Session,
    search_term: str,
) -> list[Category]:
    """Search categories by name."""

    statement = select(Category).where(
        Category.name.ilike(f"%{search_term}%")
    )

    return list(db.scalars(statement).all())


def delete_category(
    db: Session,
    category_id: int,
) -> bool:
    """Delete a category only if no products use it."""

    category = db.get(Category, category_id)

    if category is None:
        return False

    # Check whether products belong to this category
    product_statement = select(Product.id).where(
        Product.category_id == category_id
    ).limit(1)

    product_exists = db.scalar(product_statement)

    if product_exists is not None:
        raise ValueError(
            "Cannot delete category because products are assigned to it"
        )

    try:
        db.delete(category)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise