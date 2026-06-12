"""
Integration tests for manuscript API endpoints.
"""

import asyncio
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.storage import LocalStorageBackend

RESOURCES = Path(__file__).parent / "resources"


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


class TestMarkDraft:
    def test_mark_draft_success(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Revert Me", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        response = client.post(f"/manuscripts/{manuscript_id}/draft", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["state"] == "draft"

    def test_mark_draft_from_draft_fails(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Already Draft", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        response = client.post(f"/manuscripts/{manuscript_id}/draft", headers=auth_headers)

        assert response.status_code == 400

    def test_mark_draft_from_archived_fails(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Archived Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)
        client.post(f"/manuscripts/{manuscript_id}/archive", headers=auth_headers)

        response = client.post(f"/manuscripts/{manuscript_id}/draft", headers=auth_headers)

        assert response.status_code == 400

    def test_mark_draft_wrong_owner(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        import uuid

        other = client.post(
            "/auth/register",
            json={
                "email": f"other-{uuid.uuid4()}@example.com",
                "password": "testpassword",
                "display_name": "Other Author",
            },
        )
        other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

        create_response = client.post(
            "/manuscripts/",
            headers=other_headers,
            data={"title": "Not Yours", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=other_headers)

        response = client.post(f"/manuscripts/{manuscript_id}/draft", headers=auth_headers)

        assert response.status_code == 404

    def test_mark_draft_malformed_uuid(self, client: TestClient, auth_headers: dict):
        response = client.post("/manuscripts/not-a-uuid/draft", headers=auth_headers)

        assert response.status_code == 404

    def test_mark_draft_nonexistent(self, client: TestClient, auth_headers: dict):
        import uuid

        response = client.post(f"/manuscripts/{uuid.uuid4()}/draft", headers=auth_headers)

        assert response.status_code == 404


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


class TestSoftDelete:
    """Tests for soft delete and restore functionality."""

    def test_delete_is_soft_delete(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Deleting a manuscript should be a soft delete."""
        # Create manuscript
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Soft Delete Test", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Delete it
        delete_response = client.delete(f"/manuscripts/{manuscript_id}", headers=auth_headers)
        assert delete_response.status_code == 204

        # Should not appear in normal list
        list_response = client.get("/manuscripts/", headers=auth_headers)
        assert all(m["id"] != manuscript_id for m in list_response.json())

        # Should appear in list with include_deleted=true
        list_deleted_response = client.get(
            "/manuscripts/?include_deleted=true", headers=auth_headers
        )
        deleted_manuscripts = [m for m in list_deleted_response.json() if m["id"] == manuscript_id]
        assert len(deleted_manuscripts) == 1
        assert deleted_manuscripts[0]["deleted_at"] is not None

    def test_restore_manuscript(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Restoring a soft-deleted manuscript should make it active again."""
        # Create and delete manuscript
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Restore Test", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.delete(f"/manuscripts/{manuscript_id}", headers=auth_headers)

        # Restore it
        restore_response = client.post(
            f"/manuscripts/{manuscript_id}/restore", headers=auth_headers
        )
        assert restore_response.status_code == 200
        assert restore_response.json()["id"] == manuscript_id
        assert restore_response.json()["title"] == "Restore Test"

        # Should now appear in normal list
        list_response = client.get("/manuscripts/", headers=auth_headers)
        assert any(m["id"] == manuscript_id for m in list_response.json())

        # Should be accessible via get
        get_response = client.get(f"/manuscripts/{manuscript_id}", headers=auth_headers)
        assert get_response.status_code == 200

    def test_restore_not_found_for_wrong_owner(self, client: TestClient, sample_epub: bytes):
        """Restoring another user's deleted manuscript should return 404."""
        import uuid as uuid_mod

        # Create with user 1
        response1 = client.post(
            "/auth/register",
            json={
                "email": f"owner-restore-{uuid_mod.uuid4()}@example.com",
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

        # Delete it
        client.delete(f"/manuscripts/{manuscript_id}", headers=headers1)

        # Try to restore with user 2
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"attacker-restore-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        restore_response = client.post(
            f"/manuscripts/{manuscript_id}/restore", headers=headers2
        )
        assert restore_response.status_code == 404

    def test_cascade_delete_samples_and_ebooks(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Deleting a manuscript should cascade soft delete to samples and ebooks."""
        # Create manuscript
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Cascade Delete Test", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Mark ready for ebook generation
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        # Create a sample
        sample_response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Chapter 1 Sample",
                "excerpt_start": "1",
                "excerpt_end": "10",
            },
        )
        sample_id = sample_response.json()["id"]

        # Generate ebook for manuscript
        ebook_response = client.post(
            f"/ebooks/manuscripts/{manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        assert ebook_response.status_code == 200
        ebook_id = ebook_response.json()[0]["id"]

        # Delete manuscript
        client.delete(f"/manuscripts/{manuscript_id}", headers=auth_headers)

        # Sample should not appear in normal list
        samples_response = client.get(
            f"/samples/manuscripts/{manuscript_id}/samples?include_deleted=true",
            headers=auth_headers,
        )
        assert samples_response.status_code == 200
        samples = samples_response.json()
        deleted_sample = next((s for s in samples if s["id"] == sample_id), None)
        assert deleted_sample is not None
        assert deleted_sample["deleted_at"] is not None

        # Ebook should also be soft deleted
        ebooks_response = client.get("/ebooks/?include_deleted=true", headers=auth_headers)
        deleted_ebook = next((e for e in ebooks_response.json() if e["id"] == ebook_id), None)
        assert deleted_ebook is not None
        assert deleted_ebook["deleted_at"] is not None

    def test_cascade_restore(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Restoring a manuscript should cascade restore to samples and ebooks."""
        # Create manuscript
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Cascade Restore Test", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]

        # Mark ready for ebook generation
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        # Create a sample
        sample_response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Chapter 1 Sample",
                "excerpt_start": "1",
                "excerpt_end": "10",
            },
        )
        sample_id = sample_response.json()["id"]

        # Generate ebook
        ebook_response = client.post(
            f"/ebooks/manuscripts/{manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = ebook_response.json()[0]["id"]

        # Delete and restore manuscript
        client.delete(f"/manuscripts/{manuscript_id}", headers=auth_headers)
        client.post(f"/manuscripts/{manuscript_id}/restore", headers=auth_headers)

        # Sample should be restored
        samples_response = client.get(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
        )
        restored_sample = next((s for s in samples_response.json() if s["id"] == sample_id), None)
        assert restored_sample is not None

        # Ebook should be restored
        ebooks_response = client.get("/ebooks/", headers=auth_headers)
        restored_ebook = next((e for e in ebooks_response.json() if e["id"] == ebook_id), None)
        assert restored_ebook is not None


class TestArchiveManuscript:
    """Tests for archive and unarchive functionality."""

    def test_archive_manuscript_success(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Archiving a ready manuscript should set state to archived."""
        # Create manuscript and mark ready
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Archive Test", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        # Archive it
        response = client.post(f"/manuscripts/{manuscript_id}/archive", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["state"] == "archived"

    def test_archive_already_archived_fails(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Archiving an already archived manuscript should fail."""
        # Create manuscript, mark ready, and archive
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Already Archived Test", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)
        client.post(f"/manuscripts/{manuscript_id}/archive", headers=auth_headers)

        # Try to archive again
        response = client.post(f"/manuscripts/{manuscript_id}/archive", headers=auth_headers)

        assert response.status_code == 400

    def test_archive_wrong_owner(self, client: TestClient, sample_epub: bytes):
        """Archiving another user's manuscript should return 404."""
        import uuid as uuid_mod

        # Create with user 1
        response1 = client.post(
            "/auth/register",
            json={
                "email": f"owner-archive-{uuid_mod.uuid4()}@example.com",
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
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=headers1)

        # Try to archive with user 2
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"attacker-archive-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        response = client.post(f"/manuscripts/{manuscript_id}/archive", headers=headers2)
        assert response.status_code == 404

    def test_archive_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Archive with malformed UUID should return 404."""
        response = client.post("/manuscripts/not-a-uuid/archive", headers=auth_headers)
        assert response.status_code == 404

    def test_unarchive_manuscript_success(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Unarchiving an archived manuscript should restore it to ready state."""
        # Create, mark ready, and archive
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Unarchive Test", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)
        client.post(f"/manuscripts/{manuscript_id}/archive", headers=auth_headers)

        # Unarchive it
        response = client.post(f"/manuscripts/{manuscript_id}/unarchive", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["state"] == "ready"

    def test_unarchive_not_archived_fails(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Unarchiving a non-archived manuscript should fail."""
        # Create manuscript and mark ready (but don't archive)
        create_response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Not Archived", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = create_response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        # Try to unarchive
        response = client.post(f"/manuscripts/{manuscript_id}/unarchive", headers=auth_headers)

        assert response.status_code == 400

    def test_unarchive_wrong_owner(self, client: TestClient, sample_epub: bytes):
        """Unarchiving another user's manuscript should return 404."""
        import uuid as uuid_mod

        # Create with user 1
        response1 = client.post(
            "/auth/register",
            json={
                "email": f"owner-unarchive-{uuid_mod.uuid4()}@example.com",
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
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=headers1)
        client.post(f"/manuscripts/{manuscript_id}/archive", headers=headers1)

        # Try to unarchive with user 2
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"attacker-unarchive-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        response = client.post(f"/manuscripts/{manuscript_id}/unarchive", headers=headers2)
        assert response.status_code == 404

    def test_unarchive_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Unarchive with malformed UUID should return 404."""
        response = client.post("/manuscripts/not-a-uuid/unarchive", headers=auth_headers)
        assert response.status_code == 404


@pytest.fixture
def sample_jpeg() -> bytes:
    return (RESOURCES / "sample.jpg").read_bytes()


@pytest.fixture
def sample_png() -> bytes:
    return (RESOURCES / "sample.png").read_bytes()


@pytest.fixture
def manuscript_id(client: TestClient, auth_headers: dict, sample_epub: bytes) -> str:
    response = client.post(
        "/manuscripts/",
        headers=auth_headers,
        data={"title": "Cover Test Book", "source_format": "epub"},
        files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
    )
    assert response.status_code == 201
    return response.json()["id"]


class TestUploadCover:
    def test_upload_jpeg_cover(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cover_image_key"] is not None
        assert data["cover_image_url"] == f"/manuscripts/{manuscript_id}/cover"

    def test_upload_png_cover(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_png: bytes
    ):
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.png", io.BytesIO(sample_png), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cover_image_key"] is not None
        assert data["cover_image_url"] == f"/manuscripts/{manuscript_id}/cover"

    def test_upload_cover_key_ends_with_correct_extension(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert response.status_code == 200
        assert response.json()["cover_image_key"].endswith(".jpg")

    def test_upload_cover_wrong_extension_gets_correct_appended(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        """JPEG bytes with .bmp extension should have .jpg appended to the key."""
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.bmp", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert response.status_code == 200
        assert response.json()["cover_image_key"].endswith(".jpg")

    def test_upload_cover_no_extension_gets_correct_extension(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        """File with no extension should get .jpg appended."""
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("coverart", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert response.status_code == 200
        assert response.json()["cover_image_key"].endswith(".jpg")

    def test_upload_cover_dotted_filename_no_extension_gets_correct_extension(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        """Multi-part filename with wrong final segment gets correct extension appended."""
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.final.final", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert response.status_code == 200
        assert response.json()["cover_image_key"].endswith(".jpg")

    def test_upload_cover_stores_file(
        self,
        client: TestClient,
        auth_headers: dict,
        manuscript_id: str,
        sample_jpeg: bytes,
        test_storage: LocalStorageBackend,
    ):
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        key = response.json()["cover_image_key"]
        assert asyncio.run(test_storage.exists(key))

    def test_upload_cover_replaces_old_and_deletes_from_storage(
        self,
        client: TestClient,
        auth_headers: dict,
        manuscript_id: str,
        sample_jpeg: bytes,
        test_storage: LocalStorageBackend,
    ):
        r1 = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        old_key = r1.json()["cover_image_key"]

        r2 = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover2.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert r2.status_code == 200
        new_key = r2.json()["cover_image_key"]

        assert new_key != old_key
        assert not asyncio.run(test_storage.exists(old_key))
        assert asyncio.run(test_storage.exists(new_key))

    def test_upload_cover_not_found(
        self, client: TestClient, auth_headers: dict, sample_jpeg: bytes
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.put(
            f"/manuscripts/{fake_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert response.status_code == 404

    def test_upload_cover_wrong_owner(
        self, client: TestClient, manuscript_id: str, sample_jpeg: bytes
    ):
        import uuid as uuid_mod
        other = client.post(
            "/auth/register",
            json={
                "email": f"other-cover-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Other",
            },
        )
        other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=other_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert response.status_code == 404

    def test_upload_cover_no_auth(
        self, client: TestClient, manuscript_id: str, sample_jpeg: bytes
    ):
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        assert response.status_code == 401

    def test_upload_cover_empty_file(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(b""), "image/jpeg")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_cover_exceeds_size_limit(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        oversized = b"x" * (5 * 1024 * 1024 + 1)
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(oversized), "image/jpeg")},
        )
        assert response.status_code == 400
        assert "5" in response.json()["detail"]

    def test_upload_cover_invalid_format(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        """Non-image bytes should be rejected with a clear error."""
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        response = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "JPEG" in detail or "PNG" in detail


class TestGetCover:
    def test_get_cover_jpeg(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        response = client.get(f"/manuscripts/{manuscript_id}/cover", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert response.content == sample_jpeg

    def test_get_cover_png(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_png: bytes
    ):
        client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.png", io.BytesIO(sample_png), "image/png")},
        )
        response = client.get(f"/manuscripts/{manuscript_id}/cover", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == sample_png

    def test_get_cover_no_cover(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        response = client.get(f"/manuscripts/{manuscript_id}/cover", headers=auth_headers)
        assert response.status_code == 404
        assert "cover" in response.json()["detail"].lower()

    def test_get_cover_not_found(self, client: TestClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/manuscripts/{fake_id}/cover", headers=auth_headers)
        assert response.status_code == 404

    def test_get_cover_accessible_to_other_users(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        import uuid as uuid_mod
        client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        other = client.post(
            "/auth/register",
            json={
                "email": f"other-get-cover-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Other",
            },
        )
        other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
        response = client.get(f"/manuscripts/{manuscript_id}/cover", headers=other_headers)
        assert response.status_code == 200

    def test_get_cover_no_auth(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        response = client.get(f"/manuscripts/{manuscript_id}/cover")
        assert response.status_code == 200


class TestDeleteCover:
    def test_delete_cover_success(
        self,
        client: TestClient,
        auth_headers: dict,
        manuscript_id: str,
        sample_jpeg: bytes,
        test_storage: LocalStorageBackend,
    ):
        r = client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        key = r.json()["cover_image_key"]

        response = client.delete(f"/manuscripts/{manuscript_id}/cover", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["cover_image_key"] is None
        assert data["cover_image_url"] is None
        assert not asyncio.run(test_storage.exists(key))

    def test_delete_cover_when_no_cover_set(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        """Deleting when no cover is set should return 200 with null key."""
        response = client.delete(f"/manuscripts/{manuscript_id}/cover", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["cover_image_key"] is None

    def test_delete_cover_cover_not_accessible_after(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        client.delete(f"/manuscripts/{manuscript_id}/cover", headers=auth_headers)

        response = client.get(f"/manuscripts/{manuscript_id}/cover", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_cover_not_found(self, client: TestClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/manuscripts/{fake_id}/cover", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_cover_wrong_owner(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        import uuid as uuid_mod
        client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        other = client.post(
            "/auth/register",
            json={
                "email": f"other-del-cover-{uuid_mod.uuid4()}@example.com",
                "password": "password",
                "display_name": "Other",
            },
        )
        other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
        response = client.delete(f"/manuscripts/{manuscript_id}/cover", headers=other_headers)
        assert response.status_code == 404

    def test_delete_cover_no_auth(
        self, client: TestClient, auth_headers: dict, manuscript_id: str, sample_jpeg: bytes
    ):
        client.put(
            f"/manuscripts/{manuscript_id}/cover",
            headers=auth_headers,
            files={"file": ("cover.jpg", io.BytesIO(sample_jpeg), "image/jpeg")},
        )
        response = client.delete(f"/manuscripts/{manuscript_id}/cover")
        assert response.status_code == 401
