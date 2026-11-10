
import pytest

from fastapi.testclient import TestClient

from main import app

import app.auth as auth_module


client = TestClient(app)


def test_health_check():

    response = client.get("/health")

    assert response.status_code == 200


def test_root():

    response = client.get("/")

    assert response.status_code == 200


def test_missing_token():

    response = client.get("/api/loans/")

    assert response.status_code == 401


def test_fake_token_is_rejected(monkeypatch):

    monkeypatch.setattr(
        auth_module,
        "ISSUER",
        "https://example.zitadel.cloud"
    )

    monkeypatch.setattr(
        auth_module,
        "AUDIENCE",
        "test-project"
    )

    monkeypatch.setattr(
        auth_module,
        "JWKS_URL",
        "https://example.zitadel.cloud/oauth/v2/keys"
    )

    class FakeJWKClient:

        def __init__(self, url):
            pass

        def get_signing_key_from_jwt(self, token):

            import jwt

            raise jwt.InvalidTokenError(
                "Invalid token"
            )

    monkeypatch.setattr(
        auth_module,
        "PyJWKClient",
        FakeJWKClient
    )

    response = client.get(
        "/api/loans/",
        headers={
            "Authorization": "Bearer fake-token"
        }
    )

    assert response.status_code == 401
