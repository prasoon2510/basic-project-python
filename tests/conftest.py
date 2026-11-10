
import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_current_user

from app.models import (
    User,
    Category,
    Product,
    Inventory,
    Order,
    OrderItem,
    Payment,
)


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def db_session():

    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def admin_client(client):

    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "test-admin-user",
        "email": "admin@example.com",
        "name": "Test Administrator",
        "role": "ADMIN",
    }

    yield client

    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def customer_client(client, db_session):

    test_user_id = "test-order-item-user-001"

    user = User(
        zitadel_user_id=test_user_id,
        email="orderitems@example.com",
        full_name="Order Items Customer",
        role="CUSTOMER",
    )

    db_session.add(user)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: {
        "sub": test_user_id,
        "email": "orderitems@example.com",
        "name": "Order Items Customer",
        "role": "CUSTOMER",
    }

    yield client

    app.dependency_overrides.pop(get_current_user, None)
