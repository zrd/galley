"""
Integration tests for manuscript API endpoints.
"""

import io

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register a user and return auth headers."""
    import uuid

    email = f"test-{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "testpassword",
            "display_name": "Test Author",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_epub() -> bytes:
    """Create a minimal valid-ish EPUB file (just bytes for testing)."""
    return b"PK\x03\x04" + b"fake epub content for testing" * 100


class TestCreateManuscript:
    def test_create_manuscript_success(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={
                "title": "My First Book",
                "source_format": "epub",
                "description": "A test book",
            },
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My First Book"
        assert data["source_format"] == "epub"
        assert data["state"] == "draft"
        assert data["description"] == "A test book"

    def test_create_manuscript_without_auth(self, client: TestClient, sample_epub: bytes):
        response = client.post(
            "/manuscripts/",
            data={"title": "Unauthorized Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )

        assert response.status_code == 401

    def test_create_manuscript_empty_file(self, client: TestClient, auth_headers: dict):
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Empty Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(b""), "application/epub+zip")},
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_create_manuscript_all_formats(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        formats = ["epub", "pdf", "docx", "odt"]

        for fmt in formats:
            response = client.post(
                "/manuscripts/",
                headers=auth_headers,
                data={"title": f"Book in {fmt}", "source_format": fmt},
                files={"file": (f"book.{fmt}", io.BytesIO(sample_epub), "application/octet-stream")},
            )

            assert response.status_code == 201, f"Failed for format {fmt}"
            assert response.json()["source_format"] == fmt


class TestListManuscripts:
    def test_list_manuscripts_empty(self, client: TestClient, auth_headers: dict):
        response = client.get("/manuscripts/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_manuscripts_with_items(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        # Create a couple manuscripts
        for i in range(3):
            client.post(
                "/manuscripts/",
                headers=auth_headers,
                data={"title": f"Book {i}", "source_format": "epub"},
                files={"file": (f"book{i}.epub", io.BytesIO(sample_epub), "application/epub+zip")},
            )

        response = client.get("/manuscripts/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_manuscripts_only_own(self, client: TestClient, sample_epub: bytes):
        import uuid as uuid_mod

        # Create manuscript with first user
        response1 = client.post(
            "/auth/register",
            json={
                "email": f"user1-list-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "User 1",
            },
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}

        client.post(
            "/manuscripts/",
            headers=headers1,
            data={"title": "User 1 Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )

        # Create manuscript with second user
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"user2-list-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "User 2",
            },
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        client.post(
            "/manuscripts/",
            headers=headers2,
            data={"title": "User 2 Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )

        # Each user should only see their own
        list1 = client.get("/manuscripts/", headers=headers1).json()
        list2 = client.get("/manuscripts/", headers=headers2).json()

        assert len(list1) == 1
        assert list1[0]["title"] == "User 1 Book"
        assert len(list2) == 1
        assert list2[0]["title"] == "User 2 Book"


class TestGetManuscript:
    def test_get_manuscript_success(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        # Create manuscript
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Get Test Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Get it
        response = client.get(f"/manuscripts/{manuscript_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["id"] == manuscript_id
        assert response.json()["title"] == "Get Test Book"

    def test_get_manuscript_not_found(self, client: TestClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/manuscripts/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    def test_get_manuscript_wrong_owner(self, client: TestClient, sample_epub: bytes):
        import uuid as uuid_mod

        # Create with user 1
        response1 = client.post(
            "/auth/register",
            json={
                "email": f"owner-get-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Owner",
            },
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}

        create_response = client.post(
            "/manuscripts/",
            headers=headers1,
            data={"title": "Owner Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Try to get with user 2
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"thief-get-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Thief",
            },
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        response = client.get(f"/manuscripts/{manuscript_id}", headers=headers2)

        assert response.status_code == 404  # Returns 404 to not leak existence


class TestUpdateManuscript:
    def test_update_manuscript_metadata(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        # Create manuscript
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Original Title", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Update it
        response = client.put(
            f"/manuscripts/{manuscript_id}",
            headers=auth_headers,
            json={"title": "Updated Title", "description": "New description"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
        assert response.json()["description"] == "New description"

    def test_update_manuscript_partial(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        # Create manuscript with description
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={
                "title": "Original",
                "source_format": "epub",
                "description": "Original desc",
            },
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Update only title
        response = client.put(
            f"/manuscripts/{manuscript_id}",
            headers=auth_headers,
            json={"title": "New Title"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "New Title"
        # Description should remain unchanged
        assert response.json()["description"] == "Original desc"


class TestMarkReady:
    def test_mark_ready_success(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        # Create manuscript
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Ready Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        assert create_response.json()["state"] == "draft"

        # Mark ready
        response = client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["state"] == "ready"

    def test_mark_ready_twice_fails(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        # Create and mark ready
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Double Ready", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        # Try again
        response = client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        assert response.status_code == 400


class TestDeleteManuscript:
    def test_delete_manuscript_success(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        # Create manuscript
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Delete Me", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/manuscripts/{manuscript_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/manuscripts/{manuscript_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_manuscript_wrong_owner(self, client: TestClient, sample_epub: bytes):
        import uuid as uuid_mod

        # Create with user 1
        response1 = client.post(
            "/auth/register",
            json={
                "email": f"owner-del-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Owner",
            },
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}

        create_response = client.post(
            "/manuscripts/",
            headers=headers1,
            data={"title": "Protected Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Try to delete with user 2
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"attacker-del-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        response = client.delete(f"/manuscripts/{manuscript_id}", headers=headers2)

        assert response.status_code == 404  # Returns 404 to not leak existence

        # Verify it still exists for owner
        get_response = client.get(f"/manuscripts/{manuscript_id}", headers=headers1)
        assert get_response.status_code == 200


class TestInputValidation:
    """Tests for malformed input handling in manuscript endpoints."""

    def test_get_manuscript_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Malformed UUID should return 404, not 500."""
        response = client.get("/manuscripts/not-a-uuid", headers=auth_headers)

        assert response.status_code == 404

    def test_get_manuscript_partial_uuid(self, client: TestClient, auth_headers: dict):
        """Partial UUID should return 404."""
        response = client.get("/manuscripts/12345", headers=auth_headers)

        assert response.status_code == 404

    def test_update_manuscript_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Update with malformed UUID should return 404."""
        response = client.put(
            "/manuscripts/not-a-uuid",
            headers=auth_headers,
            json={"title": "New Title"},
        )

        assert response.status_code == 404

    def test_delete_manuscript_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Delete with malformed UUID should return 404."""
        response = client.delete("/manuscripts/not-a-uuid", headers=auth_headers)

        assert response.status_code == 404

    def test_mark_ready_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Mark ready with malformed UUID should return 404."""
        response = client.post("/manuscripts/not-a-uuid/ready", headers=auth_headers)

        assert response.status_code == 404

    def test_create_manuscript_empty_title(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Empty title should be rejected."""
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )

        assert response.status_code == 422

    def test_create_manuscript_whitespace_title(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Whitespace-only title should be rejected."""
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "   ", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )

        # May be 422 or 400 depending on where validation happens
        assert response.status_code in (400, 422)

    def test_create_manuscript_invalid_source_format(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Invalid source format should be rejected."""
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Test Book", "source_format": "exe"},
            files={"file": ("book.exe", io.BytesIO(sample_epub), "application/octet-stream")},
        )

        assert response.status_code == 422

    def test_create_manuscript_missing_title(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Missing title should be rejected."""
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )

        assert response.status_code == 422

    def test_create_manuscript_missing_source_format(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Missing source format should be rejected."""
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Test Book"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )

        assert response.status_code == 422

    def test_create_manuscript_missing_file(self, client: TestClient, auth_headers: dict):
        """Missing file should be rejected."""
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Test Book", "source_format": "epub"},
        )

        assert response.status_code == 422

    def test_update_manuscript_empty_title(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Update with empty title should be rejected."""
        # Create manuscript first
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Original Title", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Try to update with empty title
        response = client.put(
            f"/manuscripts/{manuscript_id}",
            headers=auth_headers,
            json={"title": ""},
        )

        assert response.status_code == 422
