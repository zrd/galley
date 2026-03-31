"""
Integration tests for tag API endpoints.
"""

import io
import uuid

import pytest
from fastapi.testclient import TestClient


def make_auth_headers(client: TestClient) -> dict[str, str]:
    email = f"test-{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "testpassword", "display_name": "Test Author"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_manuscript_with_tags(
    client: TestClient, auth_headers: dict, tag_names: list[str]
) -> dict:
    """Create a manuscript, using it as the vehicle to create tags."""
    sample_epub = b"PK\x03\x04" + b"fake epub content for testing" * 100
    files = [
        ("file", ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")),
        ("title", (None, "Tagged Book")),
        ("source_format", (None, "epub")),
    ] + [("tag_names", (None, name)) for name in tag_names]
    response = client.post(
        "/manuscripts/",
        headers=auth_headers,
        files=files,
    )
    return response.json()


class TestListTags:
    @pytest.fixture
    def auth_headers(self, client: TestClient) -> dict[str, str]:
        return make_auth_headers(client)

    def test_list_tags_empty(self, client: TestClient, auth_headers: dict):
        response = client.get("/tags/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_tags_returns_own_tags(self, client: TestClient, auth_headers: dict):
        create_manuscript_with_tags(client, auth_headers, ["Hard Sci-Fi", "Adventure"])

        response = client.get("/tags/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert {t["slug"] for t in data} == {"hard-sci-fi", "adventure"}

    def test_list_tags_excludes_other_authors(self, client: TestClient, auth_headers: dict):
        other_headers = make_auth_headers(client)
        create_manuscript_with_tags(client, other_headers, ["Horror"])
        create_manuscript_with_tags(client, auth_headers, ["Fantasy"])

        response = client.get("/tags/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "fantasy"

    def test_list_tags_unauthenticated(self, client: TestClient):
        response = client.get("/tags/")

        assert response.status_code == 401

    def test_list_tags_item_structure(self, client: TestClient, auth_headers: dict):
        create_manuscript_with_tags(client, auth_headers, ["Cozy Mystery"])

        response = client.get("/tags/", headers=auth_headers)

        assert response.status_code == 200
        item = response.json()[0]
        assert "id" in item
        assert "name" in item
        assert "slug" in item

    def test_list_tags_deduplicates_across_manuscripts(self, client: TestClient, auth_headers: dict):
        """The same tag assigned to two manuscripts should appear once."""
        sample_epub = b"PK\x03\x04" + b"fake epub content for testing" * 100
        for title in ["Book One", "Book Two"]:
            client.post(
                "/manuscripts/",
                headers=auth_headers,
                files=[
                    ("file", ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")),
                    ("title", (None, title)),
                    ("source_format", (None, "epub")),
                    ("tag_names", (None, "Fantasy")),
                ],
            )

        response = client.get("/tags/", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestGetTag:
    @pytest.fixture
    def auth_headers(self, client: TestClient) -> dict[str, str]:
        return make_auth_headers(client)

    def test_get_tag_by_slug(self, client: TestClient, auth_headers: dict):
        create_manuscript_with_tags(client, auth_headers, ["Hard Sci-Fi"])

        response = client.get("/tags/hard-sci-fi", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "hard-sci-fi"
        assert data["name"] == "Hard Sci-Fi"

    def test_get_tag_not_found(self, client: TestClient, auth_headers: dict):
        response = client.get("/tags/nonexistent-tag", headers=auth_headers)

        assert response.status_code == 404

    def test_get_tag_wrong_owner(self, client: TestClient, auth_headers: dict):
        other_headers = make_auth_headers(client)
        create_manuscript_with_tags(client, other_headers, ["Horror"])

        response = client.get("/tags/horror", headers=auth_headers)

        assert response.status_code == 404

    def test_get_tag_unauthenticated(self, client: TestClient):
        response = client.get("/tags/some-tag")

        assert response.status_code == 401
