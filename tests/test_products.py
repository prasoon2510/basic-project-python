
import pytest

from fastapi.testclient import TestClient

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
# HELPER FUNCTION
# --------------------------------------------------

def create_test_category(client):
    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Electronics",
            "description": "Electronic products",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_test_product(client, category_id):
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

    assert response.status_code == 201

    return response.json()


# --------------------------------------------------
# CREATE PRODUCT
# --------------------------------------------------

def test_create_product(admin_client):
    category_id = create_test_category(admin_client)

    response = admin_client.post(
        "/api/v1/products/",
        json={
            "name": "Laptop",
            "description": "Business laptop",
            "price": 75000.00,
            "sku": "LAPTOP-001",
            "category_id": category_id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Laptop"
    assert data["price"] == 75000.00
    assert data["sku"] == "LAPTOP-001"
    assert data["category_id"] == category_id
    assert data["is_active"] is True
    assert "id" in data


# --------------------------------------------------
# GET ALL PRODUCTS
# --------------------------------------------------

def test_get_all_products(admin_client):
    category_id = create_test_category(admin_client)

    create_test_product(admin_client, category_id)

    response = admin_client.get("/api/v1/products/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Laptop"


# --------------------------------------------------
# GET PRODUCT BY ID
# --------------------------------------------------

def test_get_product_by_id(admin_client):
    category_id = create_test_category(admin_client)

    product = create_test_product(admin_client, category_id)

    product_id = product["id"]

    response = admin_client.get(
        f"/api/v1/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Laptop"


# --------------------------------------------------
# UPDATE PRODUCT
# --------------------------------------------------

def test_update_product(admin_client):
    category_id = create_test_category(admin_client)

    product = create_test_product(admin_client, category_id)

    product_id = product["id"]

    response = admin_client.put(
        f"/api/v1/products/{product_id}",
        json={
            "name": "Updated Laptop",
            "description": "Updated business laptop",
            "price": 85000.00,
            "sku": "LAPTOP-001",
            "category_id": category_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Updated Laptop"
    assert data["price"] == 85000.00


# --------------------------------------------------
# DELETE PRODUCT
# --------------------------------------------------

def test_delete_product(admin_client):
    category_id = create_test_category(admin_client)

    product = create_test_product(admin_client, category_id)

    product_id = product["id"]

    response = admin_client.delete(
        f"/api/v1/products/{product_id}"
    )

    assert response.status_code in (200, 204)

    get_response = admin_client.get(
        f"/api/v1/products/{product_id}"
    )

    assert get_response.status_code == 404


# --------------------------------------------------
# INVALID PRODUCT DATA
# --------------------------------------------------

def test_create_product_with_invalid_price(admin_client):
    category_id = create_test_category(admin_client)

    response = admin_client.post(
        "/api/v1/products/",
        json={
            "name": "Invalid Laptop",
            "description": "Invalid price example",
            "price": -100,
            "sku": "INVALID-001",
            "category_id": category_id,
        },
    )

    assert response.status_code == 422


# --------------------------------------------------
# NON-EXISTING PRODUCT
# --------------------------------------------------

def test_get_non_existing_product(admin_client):
    response = admin_client.get(
        "/api/v1/products/99999"
    )

    assert response.status_code == 404
