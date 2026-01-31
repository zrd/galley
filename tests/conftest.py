"""
Pytest configuration and fixtures for testing the self-publishing platform.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import (
    InMemoryAuthorRepository,
    InMemoryEbookRepository,
    InMemoryManuscriptRepository,
    InMemorySampleRepository,
)
from app.security.auth import create_access_token, hash_password
from app.services import AuthorService, EbookService, ManuscriptService, SampleService


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


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
