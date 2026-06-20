"""
Integration tests for author profile API endpoints.
"""

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    email = f"author-test-{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "testpassword", "display_name": "Test Author"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


class TestGetCurrentAuthor:
    def test_get_me_returns_profile(self, client: TestClient, auth_headers: dict):
        response = client.get("/authors/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Test Author"
        assert data["bio"] is None
        assert data["website"] is None
        assert data["is_public"] is False

    def test_get_me_requires_auth(self, client: TestClient):
        response = client.get("/authors/me")
        assert response.status_code == 401


class TestUpdateCurrentAuthor:
    def test_update_display_name(self, client: TestClient, auth_headers: dict):
        response = client.put(
            "/authors/me",
            headers=auth_headers,
            json={"display_name": "New Name"},
        )
        assert response.status_code == 200
        assert response.json()["display_name"] == "New Name"

    def test_update_bio(self, client: TestClient, auth_headers: dict):
        response = client.put(
            "/authors/me",
            headers=auth_headers,
            json={"bio": "I write books."},
        )
        assert response.status_code == 200
        assert response.json()["bio"] == "I write books."

    def test_update_partial_preserves_other_fields(self, client: TestClient, auth_headers: dict):
        client.put("/authors/me", headers=auth_headers, json={"bio": "My bio", "is_public": True})

        response = client.put("/authors/me", headers=auth_headers, json={"bio": "Updated bio"})
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Updated bio"
        assert data["display_name"] == "Test Author"
        assert data["is_public"] is True

    def test_update_website_bare_domain_normalized(self, client: TestClient, auth_headers: dict):
        response = client.put(
            "/authors/me",
            headers=auth_headers,
            json={"website": "mybooksite.com"},
        )
        assert response.status_code == 200
        assert response.json()["website"] == "https://mybooksite.com"

    def test_update_website_invalid_scheme_rejected(self, client: TestClient, auth_headers: dict):
        response = client.put(
            "/authors/me",
            headers=auth_headers,
            json={"website": "ftp://mybooksite.com"},
        )
        assert response.status_code == 422

    def test_clear_bio(self, client: TestClient, auth_headers: dict):
        client.put("/authors/me", headers=auth_headers, json={"bio": "Some bio"})

        response = client.put("/authors/me", headers=auth_headers, json={"bio": None})
        assert response.status_code == 200
        assert response.json()["bio"] is None

    def test_update_is_public(self, client: TestClient, auth_headers: dict):
        response = client.put("/authors/me", headers=auth_headers, json={"is_public": True})
        assert response.status_code == 200
        assert response.json()["is_public"] is True

        response = client.put("/authors/me", headers=auth_headers, json={"is_public": False})
        assert response.status_code == 200
        assert response.json()["is_public"] is False

    def test_update_is_public_does_not_clear_bio(self, client: TestClient, auth_headers: dict):
        client.put("/authors/me", headers=auth_headers, json={"bio": "My bio"})

        response = client.put("/authors/me", headers=auth_headers, json={"is_public": True})
        assert response.status_code == 200
        assert response.json()["bio"] == "My bio"

    def test_clear_website(self, client: TestClient, auth_headers: dict):
        client.put("/authors/me", headers=auth_headers, json={"website": "https://example.com"})

        response = client.put("/authors/me", headers=auth_headers, json={"website": None})
        assert response.status_code == 200
        assert response.json()["website"] is None

    def test_whitespace_display_name_rejected(self, client: TestClient, auth_headers: dict):
        response = client.put("/authors/me", headers=auth_headers, json={"display_name": "   "})
        assert response.status_code == 422

    def test_update_requires_auth(self, client: TestClient):
        response = client.put("/authors/me", json={"display_name": "Hacker"})
        assert response.status_code == 401
