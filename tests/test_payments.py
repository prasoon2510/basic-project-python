
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


# --------------------------------------------------
# TEST USER
# --------------------------------------------------

TEST_USER_ID = "test-payment-user-001"
OTHER_USER_ID = "another-payment-user-001"


# --------------------------------------------------
# AUTHENTICATED CUSTOMER FIXTURE
# --------------------------------------------------

@pytest.fixture
def customer_client(client, db_session):

    user = User(
        zitadel_user_id=TEST_USER_ID,
        email="payment@example.com",
        full_name="Payment Customer",
        role="CUSTOMER",
    )

    db_session.add(user)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: {
        "sub": TEST_USER_ID,
        "email": "payment@example.com",
        "name": "Payment Customer",
    }

    yield client

    app.dependency_overrides.pop(get_current_user, None)


# --------------------------------------------------
# HELPER: CREATE TEST ORDER
# --------------------------------------------------

def create_test_order(db_session):

    user = db_session.query(User).filter(
        User.zitadel_user_id == TEST_USER_ID
    ).first()

    category = Category(
        name="Payment Electronics",
        description="Payment test category",
    )

    db_session.add(category)
    db_session.flush()

    product = Product(
        name="Payment Laptop",
        description="Laptop for payment tests",
        price=Decimal("50000.00"),
        sku="PAYMENT-LAPTOP-001",
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
    db_session.commit()

    db_session.refresh(order)

    return order


# --------------------------------------------------
# HELPER: PAYMENT PAYLOAD
# --------------------------------------------------

def payment_payload(order_id, amount=100000.00):
    return {
        "order_id": order_id,
        "amount": amount,
        "payment_method": "CARD",
    }


# --------------------------------------------------
# TEST 1: CREATE PAYMENT
# --------------------------------------------------

def test_create_payment(customer_client, db_session):

    order = create_test_order(db_session)

    response = customer_client.post(
        "/api/v1/payments/",
        json=payment_payload(order.id),
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["order_id"] == order.id
    assert data["amount"] == 100000.00
    assert data["payment_method"] == "CARD"
    assert data["status"] == "PENDING"
    assert "id" in data


# --------------------------------------------------
# TEST 2: GET PAYMENT BY ID
# --------------------------------------------------

def test_get_payment_by_id(customer_client, db_session):

    order = create_test_order(db_session)

    create_response = customer_client.post(
        "/api/v1/payments/",
        json=payment_payload(order.id),
    )

    assert create_response.status_code == status.HTTP_201_CREATED

    payment_id = create_response.json()["id"]

    response = customer_client.get(
        f"/api/v1/payments/{payment_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == payment_id
    assert data["order_id"] == order.id
    assert data["status"] == "PENDING"


# --------------------------------------------------
# TEST 3: GET PAYMENTS FOR AN ORDER
# --------------------------------------------------

def test_get_order_payments(customer_client, db_session):

    order = create_test_order(db_session)

    create_response = customer_client.post(
        "/api/v1/payments/",
        json=payment_payload(order.id),
    )

    assert create_response.status_code == status.HTTP_201_CREATED

    response = customer_client.get(
        f"/api/v1/payments/order/{order.id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["order_id"] == order.id


# --------------------------------------------------
# TEST 4: NONEXISTENT ORDER
# --------------------------------------------------

def test_create_payment_for_non_existing_order(customer_client):

    response = customer_client.post(
        "/api/v1/payments/",
        json=payment_payload(99999),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --------------------------------------------------
# TEST 5: INCORRECT PAYMENT AMOUNT
# --------------------------------------------------

def test_create_payment_with_incorrect_amount(
    customer_client,
    db_session,
):

    order = create_test_order(db_session)

    response = customer_client.post(
        "/api/v1/payments/",
        json=payment_payload(
            order.id,
            amount=50000.00,
        ),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# --------------------------------------------------
# TEST 6: INVALID PAYMENT METHOD
# --------------------------------------------------

def test_create_payment_with_invalid_method(
    customer_client,
    db_session,
):

    order = create_test_order(db_session)

    response = customer_client.post(
        "/api/v1/payments/",
        json={
            "order_id": order.id,
            "amount": 100000.00,
            "payment_method": "X",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --------------------------------------------------
# TEST 7: NONEXISTENT PAYMENT
# --------------------------------------------------

def test_get_non_existing_payment(customer_client):

    response = customer_client.get(
        "/api/v1/payments/99999"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
