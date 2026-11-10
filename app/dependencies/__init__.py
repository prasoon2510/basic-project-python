from app.dependencies.common import (
    DbSession,
    CurrentUser,
)

from app.dependencies.auth import (
    AuthenticatedUser,
    AdminUser,
    CustomerUser,
    InventoryManager,
    OrderManager,
    PaymentManager,
    CanCreateProduct,
    CanUpdateProduct,
    CanDeleteProduct,
)