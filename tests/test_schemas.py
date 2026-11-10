import pytest

from pydantic import ValidationError

from app.schemas.product import ProductCreate


def test_valid_product():

    product = ProductCreate(
        name="Laptop",
        description="Gaming Laptop",
        price=75000,
        sku="LAP001",
        category_id=1
    )

    assert product.name == "Laptop"

    assert product.price == 75000


def test_invalid_product_price():

    with pytest.raises(ValidationError):

        ProductCreate(
            name="Laptop",
            price=-100,
            sku="LAP001",
            category_id=1
        )


def test_invalid_product_name():

    with pytest.raises(ValidationError):

        ProductCreate(
            name="A",
            price=50000,
            sku="LAP001",
            category_id=1
        )