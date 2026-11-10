
import pytest

from fastapi import status

from app.main import app
from app.core.security import get_current_user


# --------------------------------------------------
# AUTHENTICATED ADMIN CLIENT
# --------------------------------------------------

@pytest.fixture
def admin_client(client):
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "test-admin-user",
        "email": "admin@example.com",
        "name": "Test Administrator",
        "role": "ADMIN",
    }

    yield client

    app.dependency_overrides.pop(get_current_user, None)


# --------------------------------------------------
# HELPER: CREATE CATEGORY
# --------------------------------------------------

def create_test_category(client):
    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Electronics",
            "description": "Electronic products",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    return response.json()["id"]


# --------------------------------------------------
# HELPER: CREATE PRODUCT
# --------------------------------------------------

def create_test_product(client):
    category_id = create_test_category(client)

    response = client.post(
        "/api/v1/products/",
        json={
            "name": "Laptop",
            "description": "Business laptop",
            "price": 75000.00,
            "sku": "LAPTOP-001",
            "category_id": category_id,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    return response.json()["id"]


# --------------------------------------------------
# HELPER: CREATE INVENTORY
# --------------------------------------------------

def create_test_inventory(client):
    product_id = create_test_product(client)

    response = client.post(
        "/api/v1/inventory/",
        json={
            "product_id": product_id,
            "quantity": 100,
            "reserved_quantity": 10,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    return response.json()


# --------------------------------------------------
# TEST 1: CREATE INVENTORY
# --------------------------------------------------

def test_create_inventory(admin_client):
    product_id = create_test_product(admin_client)

    response = admin_client.post(
        "/api/v1/inventory/",
        json={
            "product_id": product_id,
            "quantity": 100,
            "reserved_quantity": 10,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["product_id"] == product_id
    assert data["quantity"] == 100
    assert data["reserved_quantity"] == 10
    assert "id" in data


# --------------------------------------------------
# TEST 2: GET ALL INVENTORY
# --------------------------------------------------

def test_get_all_inventory(admin_client):
    create_test_inventory(admin_client)

    response = admin_client.get(
        "/api/v1/inventory/"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["quantity"] == 100


# --------------------------------------------------
# TEST 3: GET INVENTORY BY ID
# --------------------------------------------------

def test_get_inventory_by_id(admin_client):
    inventory = create_test_inventory(admin_client)

    inventory_id = inventory["id"]

    response = admin_client.get(
        f"/api/v1/inventory/{inventory_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == inventory_id
    assert data["quantity"] == 100
    assert data["reserved_quantity"] == 10


# --------------------------------------------------
# TEST 4: GET INVENTORY BY PRODUCT ID
# --------------------------------------------------

def test_get_inventory_by_product_id(admin_client):
    inventory = create_test_inventory(admin_client)

    product_id = inventory["product_id"]

    response = admin_client.get(
        f"/api/v1/inventory/product/{product_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["product_id"] == product_id
    assert data["quantity"] == 100


# --------------------------------------------------
# TEST 5: UPDATE INVENTORY
# --------------------------------------------------

def test_update_inventory(admin_client):
    inventory = create_test_inventory(admin_client)

    inventory_id = inventory["id"]

    response = admin_client.put(
        f"/api/v1/inventory/{inventory_id}",
        json={
            "quantity": 150,
            "reserved_quantity": 20,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == inventory_id
    assert data["quantity"] == 150
    assert data["reserved_quantity"] == 20


# --------------------------------------------------
# TEST 6: REJECT NEGATIVE QUANTITY
# --------------------------------------------------

def test_create_inventory_with_negative_quantity(admin_client):
    product_id = create_test_product(admin_client)

    response = admin_client.post(
        "/api/v1/inventory/",
        json={
            "product_id": product_id,
            "quantity": -10,
            "reserved_quantity": 0,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --------------------------------------------------
# TEST 7: REJECT RESERVED QUANTITY GREATER THAN STOCK
# --------------------------------------------------

def test_create_inventory_with_invalid_reserved_quantity(admin_client):
    product_id = create_test_product(admin_client)

    response = admin_client.post(
        "/api/v1/inventory/",
        json={
            "product_id": product_id,
            "quantity": 10,
            "reserved_quantity": 20,
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# --------------------------------------------------
# TEST 8: INVENTORY FOR NON-EXISTING PRODUCT
# --------------------------------------------------

def test_create_inventory_for_non_existing_product(admin_client):
    response = admin_client.post(
        "/api/v1/inventory/",
        json={
            "product_id": 99999,
            "quantity": 50,
            "reserved_quantity": 0,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --------------------------------------------------
# TEST 9: GET AVAILABLE STOCK
# --------------------------------------------------

def test_get_available_stock(admin_client):
    inventory = create_test_inventory(admin_client)

    product_id = inventory["product_id"]

    response = admin_client.get(
        f"/api/v1/inventory/available/{product_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["available_quantity"] == 90
