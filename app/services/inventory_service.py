from sqlalchemy.orm import Session

from app.repositories.inventory_repository import (
    create_inventory,
    get_inventory_by_id,
    get_inventory_by_product_id,
    get_all_inventory,
    update_inventory,
    get_available_quantity,
)

from app.repositories.product_repository import (
    get_product_by_id,
)

from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
)


def create_new_inventory(
    db: Session,
    inventory_data: InventoryCreate,
):
    # Verify that the product exists
    product = get_product_by_id(
        db,
        inventory_data.product_id,
    )

    if product is None:
        raise ValueError("Product not found")

    # Check whether inventory already exists
    existing_inventory = get_inventory_by_product_id(
        db,
        inventory_data.product_id,
    )

    if existing_inventory:
        raise ValueError(
            "Inventory already exists for this product"
        )

    # Validate reserved quantity
    if inventory_data.reserved_quantity > inventory_data.quantity:
        raise ValueError(
            "Reserved quantity cannot exceed total quantity"
        )

    return create_inventory(db, inventory_data)


def fetch_inventory(
    db: Session,
    inventory_id: int,
):
    inventory = get_inventory_by_id(db, inventory_id)

    if inventory is None:
        raise ValueError("Inventory not found")

    return inventory


def fetch_all_inventory(
    db: Session,
):
    return get_all_inventory(db)


def fetch_product_inventory(
    db: Session,
    product_id: int,
):
    inventory = get_inventory_by_product_id(db, product_id)

    if inventory is None:
        raise ValueError("Inventory not found for this product")

    return inventory


def update_existing_inventory(
    db: Session,
    inventory_id: int,
    inventory_data: InventoryUpdate,
):
    inventory = get_inventory_by_id(db, inventory_id)

    if inventory is None:
        raise ValueError("Inventory not found")

    update_data = inventory_data.model_dump(
        exclude_unset=True
    )

    new_quantity = update_data.get(
        "quantity",
        inventory.quantity,
    )

    new_reserved_quantity = update_data.get(
        "reserved_quantity",
        inventory.reserved_quantity,
    )

    if new_reserved_quantity > new_quantity:
        raise ValueError(
            "Reserved quantity cannot exceed total quantity"
        )

    return update_inventory(
        db,
        inventory_id,
        inventory_data,
    )


def fetch_available_stock(
    db: Session,
    product_id: int,
):
    product = get_product_by_id(db, product_id)

    if product is None:
        raise ValueError("Product not found")

    return {
        "product_id": product_id,
        "product_name": product.name,
        "available_quantity": get_available_quantity(
            db,
            product_id,
        ),
    }