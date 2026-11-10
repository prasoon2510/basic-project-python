
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem

from app.schemas.order import OrderCreate


# CREATE ORDER
def create_order(
    db: Session,
    order_data: OrderCreate,
    user_id: int,
) -> Order:
    """
    Create an order for a local authenticated user.

    Validate products and inventory, calculate the total,
    create order items, and reserve inventory.
    """

    try:
        # 1. Verify the local user exists.
        user = db.get(User, user_id)

        if user is None:
            raise ValueError("User profile not found")

        # 2. Validate order items.
        if not order_data.items:
            raise ValueError(
                "An order must contain at least one item"
            )

        # 3. Aggregate duplicate product IDs.
        requested_quantities: dict[int, int] = {}

        for item in order_data.items:
            if item.quantity <= 0:
                raise ValueError(
                    "Quantity must be greater than zero"
                )

            requested_quantities[item.product_id] = (
                requested_quantities.get(item.product_id, 0)
                + item.quantity
            )

        total_amount = Decimal("0.00")
        order_items_data = []

        # 4. Process products in sorted order.
        for product_id in sorted(requested_quantities):
            quantity = requested_quantities[product_id]

            # Lock product row.
            product = db.scalar(
                select(Product)
                .where(Product.id == product_id)
                .with_for_update()
            )

            if product is None:
                raise ValueError(
                    f"Product {product_id} not found"
                )

            if not product.is_active:
                raise ValueError(
                    f"Product {product.name} is inactive"
                )

            # Lock inventory row.
            inventory = db.scalar(
                select(Inventory)
                .where(Inventory.product_id == product_id)
                .with_for_update()
            )

            if inventory is None:
                raise ValueError(
                    f"Inventory not found for {product.name}"
                )

            # Calculate available stock.
            available_quantity = (
                inventory.quantity - inventory.reserved_quantity
            )

            if available_quantity < 0:
                raise ValueError(
                    f"Invalid inventory state for {product.name}"
                )

            if quantity > available_quantity:
                raise ValueError(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {available_quantity}"
                )

            # Capture product price at order creation time.
            unit_price = Decimal(str(product.price))

            if unit_price < 0:
                raise ValueError(
                    f"Invalid price for {product.name}"
                )

            order_items_data.append(
                {
                    "product_id": product.id,
                    "inventory": inventory,
                    "quantity": quantity,
                    "unit_price": unit_price,
                }
            )

            total_amount += unit_price * quantity

        # 5. Create the main order.
        order = Order(
            user_id=user.id,
            total_amount=total_amount,
            status="PENDING",
            shipping_address=order_data.shipping_address,
        )

        db.add(order)
        db.flush()

        # 6. Create order items and reserve inventory.
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
            )

            db.add(order_item)

            item_data["inventory"].reserved_quantity += (
                item_data["quantity"]
            )

        # 7. Flush all changes.
        db.flush()

        # 8. Load the order and its items.
        statement = (
            select(Order)
            .options(selectinload(Order.order_items))
            .where(Order.id == order.id)
        )

        created_order = db.scalar(statement)

        if created_order is None:
            raise RuntimeError(
                "Order could not be retrieved after creation"
            )

        # 9. Commit the transaction.
        db.commit()

        return created_order

    except Exception:
        db.rollback()
        raise


# GET ORDER BY ID
def get_order_by_id(
    db: Session,
    order_id: int,
) -> Order | None:
    statement = (
        select(Order)
        .options(selectinload(Order.order_items))
        .where(Order.id == order_id)
    )

    return db.scalar(statement)


# GET ALL ORDERS
def get_all_orders(
    db: Session,
    skip: int = 0,
    limit: int = 10,
) -> list[Order]:
    if skip < 0:
        raise ValueError("Skip cannot be negative")

    if limit < 1 or limit > 100:
        raise ValueError(
            "Limit must be between 1 and 100"
        )

    statement = (
        select(Order)
        .options(selectinload(Order.order_items))
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


# GET ORDERS FOR A USER
def get_user_orders(
    db: Session,
    user_id: int,
) -> list[Order]:
    statement = (
        select(Order)
        .options(selectinload(Order.order_items))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )

    return list(db.scalars(statement).all())
