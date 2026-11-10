
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.inventory import Inventory


# GET ALL ITEMS FOR AN ORDER
def get_order_items(
    db: Session,
    order_id: int,
) -> list[OrderItem]:

    statement = (
        select(OrderItem)
        .where(OrderItem.order_id == order_id)
        .order_by(OrderItem.id)
    )

    return list(db.scalars(statement).all())


# GET ORDER ITEM BY ID
def get_order_item_by_id(
    db: Session,
    item_id: int,
) -> OrderItem | None:

    return db.get(OrderItem, item_id)


# RECALCULATE ORDER TOTAL
def recalculate_order_total(
    db: Session,
    order: Order,
) -> None:

    order_items = db.scalars(
        select(OrderItem).where(
            OrderItem.order_id == order.id
        )
    ).all()

    order.total_amount = sum(
        (
            Decimal(str(item.unit_price)) * item.quantity
            for item in order_items
        ),
        start=Decimal("0.00"),
    )


# LOCK ORDER FIRST, THEN ORDER ITEM
def get_locked_order_and_item(
    db: Session,
    item_id: int,
) -> tuple[Order, OrderItem] | None:

    # Find the order associated with the item.
    item_reference = db.get(
        OrderItem,
        item_id,
    )

    if item_reference is None:
        return None

    order_id = item_reference.order_id

    # Lock the order first.
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .with_for_update()
    )

    if order is None:
        raise ValueError("Order not found")

    # Lock the order item.
    item = db.scalar(
        select(OrderItem)
        .where(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id,
        )
        .with_for_update()
    )

    if item is None:
        return None

    return order, item


# UPDATE ORDER ITEM QUANTITY
def update_order_item(
    db: Session,
    item_id: int,
    quantity: int,
) -> OrderItem | None:

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero"
        )

    try:
        locked_records = get_locked_order_and_item(
            db=db,
            item_id=item_id,
        )

        if locked_records is None:
            return None

        order, item = locked_records

        # Only pending orders can be modified.
        if order.status != "PENDING":
            raise ValueError(
                "Only pending orders can be modified"
            )

        # Lock inventory.
        inventory = db.scalar(
            select(Inventory)
            .where(
                Inventory.product_id == item.product_id
            )
            .with_for_update()
        )

        if inventory is None:
            raise ValueError(
                "Inventory not found"
            )

        old_quantity = item.quantity

        # Validate existing inventory reservation.
        if (
            inventory.reserved_quantity < old_quantity
            or inventory.reserved_quantity > inventory.quantity
        ):
            raise ValueError(
                "Invalid inventory reservation state"
            )

        quantity_difference = quantity - old_quantity

        # Calculate available stock.
        available_quantity = (
            inventory.quantity - inventory.reserved_quantity
        )

        if quantity_difference > available_quantity:
            raise ValueError(
                "Insufficient inventory"
            )

        # Calculate the new reservation.
        new_reserved_quantity = (
            inventory.reserved_quantity + quantity_difference
        )

        if (
            new_reserved_quantity < 0
            or new_reserved_quantity > inventory.quantity
        ):
            raise ValueError(
                "Invalid inventory reservation state"
            )

        # Update inventory reservation.
        inventory.reserved_quantity = new_reserved_quantity

        # Update order item.
        item.quantity = quantity

        db.flush()

        # Recalculate order total.
        recalculate_order_total(
            db=db,
            order=order,
        )

        db.commit()
        db.refresh(item)

        return item

    except Exception:
        db.rollback()
        raise


# DELETE ORDER ITEM
def delete_order_item(
    db: Session,
    item_id: int,
) -> bool:

    try:
        locked_records = get_locked_order_and_item(
            db=db,
            item_id=item_id,
        )

        if locked_records is None:
            return False

        order, item = locked_records

        # Only pending orders can be modified.
        if order.status != "PENDING":
            raise ValueError(
                "Only pending orders can be modified"
            )

        # Lock inventory.
        inventory = db.scalar(
            select(Inventory)
            .where(
                Inventory.product_id == item.product_id
            )
            .with_for_update()
        )

        if inventory is None:
            raise ValueError(
                "Inventory not found"
            )

        # Validate reservation.
        if (
            inventory.reserved_quantity < item.quantity
            or inventory.reserved_quantity > inventory.quantity
        ):
            raise ValueError(
                "Invalid inventory reservation state"
            )

        # Release reserved inventory.
        inventory.reserved_quantity -= item.quantity

        # Delete order item.
        db.delete(item)

        db.flush()

        # Recalculate order total.
        recalculate_order_total(
            db=db,
            order=order,
        )

        # Cancel the order if its last item was deleted.
        remaining_items = db.scalars(
            select(OrderItem).where(
                OrderItem.order_id == order.id
            )
        ).all()

        if not remaining_items:
            order.status = "CANCELLED"

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise
