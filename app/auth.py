
import os

import jwt

from jwt import PyJWKClient
from jwt.exceptions import (
    PyJWTError,
    PyJWKClientError,
    PyJWKClientConnectionError
)

from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2AuthorizationCodeBearer


ISSUER = os.getenv("ZITADEL_ISSUER", "").rstrip("/")

AUDIENCE = os.getenv("ZITADEL_API_AUDIENCE", "")

JWKS_URL = os.getenv("ZITADEL_JWKS_URL", "")

CLIENT_ID = os.getenv("ZITADEL_CLIENT_ID", "")


AUDIENCE_SCOPE = (
    f"urn:zitadel:iam:org:project:id:{AUDIENCE}:aud"
)


AUTHORIZATION_URL = f"{ISSUER}/oauth/v2/authorize"

TOKEN_URL = f"{ISSUER}/oauth/v2/token"


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=AUTHORIZATION_URL,
    tokenUrl=TOKEN_URL,
    scopes={
        "openid": "Authenticate the user",
        "profile": "Read user profile",
        "email": "Read user email",
        AUDIENCE_SCOPE: "Access Loan Management API"
    }
)


def validate_token(token: str):

    if not ISSUER or not AUDIENCE or not JWKS_URL:

        raise HTTPException(
            status_code=503,
            detail="ZITADEL configuration is incomplete"
        )

    try:

        # Read JWT header
        header = jwt.get_unverified_header(token)

        # Accept only RS256
        if header.get("alg") != "RS256":

            raise HTTPException(
                status_code=401,
                detail="Unsupported token algorithm"
            )

        # Connect to ZITADEL JWKS
        jwks_client = PyJWKClient(JWKS_URL)

        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Verify JWT signature and claims
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": ["exp", "iat", "iss", "sub"]
            }
        )

        return payload

    except HTTPException:
        raise

    except PyJWKClientConnectionError:

        raise HTTPException(
            status_code=503,
            detail="Unable to connect to ZITADEL JWKS"
        )

    except (PyJWTError, PyJWKClientError, ValueError):

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired ZITADEL access token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    token: str = Security(
        oauth2_scheme,
        scopes=[
            "openid",
            "profile",
            "email",
            AUDIENCE_SCOPE
        ]
    )
):

    return validate_token(token)
