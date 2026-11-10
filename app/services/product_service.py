from sqlalchemy.orm import Session

from app.repositories.product_repository import (
    create_product,
    get_product_by_id,
    get_all_products,
    search_products,
    update_product,
    delete_product,
)

from app.repositories.category_repository import (
    get_category_by_id,
)

from app.schemas.product import ProductCreate, ProductUpdate


def create_new_product(
    db: Session,
    product_data: ProductCreate,
):
    # Check whether the category exists
    category = get_category_by_id(
        db,
        product_data.category_id,
    )

    if category is None:
        raise ValueError("Category not found")

    # Check whether SKU already exists
    existing_products = search_products(
        db,
        product_data.sku,
    )

    # Search by SKU directly for an exact match
    from sqlalchemy import select
    from app.models.product import Product

    existing_product = db.scalar(
        select(Product).where(
            Product.sku == product_data.sku
        )
    )

    if existing_product:
        raise ValueError("Product SKU already exists")

    return create_product(db, product_data)


def fetch_product(
    db: Session,
    product_id: int,
):
    product = get_product_by_id(db, product_id)

    if product is None:
        raise ValueError("Product not found")

    return product


def fetch_all_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
):
    return get_all_products(
        db,
        skip=skip,
        limit=limit,
    )


def search_product(
    db: Session,
    search_term: str,
):
    if not search_term.strip():
        raise ValueError("Search term cannot be empty")

    return search_products(db, search_term)


def update_existing_product(
    db: Session,
    product_id: int,
    product_data: ProductUpdate,
):
    product = get_product_by_id(db, product_id)

    if product is None:
        raise ValueError("Product not found")

    update_data = product_data.model_dump(exclude_unset=True)

    if "category_id" in update_data:
        category = get_category_by_id(
            db,
            update_data["category_id"],
        )

        if category is None:
            raise ValueError("Category not found")

    if "sku" in update_data:
        from sqlalchemy import select
        from app.models.product import Product

        existing_product = db.scalar(
            select(Product).where(
                Product.sku == update_data["sku"],
                Product.id != product_id,
            )
        )

        if existing_product:
            raise ValueError("Product SKU already exists")

    return update_product(
        db,
        product_id,
        product_data,
    )


def remove_product(
    db: Session,
    product_id: int,
):
    product = get_product_by_id(db, product_id)

    if product is None:
        raise ValueError("Product not found")

    return delete_product(db, product_id)