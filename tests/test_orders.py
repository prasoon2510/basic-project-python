
import pytest

from fastapi import status

from app.main import app
from app.core.security import get_current_user

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory


# --------------------------------------------------
# TEST CUSTOMER
# --------------------------------------------------

TEST_USER_ID = "test-customer-zitadel-id"
OTHER_USER_ID = "another-customer-zitadel-id"


@pytest.fixture
def customer_client(client, db_session):
    user = User(
        zitadel_user_id=TEST_USER_ID,
        email="customer@example.com",
        full_name="Test Customer",
        role="CUSTOMER",
    )

    db_session.add(user)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: {
        "sub": TEST_USER_ID,
        "email": "customer@example.com",
        "name": "Test Customer",
    }

    yield client

    app.dependency_overrides.pop(get_current_user, None)


# --------------------------------------------------
# HELPER: CREATE PRODUCT AND INVENTORY
# --------------------------------------------------

def create_test_product(db_session, quantity=100):
    category = Category(
        name="Electronics",
        description="Electronic products",
    )

    db_session.add(category)
    db_session.flush()

    product = Product(
        name="Laptop",
        description="Business laptop",
        price=75000.00,
        sku="LAPTOP-001",
        category_id=category.id,
        is_active=True,
    )

    db_session.add(product)
    db_session.flush()

    inventory = Inventory(
        product_id=product.id,
        quantity=quantity,
        reserved_quantity=0,
    )

    db_session.add(inventory)
    db_session.commit()

    return product.id


# --------------------------------------------------
# HELPER: CREATE ORDER
# --------------------------------------------------

def create_test_order(client, product_id, quantity=2):
    return client.post(
        "/api/v1/orders/",
        json={
            "shipping_address": "Hyderabad, Telangana, India",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                }
            ],
        },
    )


# --------------------------------------------------
# TEST 1: CREATE ORDER
# --------------------------------------------------

def test_create_order(customer_client, db_session):
    product_id = create_test_product(db_session)

    response = create_test_order(
        customer_client,
        product_id,
        quantity=2,
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["user_id"] is not None
    assert data["status"] == "PENDING"
    assert data["shipping_address"] == "Hyderabad, Telangana, India"
    assert data["total_amount"] == 150000.00

    assert len(data["order_items"]) == 1
    assert data["order_items"][0]["product_id"] == product_id
    assert data["order_items"][0]["quantity"] == 2


# --------------------------------------------------
# TEST 2: GET ORDER BY ID
# --------------------------------------------------

def test_get_order_by_id(customer_client, db_session):
    product_id = create_test_product(db_session)

    create_response = create_test_order(
        customer_client,
        product_id,
    )

    assert create_response.status_code == status.HTTP_201_CREATED

    order_id = create_response.json()["id"]

    response = customer_client.get(
        f"/api/v1/orders/{order_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == order_id
    assert data["status"] == "PENDING"


# --------------------------------------------------
# TEST 3: GET CUSTOMER ORDERS
# --------------------------------------------------

def test_get_customer_orders(customer_client, db_session):
    product_id = create_test_product(db_session)

    create_response = create_test_order(
        customer_client,
        product_id,
    )

    assert create_response.status_code == status.HTTP_201_CREATED

    response = customer_client.get(
        "/api/v1/orders/my-orders"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["status"] == "PENDING"


# --------------------------------------------------
# TEST 4: INVALID ORDER QUANTITY
# --------------------------------------------------

def test_create_order_with_invalid_quantity(
    customer_client,
    db_session,
):
    product_id = create_test_product(db_session)

    response = create_test_order(
        customer_client,
        product_id,
        quantity=0,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --------------------------------------------------
# TEST 5: NON-EXISTING PRODUCT
# --------------------------------------------------

def test_create_order_with_non_existing_product(customer_client):
    response = create_test_order(
        customer_client,
        product_id=99999,
        quantity=1,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --------------------------------------------------
# TEST 6: INSUFFICIENT STOCK
# --------------------------------------------------

def test_create_order_with_insufficient_stock(
    customer_client,
    db_session,
):
    product_id = create_test_product(
        db_session,
        quantity=2,
    )

    response = create_test_order(
        customer_client,
        product_id,
        quantity=10,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# --------------------------------------------------
# TEST 7: NON-EXISTING ORDER
# --------------------------------------------------

def test_get_non_existing_order(customer_client):
    response = customer_client.get(
        "/api/v1/orders/99999"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
