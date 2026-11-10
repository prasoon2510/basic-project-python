from app.services.user_service import (
    register_user,
    fetch_user,
    fetch_user_by_zitadel_id,
    fetch_all_users,
)

from app.services.category_service import (
    create_new_category,
    fetch_category,
    fetch_all_categories,
    search_category,
    remove_category,
)

from app.services.product_service import (
    create_new_product,
    fetch_product,
    fetch_all_products,
    search_product,
    update_existing_product,
    remove_product,
)

from app.services.inventory_service import (
    create_new_inventory,
    fetch_inventory,
    fetch_all_inventory,
    fetch_product_inventory,
    update_existing_inventory,
    fetch_available_stock,
)

from app.services.order_service import (
    create_new_order,
    fetch_order,
    fetch_all_orders,
    fetch_customer_orders,
    fetch_customer_order,
)

from app.services.payment_service import (
    create_new_payment,
    fetch_payment,
    fetch_order_payments,
    update_existing_payment,
)