
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
)


def create_inventory(
    db: Session,
    inventory_data: InventoryCreate,
) -> Inventory:
    """Create inventory for an existing product."""

    product = db.get(
        Product,
        inventory_data.product_id,
    )

    if product is None:
        raise ValueError("Product not found")

    existing_inventory = db.scalar(
        select(Inventory).where(
            Inventory.product_id == inventory_data.product_id
        )
    )

    if existing_inventory is not None:
        raise ValueError(
            "Inventory already exists for this product"
        )

    if inventory_data.quantity < 0:
        raise ValueError("Quantity cannot be negative")

    if inventory_data.reserved_quantity < 0:
        raise ValueError(
            "Reserved quantity cannot be negative"
        )

    if (
        inventory_data.reserved_quantity
        > inventory_data.quantity
    ):
        raise ValueError(
            "Reserved quantity cannot exceed total quantity"
        )

    inventory = Inventory(
        **inventory_data.model_dump()
    )

    try:
        db.add(inventory)
        db.commit()
        db.refresh(inventory)

        return inventory

    except Exception:
        db.rollback()
        raise


def get_inventory_by_id(
    db: Session,
    inventory_id: int,
) -> Inventory | None:
    """Get inventory using its primary key."""

    return db.get(
        Inventory,
        inventory_id,
    )


def get_inventory_by_product_id(
    db: Session,
    product_id: int,
) -> Inventory | None:
    """Get inventory using the product ID."""

    statement = (
        select(Inventory)
        .where(Inventory.product_id == product_id)
    )

    return db.scalar(statement)


def get_all_inventory(
    db: Session,
) -> list[Inventory]:
    """Get all inventory records."""

    statement = (
        select(Inventory)
        .order_by(Inventory.id)
    )

    return list(db.scalars(statement).all())


def update_inventory(
    db: Session,
    inventory_id: int,
    inventory_data: InventoryUpdate,
) -> Inventory | None:
    """Update an existing inventory record."""

    inventory = db.get(
        Inventory,
        inventory_id,
    )

    if inventory is None:
        return None

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

    if new_quantity < 0:
        raise ValueError("Quantity cannot be negative")

    if new_reserved_quantity < 0:
        raise ValueError(
            "Reserved quantity cannot be negative"
        )

    if new_reserved_quantity > new_quantity:
        raise ValueError(
            "Reserved quantity cannot exceed total quantity"
        )

    try:
        for field, value in update_data.items():
            setattr(inventory, field, value)

        db.commit()
        db.refresh(inventory)

        return inventory

    except Exception:
        db.rollback()
        raise


def get_available_quantity(
    db: Session,
    product_id: int,
) -> int:
    """Calculate available stock for a product."""

    inventory = get_inventory_by_product_id(
        db,
        product_id,
    )

    if inventory is None:
        return 0

    return (
        inventory.quantity
        - inventory.reserved_quantity
    )
