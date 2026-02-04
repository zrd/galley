"""
Pytest configuration and fixtures for testing the self-publishing platform.

Uses an in-memory SQLite database for API integration tests to ensure
test isolation and avoid polluting the development database.
"""

import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.main import app
from app.db import get_db
from app.repositories import (
    InMemoryAuthorRepository,
    InMemoryEbookRepository,
    InMemoryManuscriptRepository,
    InMemorySampleRepository,
)
from app.security.auth import create_access_token, hash_password
from app.services import AuthorService, EbookService, ManuscriptService, SampleService
from app.storage import get_storage_backend, LocalStorageBackend


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
    original_get_storage = get_storage_backend

    def override_get_storage():
        return test_storage

    # Patch the storage module in all places it's imported
    import app.storage as storage_module
    import app.api.manuscripts as manuscripts_module
    import app.api.ebooks as ebooks_module
    import app.services.generation_service as generation_service_module

    original_storage_func = storage_module.get_storage_backend
    storage_module.get_storage_backend = override_get_storage
    manuscripts_module.get_storage_backend = override_get_storage
    ebooks_module.get_storage_backend = override_get_storage
    generation_service_module.get_storage_backend = override_get_storage

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
        # Drop all tables
        Base.metadata.drop_all(bind=test_engine)


# ============================================================
# In-memory repository fixtures for unit tests
# ============================================================

@pytest.fixture
def author_repo() -> InMemoryAuthorRepository:
    """Create an in-memory author repository for testing."""
    return InMemoryAuthorRepository()


@pytest.fixture
def manuscript_repo() -> InMemoryManuscriptRepository:
    """Create an in-memory manuscript repository for testing."""
    return InMemoryManuscriptRepository()


@pytest.fixture
def sample_repo() -> InMemorySampleRepository:
    """Create an in-memory sample repository for testing."""
    return InMemorySampleRepository()


@pytest.fixture
def ebook_repo() -> InMemoryEbookRepository:
    """Create an in-memory ebook repository for testing."""
    return InMemoryEbookRepository()


@pytest.fixture
def author_service(author_repo: InMemoryAuthorRepository) -> AuthorService:
    """Create an author service with in-memory repository."""
    return AuthorService(author_repo)


@pytest.fixture
def manuscript_service(manuscript_repo: InMemoryManuscriptRepository) -> ManuscriptService:
    """Create a manuscript service with in-memory repository."""
    return ManuscriptService(manuscript_repo)


@pytest.fixture
def sample_service(sample_repo: InMemorySampleRepository) -> SampleService:
    """Create a sample service with in-memory repository."""
    return SampleService(sample_repo)


@pytest.fixture
def ebook_service(ebook_repo: InMemoryEbookRepository) -> EbookService:
    """Create an ebook service with in-memory repository."""
    return EbookService(ebook_repo)


@pytest.fixture
def test_author(author_service: AuthorService):
    """Create a test author."""
    return author_service.create(
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        display_name="Test Author",
    )


@pytest.fixture
def auth_headers(test_author) -> dict[str, str]:
    """Create authorization headers with a valid JWT token."""
    token = create_access_token(test_author.id)
    return {"Authorization": f"Bearer {token}"}
