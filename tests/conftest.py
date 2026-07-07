"""
Pytest configuration and fixtures for testing the self-publishing platform.

Uses an in-memory SQLite database for tests to ensure test isolation
and avoid polluting the development database.
"""

import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.storage import LocalStorageBackend

# Create an in-memory SQLite database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable foreign key support for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override dependency for testing with in-memory database."""
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_storage() -> Generator[LocalStorageBackend, None, None]:
    """Create a temporary storage backend for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield LocalStorageBackend(temp_dir)


@pytest.fixture(scope="function")
def client(db_session: Session, test_storage: LocalStorageBackend) -> Generator[TestClient, None, None]:
    """Create a test client with isolated database and storage."""
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Override storage backend
    def override_get_storage():
        return test_storage

    # Patch the storage module in all places it's imported
    import app.api.ebooks as ebooks_module
    import app.api.manuscripts as manuscripts_module
    import app.services.generation_service as generation_service_module
    import app.services.manuscript_service as manuscript_service_module
    import app.storage as storage_module

    original_storage_func = storage_module.get_storage_backend
    storage_module.get_storage_backend = override_get_storage
    manuscripts_module.get_storage_backend = override_get_storage
    ebooks_module.get_storage_backend = override_get_storage
    generation_service_module.get_storage_backend = override_get_storage
    manuscript_service_module.get_storage_backend = override_get_storage

    # Create tables for this test
    Base.metadata.create_all(bind=test_engine)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()
        storage_module.get_storage_backend = original_storage_func
        manuscripts_module.get_storage_backend = original_storage_func
        ebooks_module.get_storage_backend = original_storage_func
        generation_service_module.get_storage_backend = original_storage_func
        manuscript_service_module.get_storage_backend = original_storage_func
        # Drop all tables
        Base.metadata.drop_all(bind=test_engine)
