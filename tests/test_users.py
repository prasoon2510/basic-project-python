
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
# HELPER: USER PAYLOAD
# --------------------------------------------------

def user_payload(
    zitadel_user_id="zitadel-user-001",
    email="customer@example.com",
    full_name="Test Customer",
):
    return {
        "zitadel_user_id": zitadel_user_id,
        "email": email,
        "full_name": full_name,
        "role": "CUSTOMER",
    }


# --------------------------------------------------
# TEST 1: REGISTER USER
# --------------------------------------------------

def test_register_user(admin_client):
    response = admin_client.post(
        "/api/v1/users/",
        json=user_payload(),
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["zitadel_user_id"] == "zitadel-user-001"
    assert data["email"] == "customer@example.com"
    assert data["full_name"] == "Test Customer"
    assert data["role"] == "CUSTOMER"
    assert "id" in data


# --------------------------------------------------
# TEST 2: GET ALL USERS
# --------------------------------------------------

def test_get_all_users(admin_client):
    admin_client.post(
        "/api/v1/users/",
        json=user_payload(),
    )

    response = admin_client.get(
        "/api/v1/users/"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["email"] == "customer@example.com"


# --------------------------------------------------
# TEST 3: GET USER BY ID
# --------------------------------------------------

def test_get_user_by_id(admin_client):
    create_response = admin_client.post(
        "/api/v1/users/",
        json=user_payload(),
    )

    assert create_response.status_code == status.HTTP_201_CREATED

    user_id = create_response.json()["id"]

    response = admin_client.get(
        f"/api/v1/users/{user_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == user_id
    assert data["email"] == "customer@example.com"


# --------------------------------------------------
# TEST 4: INVALID EMAIL
# --------------------------------------------------

def test_register_user_with_invalid_email(admin_client):
    response = admin_client.post(
        "/api/v1/users/",
        json=user_payload(email="invalid-email"),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --------------------------------------------------
# TEST 5: DUPLICATE ZITADEL USER ID
# --------------------------------------------------

def test_register_user_with_duplicate_zitadel_id(admin_client):
    first_response = admin_client.post(
        "/api/v1/users/",
        json=user_payload(
            zitadel_user_id="zitadel-user-001",
            email="first@example.com",
        ),
    )

    assert first_response.status_code == status.HTTP_201_CREATED

    second_response = admin_client.post(
        "/api/v1/users/",
        json=user_payload(
            zitadel_user_id="zitadel-user-001",
            email="second@example.com",
        ),
    )

    assert second_response.status_code == status.HTTP_409_CONFLICT


# --------------------------------------------------
# TEST 6: DUPLICATE EMAIL
# --------------------------------------------------

def test_register_user_with_duplicate_email(admin_client):
    first_response = admin_client.post(
        "/api/v1/users/",
        json=user_payload(
            zitadel_user_id="zitadel-user-001",
            email="same@example.com",
        ),
    )

    assert first_response.status_code == status.HTTP_201_CREATED

    second_response = admin_client.post(
        "/api/v1/users/",
        json=user_payload(
            zitadel_user_id="zitadel-user-002",
            email="same@example.com",
        ),
    )

    assert second_response.status_code == status.HTTP_409_CONFLICT


# --------------------------------------------------
# TEST 7: NON-EXISTING USER
# --------------------------------------------------

def test_get_non_existing_user(admin_client):
    response = admin_client.get(
        "/api/v1/users/99999"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
