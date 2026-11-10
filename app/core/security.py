
import logging

import jwt

from jwt import PyJWKClient
from jwt.exceptions import PyJWKError, PyJWTError

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


# LOGGER
logger = logging.getLogger(__name__)


# HTTP BEARER AUTHENTICATION
bearer_scheme = HTTPBearer(
    auto_error=False,
)


# ZITADEL JWKS CLIENT
jwks_client = PyJWKClient(
    settings.ZITADEL_JWKS_URL,
    cache_keys=True,
)


# GET ROLE FROM SQLALCHEMY USER OR TEST DICTIONARY
def get_role_value(current_user) -> str:

    if isinstance(current_user, dict):
        role = current_user.get("role")
    else:
        role = getattr(
            current_user,
            "role",
            None,
        )

    if not role:
        return "CUSTOMER"

    return str(role).strip().upper()


# VERIFY ZITADEL ACCESS TOKEN
def verify_access_token(token: str) -> dict:

    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:

        # READ UNVERIFIED CLAIMS FOR DIAGNOSTICS ONLY
        # THESE CLAIMS ARE NOT TRUSTED FOR AUTHENTICATION

        unverified_header = jwt.get_unverified_header(
            token,
        )

        unverified_payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
                "verify_nbf": False,
            },
        )

        token_algorithm = unverified_header.get("alg")

        token_issuer = unverified_payload.get("iss")

        token_audience = unverified_payload.get("aud")

        token_expiration = unverified_payload.get("exp")

        # PRINT JWT DIAGNOSTICS
        print("\n========== ZITADEL JWT DIAGNOSTICS ==========")

        print(
            "Token Algorithm:",
            token_algorithm,
        )

        print(
            "Token Issuer:",
            token_issuer,
        )

        print(
            "Token Audience:",
            token_audience,
        )

        print(
            "Token Expiration:",
            token_expiration,
        )

        print(
            "Expected Issuer:",
            settings.ZITADEL_ISSUER,
        )

        print(
            "Expected Audience:",
            settings.ZITADEL_API_AUDIENCE,
        )

        print("=============================================\n")

        # CHECK ALGORITHM
        if token_algorithm != "RS256":

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported JWT signing algorithm",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        # GET SIGNING KEY FROM ZITADEL JWKS
        signing_key = jwks_client.get_signing_key_from_jwt(
            token,
        )

        # VERIFY SIGNATURE AND JWT CLAIMS
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.ZITADEL_API_AUDIENCE,
            issuer=settings.ZITADEL_ISSUER,
            options={
                "require": [
                    "exp",
                    "iss",
                    "sub",
                ],
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )

        print("ZITADEL TOKEN VALIDATION SUCCESSFUL")

        return payload

    # JWKS ERRORS
    except PyJWKError as error:

        logger.error(
            "ZITADEL JWKS validation failed: %s: %s",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to validate token signing key",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error

    # JWT VALIDATION ERRORS
    except PyJWTError as error:

        logger.error(
            "JWT validation failed: %s: %s",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error


# GET CURRENT AUTHENTICATED USER
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme,
    ),
    db: Session = Depends(get_db),
) -> User:

    # CHECK BEARER TOKEN
    if credentials is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # EXTRACT ACCESS TOKEN
    access_token = credentials.credentials

    # VERIFY ACCESS TOKEN
    payload = verify_access_token(
        access_token,
    )

    # EXTRACT ZITADEL USER ID
    zitadel_user_id = payload.get("sub")

    if not zitadel_user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ZITADEL user ID is missing",
        )

    # FIND USER IN LOCAL DATABASE
    user = db.scalar(
        select(User).where(
            User.zitadel_user_id == zitadel_user_id
        )
    )

    # CHECK LOCAL USER REGISTRATION
    if user is None:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not registered in this application",
        )

    return user


# ROLE-BASED ACCESS CONTROL
def require_roles(*allowed_roles: str):

    normalized_roles = {
        role.strip().upper()
        for role in allowed_roles
    }

    def role_checker(
        current_user=Depends(get_current_user),
    ):

        user_role = get_role_value(
            current_user,
        )

        if user_role not in normalized_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )

        return current_user

    return role_checker
