import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Force isolated in-memory test database and test secrets before any app modules are loaded
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum-safe-key-12345"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

import tempfile
import shutil
TEST_UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "mizigo_test_uploads")
os.environ["UPLOAD_DIR"] = TEST_UPLOAD_DIR

import app.db.database as db_module
from app.db.database import Base
from app.db.session import get_db

# Import all models so metadata knows all tables
import app.models.user
import app.models.vendor
import app.models.product
import app.models.inventory
import app.models.order
import app.models.order_item
import app.models.payment

from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=test_engine,
)

# Point global engine and SessionLocal to test database to avoid any accidental external access
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure every test runs against a clean, isolated database state."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    # Clean up test files in isolated test storage
    if os.path.exists(TEST_UPLOAD_DIR):
        for root, dirs, files in os.walk(TEST_UPLOAD_DIR):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except OSError:
                    pass
