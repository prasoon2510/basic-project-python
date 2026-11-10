from typing import Annotated

from fastapi import Depends

from app.core.security import get_current_user
from app.core.permissions import (
    require_roles,
    require_permissions,
)


# Authenticated user dependency
AuthenticatedUser = Annotated[
    dict,
    Depends(get_current_user),
]


# Administrator dependency
AdminUser = Annotated[
    dict,
    Depends(require_roles("ADMIN")),
]


# Customer dependency
CustomerUser = Annotated[
    dict,
    Depends(require_roles("CUSTOMER")),
]


# Inventory manager dependency
InventoryManager = Annotated[
    dict,
    Depends(require_roles("ADMIN", "INVENTORY_MANAGER")),
]


# Order manager dependency
OrderManager = Annotated[
    dict,
    Depends(require_roles("ADMIN", "ORDER_MANAGER")),
]


# Payment manager dependency
PaymentManager = Annotated[
    dict,
    Depends(require_roles("ADMIN", "PAYMENT_MANAGER")),
]


# Product creation permission
CanCreateProduct = Annotated[
    dict,
    Depends(require_permissions("products:create")),
]


# Product update permission
CanUpdateProduct = Annotated[
    dict,
    Depends(require_permissions("products:update")),
]


# Product deletion permission
CanDeleteProduct = Annotated[
    dict,
    Depends(require_permissions("products:delete")),
]