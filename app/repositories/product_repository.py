from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(
    db: Session,
    product_data: ProductCreate,
) -> Product:
    """Create a new product."""

    product = Product(
        **product_data.model_dump()
    )

    try:
        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise


def get_product_by_id(
    db: Session,
    product_id: int,
) -> Product | None:
    """Retrieve a product using its ID."""

    return db.get(Product, product_id)


def get_all_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
) -> list[Product]:
    """Retrieve products with pagination."""

    statement = (
        select(Product)
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def search_products(
    db: Session,
    search_term: str,
    skip: int = 0,
    limit: int = 10,
) -> list[Product]:
    """Search products by name."""

    statement = (
        select(Product)
        .where(Product.name.ilike(f"%{search_term}%"))
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def update_product(
    db: Session,
    product_id: int,
    product_data: ProductUpdate,
) -> Product | None:
    """Update an existing product."""

    product = db.get(Product, product_id)

    if product is None:
        return None

    update_data = product_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise


def delete_product(
    db: Session,
    product_id: int,
) -> bool:
    """Delete a product."""

    product = db.get(Product, product_id)

    if product is None:
        return False

    try:
        db.delete(product)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise