
from fastapi import Depends, HTTPException, status

from app.core.security import (
    get_current_user,
    get_role_value,
)


# ROLE-BASED PERMISSION CONFIGURATION
ROLE_PERMISSIONS = {
    "ADMIN": [
        "users:read",
        "users:manage",

        "products:read",
        "products:create",
        "products:update",
        "products:delete",

        "categories:read",
        "categories:manage",

        "inventory:read",
        "inventory:manage",

        "orders:read",
        "orders:create",
        "orders:manage",

        "payments:create",
        "payments:read",
        "payments:read_own",
        "payments:manage",
    ],

    "CUSTOMER": [
        "products:read",
        "categories:read",

        "orders:create",
        "orders:read_own",

        "payments:create",
        "payments:read_own",
    ],

    "INVENTORY_MANAGER": [
        "products:read",
        "inventory:read",
        "inventory:manage",
    ],

    "ORDER_MANAGER": [
        "orders:read",
        "orders:manage",
        "products:read",
    ],

    "PAYMENT_MANAGER": [
        "payments:create",
        "payments:read",
        "payments:read_own",
        "payments:manage",

        "orders:read",
    ],
}


# GET AUTHENTICATED USER ROLE
def get_user_role(current_user) -> str:

    role = get_role_value(current_user)

    if not role:
        return ""

    return str(role).strip().upper()


# CHECK WHETHER USER HAS AN ALLOWED ROLE
def require_roles(*allowed_roles: str):

    normalized_roles = {
        role.strip().upper()
        for role in allowed_roles
    }

    def role_checker(
        current_user=Depends(get_current_user),
    ):

        user_role = get_user_role(current_user)

        if user_role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )

        return current_user

    return role_checker


# CHECK WHETHER USER HAS REQUIRED PERMISSIONS
def require_permissions(*required_permissions: str):

    def permission_checker(
        current_user=Depends(get_current_user),
    ):

        user_role = get_user_role(current_user)

        user_permissions = ROLE_PERMISSIONS.get(
            user_role,
            [],
        )

        missing_permissions = [
            permission
            for permission in required_permissions
            if permission not in user_permissions
        ]

        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return permission_checker
