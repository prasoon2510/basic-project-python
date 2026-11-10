from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/me")
def get_my_profile(
    current_user: dict = Depends(get_current_user),
):
    """
    Return the currently authenticated ZITADEL user.
    """

    return {
        "user_id": current_user.get("sub"),
        "username": current_user.get("preferred_username"),
        "email": current_user.get("email"),
        "email_verified": current_user.get("email_verified"),
        "name": current_user.get("name"),
        "role": current_user.get("role", "CUSTOMER"),
        "authenticated": True,
    }


@router.get("/verify")
def verify_token(
    current_user: dict = Depends(get_current_user),
):
    """
    Verify whether the current access token is valid.
    """

    return {
        "message": "Access token is valid",
        "authenticated": True,
        "user_id": current_user.get("sub"),
    }