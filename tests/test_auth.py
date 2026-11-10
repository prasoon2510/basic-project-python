
import pytest

from fastapi import status

from app.main import app
from app.core.security import get_current_user


# --------------------------------------------------
# TEST USER CLAIMS
# --------------------------------------------------

TEST_USER = {
    "sub": "test-zitadel-user-123",
    "preferred_username": "testcustomer",
    "email": "customer@example.com",
    "email_verified": True,
    "name": "Test Customer",
}


# --------------------------------------------------
# AUTHENTICATED CLIENT FIXTURE
# --------------------------------------------------

@pytest.fixture
def authenticated_client(client):

    app.dependency_overrides[get_current_user] = lambda: TEST_USER.copy()

    yield client

    app.dependency_overrides.pop(get_current_user, None)


# --------------------------------------------------
# TEST 1: GET AUTHENTICATED USER PROFILE
# --------------------------------------------------

def test_get_my_profile(authenticated_client):

    response = authenticated_client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["user_id"] == TEST_USER["sub"]
    assert data["username"] == TEST_USER["preferred_username"]
    assert data["email"] == TEST_USER["email"]
    assert data["email_verified"] is True
    assert data["name"] == TEST_USER["name"]
    assert data["authenticated"] is True


# --------------------------------------------------
# TEST 2: VERIFY ACCESS TOKEN
# --------------------------------------------------

def test_verify_access_token(authenticated_client):

    response = authenticated_client.get(
        "/api/v1/auth/verify"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["message"] == "Access token is valid"
    assert data["authenticated"] is True
    assert data["user_id"] == TEST_USER["sub"]


# --------------------------------------------------
# TEST 3: UNAUTHENTICATED PROFILE REQUEST
# --------------------------------------------------

def test_profile_without_authentication(client):

    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


# --------------------------------------------------
# TEST 4: UNAUTHENTICATED TOKEN VERIFICATION
# --------------------------------------------------

def test_verify_without_authentication(client):

    response = client.get(
        "/api/v1/auth/verify"
    )

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


# --------------------------------------------------
# TEST 5: PROFILE WITH MISSING OPTIONAL CLAIMS
# --------------------------------------------------

def test_profile_with_missing_optional_claims(client):

    minimal_user = {
        "sub": "minimal-zitadel-user-123",
    }

    app.dependency_overrides[get_current_user] = (
        lambda: minimal_user.copy()
    )

    try:
        response = client.get(
            "/api/v1/auth/me"
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["user_id"] == minimal_user["sub"]
        assert data["email"] is None
        assert data["name"] is None
        assert data["authenticated"] is True

    finally:
        app.dependency_overrides.pop(get_current_user, None)
