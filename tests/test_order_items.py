
from decimal import Decimal

import pytest

from fastapi import status

from app.main import app
from app.core.security import get_current_user

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem


# --------------------------------------------------
# TEST USER
# --------------------------------------------------

TEST_USER_ID = "test-order-item-user-001"


# --------------------------------------------------
# AUTHENTICATED CUSTOMER FIXTURE
# --------------------------------------------------

@pytest.fixture
def customer_client(client, db_session):

    user = User(
        zitadel_user_id=TEST_USER_ID,
        email="orderitems@example.com",
        full_name="Order Items Customer",
        role="CUSTOMER",
    )

    db_session.add(user)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: {
        "sub": TEST_USER_ID,
        "email": "orderitems@example.com",
        "name": "Order Items Customer",
    }

    yield client

    app.dependency_overrides.pop(get_current_user, None)


# --------------------------------------------------
# HELPER: CREATE ORDER AND ORDER ITEM
# --------------------------------------------------

def create_test_order_item(db_session):

    user = db_session.query(User).filter(
        User.zitadel_user_id == TEST_USER_ID
    ).first()

    category = Category(
        name="Order Item Electronics",
        description="Electronics for order item tests",
    )

    db_session.add(category)
    db_session.flush()

    product = Product(
        name="Test Laptop",
        description="Laptop for order item testing",
        price=Decimal("50000.00"),
        sku="ORDER-ITEM-LAPTOP-001",
        category_id=category.id,
        is_active=True,
    )

    db_session.add(product)
    db_session.flush()

    inventory = Inventory(
        product_id=product.id,
        quantity=100,
        reserved_quantity=2,
    )

    db_session.add(inventory)

    order = Order(
        user_id=user.id,
        total_amount=Decimal("100000.00"),
        status="PENDING",
        shipping_address="Hyderabad, Telangana, India",
    )

    db_session.add(order)
    db_session.flush()

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        unit_price=Decimal("50000.00"),
    )

    db_session.add(order_item)
    db_session.commit()

    db_session.refresh(order)
    db_session.refresh(order_item)

    return order, order_item


# --------------------------------------------------
# TEST 1: GET ALL ITEMS FOR AN ORDER
# --------------------------------------------------

def test_get_order_items(customer_client, db_session):

    order, order_item = create_test_order_item(db_session)

    response = customer_client.get(
        f"/api/v1/order-items/order/{order.id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["id"] == order_item.id
    assert data[0]["order_id"] == order.id
    assert data[0]["product_id"] == order_item.product_id
    assert data[0]["quantity"] == 2


# --------------------------------------------------
# TEST 2: GET ORDER ITEM BY ID
# --------------------------------------------------

def test_get_order_item_by_id(customer_client, db_session):

    order, order_item = create_test_order_item(db_session)

    response = customer_client.get(
        f"/api/v1/order-items/{order_item.id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == order_item.id
    assert data["order_id"] == order.id
    assert data["quantity"] == 2


# --------------------------------------------------
# TEST 3: UPDATE ORDER ITEM QUANTITY
# --------------------------------------------------

def test_update_order_item_quantity(
    customer_client,
    db_session,
):

    order, order_item = create_test_order_item(db_session)

    response = customer_client.put(
        f"/api/v1/order-items/{order_item.id}",
        json={
            "quantity": 3,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == order_item.id
    assert data["quantity"] == 3


# --------------------------------------------------
# TEST 4: REJECT ZERO QUANTITY
# --------------------------------------------------

def test_update_order_item_with_zero_quantity(
    customer_client,
    db_session,
):

    order, order_item = create_test_order_item(db_session)

    response = customer_client.put(
        f"/api/v1/order-items/{order_item.id}",
        json={
            "quantity": 0,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --------------------------------------------------
# TEST 5: DELETE ORDER ITEM
# --------------------------------------------------

def test_delete_order_item(customer_client, db_session):

    order, order_item = create_test_order_item(db_session)

    response = customer_client.delete(
        f"/api/v1/order-items/{order_item.id}"
    )

    assert response.status_code in (
        status.HTTP_200_OK,
        status.HTTP_204_NO_CONTENT,
    )

    get_response = customer_client.get(
        f"/api/v1/order-items/{order_item.id}"
    )

    assert get_response.status_code == status.HTTP_404_NOT_FOUND


# --------------------------------------------------
# TEST 6: GET NONEXISTENT ORDER ITEM
# --------------------------------------------------

def test_get_non_existing_order_item(customer_client):

    response = customer_client.get(
        "/api/v1/order-items/99999"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --------------------------------------------------
# TEST 7: GET ITEMS FOR NONEXISTENT ORDER
# --------------------------------------------------

def test_get_items_for_non_existing_order(customer_client):

    response = customer_client.get(
        "/api/v1/order-items/order/99999"
    )

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == []
