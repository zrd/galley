"""
Integration tests for ebook API endpoints.
"""

import io
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import EbookModel


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register a user and return auth headers."""
    import uuid

    email = f"ebook-test-{uuid.uuid4()}@example.com"
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
    return b"PK\x03\x04" + b"fake epub content" * 100


@pytest.fixture
def ready_manuscript_id(client: TestClient, auth_headers: dict, sample_epub: bytes) -> str:
    """Create a manuscript in READY state and return its ID."""
    # Create manuscript
    response = client.post(
        "/manuscripts/",
        headers=auth_headers,
        data={"title": "Test Book for Ebooks", "source_format": "epub"},
        files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
    )
    manuscript_id = response.json()["id"]

    # Mark ready
    client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

    return manuscript_id


class TestListEbooks:
    def test_list_ebooks_empty(self, client: TestClient, auth_headers: dict):
        response = client.get("/ebooks/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_ebooks_with_items(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """List ebooks after generating some."""
        # Generate an ebook
        client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )

        # List ebooks
        response = client.get("/ebooks/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["output_format"] == "epub"

    def test_list_ebooks_only_own(self, client: TestClient, sample_epub: bytes):
        """Users only see their own ebooks."""
        import uuid

        # Create and generate ebook for user 1
        response1 = client.post(
            "/auth/register",
            json={
                "email": f"user1-list-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "User 1",
            },
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}

        # Create manuscript, mark ready, generate ebook
        manuscript_resp = client.post(
            "/manuscripts/",
            headers=headers1,
            data={"title": "User 1 Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        mid1 = manuscript_resp.json()["id"]
        client.post(f"/manuscripts/{mid1}/ready", headers=headers1)
        client.post(
            f"/ebooks/manuscripts/{mid1}/generate",
            headers=headers1,
            json={"output_formats": ["epub"]},
        )

        # Create user 2 (no ebooks)
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"user2-list-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "User 2",
            },
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        # User 1 sees their ebook
        list1 = client.get("/ebooks/", headers=headers1).json()
        assert len(list1) == 1

        # User 2 sees empty list
        list2 = client.get("/ebooks/", headers=headers2).json()
        assert len(list2) == 0


class TestGetEbook:
    def test_get_ebook_success(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Get ebook metadata after generation."""
        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]

        # Get ebook
        response = client.get(f"/ebooks/{ebook_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ebook_id
        assert data["output_format"] == "epub"
        assert data["manuscript_id"] == ready_manuscript_id

    def test_get_ebook_not_found(self, client: TestClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/ebooks/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    def test_get_ebook_wrong_owner(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Cannot get another user's ebook metadata."""
        import uuid

        # Generate ebook as first user
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]

        # Register second user
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"attacker-get-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        attacker_headers = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        # Try to get ebook as second user
        response = client.get(f"/ebooks/{ebook_id}", headers=attacker_headers)

        assert response.status_code == 404


class TestGenerateEbooks:
    def test_generate_ebook_not_ready(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Cannot generate ebook from draft manuscript."""
        # Create manuscript (draft state)
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Draft Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = response.json()["id"]

        # Try to generate ebook
        response = client.post(
            f"/ebooks/manuscripts/{manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )

        assert response.status_code == 400
        assert "ready" in response.json()["detail"].lower()

    def test_generate_ebook_success(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Successfully generate ebook from ready manuscript."""
        # Generate ebook (epub → epub doesn't require Pandoc)
        response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["output_format"] == "epub"
        assert data[0]["manuscript_id"] == ready_manuscript_id
        assert data[0]["sample_id"] is None
        assert data[0]["file_size_bytes"] > 0
        assert data[0]["download_count"] == 0

    def test_generate_multiple_formats(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Generate ebooks in multiple formats."""
        # Note: only epub works without Pandoc (same-format passthrough)
        response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_generate_ebook_wrong_owner(
        self, client: TestClient, ready_manuscript_id: str
    ):
        """Cannot generate ebook for another user's manuscript."""
        import uuid

        # Register another user
        register_response = client.post(
            "/auth/register",
            json={
                "email": f"attacker-gen-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        attacker_headers = {
            "Authorization": f"Bearer {register_response.json()['access_token']}"
        }

        # Try to generate ebook
        response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=attacker_headers,
            json={"output_formats": ["epub"]},
        )

        assert response.status_code == 404

    def test_generated_ebook_has_default_prices(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Newly generated ebooks have null prices and USD currency."""
        response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )

        assert response.status_code == 200
        ebook = response.json()[0]
        assert ebook["list_price_cents"] is None
        assert ebook["sale_price_cents"] is None
        assert ebook["price_currency"] == "USD"

    def test_generate_succeeds_for_title_containing_path_separator(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ):
        """Manuscript titles are historical metadata, not live upload input —
        a '/' in a title must be silently sanitized out of the derived
        storage key, never rejected (see BUG-009's reject_unsafe design)."""
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Choose Your Path: A/B Testing", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)

        response = client.post(
            f"/ebooks/manuscripts/{manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )

        assert response.status_code == 200
        ebook_id = response.json()[0]["id"]

        # Full round trip: the sanitized storage key must actually be
        # retrievable, not just accepted at generation time.
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)
        download = client.get(f"/ebooks/{ebook_id}/download")

        assert download.status_code == 200
        assert len(download.content) > 0
        # Content-Disposition filename is a separate sanitizer
        # (_sanitize_download_filename) from the storage key -- confirm it
        # also stripped the '/' rather than passing it through raw.
        assert "/" not in download.headers["content-disposition"]


class TestDownloadEbook:
    def test_download_nonexistent_ebook(self, client: TestClient):
        """Downloading nonexistent ebook returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/ebooks/{fake_id}/download")

        assert response.status_code == 404

    def test_download_with_tracking_code(self, client: TestClient):
        """Download endpoint accepts tracking code parameter."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/ebooks/{fake_id}/download?t=event123")

        # Should still be 404 (ebook doesn't exist), but tracking param is accepted
        assert response.status_code == 404

    def test_download_ebook_success(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Successfully download a generated ebook."""
        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)

        # Download ebook (no auth required)
        response = client.get(f"/ebooks/{ebook_id}/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/epub+zip"
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.content) > 0

    def test_download_increments_count(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Download count is incremented on each download."""
        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]
        assert generate_response.json()[0]["download_count"] == 0
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)

        # Download twice
        client.get(f"/ebooks/{ebook_id}/download")
        client.get(f"/ebooks/{ebook_id}/download")

        # Check count increased
        get_response = client.get(f"/ebooks/{ebook_id}", headers=auth_headers)
        assert get_response.json()["download_count"] == 2

    def test_download_with_tracking_code_recorded(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Download with tracking code is recorded."""
        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)

        # Download with tracking code
        response = client.get(f"/ebooks/{ebook_id}/download?t=campaign123")

        assert response.status_code == 200
        # Tracking is recorded internally - just verify download succeeds

    def test_download_ebook_missing_file(
        self,
        client: TestClient,
        auth_headers: dict,
        ready_manuscript_id: str,
        test_storage,
    ):
        """Returns 404 when the ebook record exists but file is gone from storage."""
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)

        # Delete every file in storage so the ebook file is missing
        for f in test_storage.base_path.rglob("*"):
            if f.is_file():
                f.unlink()

        response = client.get(f"/ebooks/{ebook_id}/download")
        assert response.status_code == 404

    def test_download_unsafe_stored_key_returns_404(
        self,
        client: TestClient,
        auth_headers: dict,
        ready_manuscript_id: str,
        db_session: Session,
    ):
        """Defense-in-depth: even if a stored key were somehow unsafe (can't
        happen through generation, which always sanitizes), get_url raising
        UnsafeStorageKey must map to 404, not an unhandled 500."""
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)

        ebook = db_session.get(EbookModel, UUID(ebook_id))
        ebook.file_key = "../../etc/passwd"
        db_session.commit()

        response = client.get(f"/ebooks/{ebook_id}/download")
        assert response.status_code == 404


class TestDeleteEbook:
    def test_delete_nonexistent_ebook(self, client: TestClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/ebooks/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_ebook_success(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Successfully delete a generated ebook."""
        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]

        # Delete it
        response = client.delete(f"/ebooks/{ebook_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/ebooks/{ebook_id}", headers=auth_headers)
        assert get_response.status_code == 404

        # Download also fails
        download_response = client.get(f"/ebooks/{ebook_id}/download")
        assert download_response.status_code == 404

    def test_delete_ebook_wrong_owner(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Cannot delete another user's ebook."""
        import uuid

        # Generate ebook as first user
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]

        # Register second user
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"attacker-del-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        attacker_headers = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        # Try to delete as second user
        response = client.delete(f"/ebooks/{ebook_id}", headers=attacker_headers)

        assert response.status_code == 404

        # Verify it still exists for owner
        get_response = client.get(f"/ebooks/{ebook_id}", headers=auth_headers)
        assert get_response.status_code == 200


class TestInputValidation:
    """Tests for malformed input handling in ebook endpoints."""

    def test_get_ebook_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Malformed UUID should return 422."""
        response = client.get("/ebooks/not-a-uuid", headers=auth_headers)

        assert response.status_code == 422

    def test_delete_ebook_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Delete with malformed UUID should return 422."""
        response = client.delete("/ebooks/not-a-uuid", headers=auth_headers)

        assert response.status_code == 422

    def test_download_ebook_malformed_uuid(self, client: TestClient):
        """Download with malformed UUID should return 422."""
        response = client.get("/ebooks/not-a-uuid/download")

        assert response.status_code == 422

    def test_generate_ebook_malformed_manuscript_uuid(
        self, client: TestClient, auth_headers: dict
    ):
        """Generate ebook with malformed manuscript UUID should return 422."""
        response = client.post(
            "/ebooks/manuscripts/not-a-uuid/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )

        assert response.status_code == 422



class TestEbookSoftDelete:
    """Tests for ebook soft delete and restore functionality."""

    def test_delete_is_soft_delete(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Deleting an ebook should be a soft delete."""
        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]

        # Delete it
        delete_response = client.delete(f"/ebooks/{ebook_id}", headers=auth_headers)
        assert delete_response.status_code == 204

        # Should not appear in normal list
        list_response = client.get("/ebooks/", headers=auth_headers)
        assert all(e["id"] != ebook_id for e in list_response.json())

        # Should appear in list with include_deleted=true
        list_deleted_response = client.get(
            "/ebooks/?include_deleted=true", headers=auth_headers
        )
        deleted_ebooks = [e for e in list_deleted_response.json() if e["id"] == ebook_id]
        assert len(deleted_ebooks) == 1
        assert deleted_ebooks[0]["deleted_at"] is not None

    def test_download_deleted_ebook_fails(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Cannot download a soft-deleted ebook."""
        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]

        # Delete it
        client.delete(f"/ebooks/{ebook_id}", headers=auth_headers)

        # Download should fail
        download_response = client.get(f"/ebooks/{ebook_id}/download")
        assert download_response.status_code == 404

    def test_restore_ebook(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Restoring a soft-deleted ebook should make it downloadable again."""
        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)

        # Delete it
        client.delete(f"/ebooks/{ebook_id}", headers=auth_headers)

        # Restore it
        restore_response = client.post(
            f"/ebooks/{ebook_id}/restore", headers=auth_headers
        )
        assert restore_response.status_code == 200
        assert restore_response.json()["id"] == ebook_id

        # Should now appear in normal list
        list_response = client.get("/ebooks/", headers=auth_headers)
        assert any(e["id"] == ebook_id for e in list_response.json())

        # Download should work again
        download_response = client.get(f"/ebooks/{ebook_id}/download")
        assert download_response.status_code == 200

    def test_restore_ebook_wrong_owner(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Cannot restore another user's soft-deleted ebook."""
        import uuid

        # Generate ebook
        generate_response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = generate_response.json()[0]["id"]

        # Delete it
        client.delete(f"/ebooks/{ebook_id}", headers=auth_headers)

        # Register second user
        response2 = client.post(
            "/auth/register",
            json={
                "email": f"attacker-restore-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        attacker_headers = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        # Try to restore as second user
        restore_response = client.post(
            f"/ebooks/{ebook_id}/restore", headers=attacker_headers
        )
        assert restore_response.status_code == 404


class TestPatchEbookPrice:
    @pytest.fixture
    def ebook_id(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ) -> str:
        response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        return response.json()[0]["id"]

    def test_set_list_price(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.patch(
            f"/ebooks/{ebook_id}",
            headers=auth_headers,
            json={"list_price_cents": 999},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["list_price_cents"] == 999
        assert data["sale_price_cents"] is None

    def test_set_sale_price_does_not_clear_list_price(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"list_price_cents": 999},
        )
        response = client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"sale_price_cents": 799},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["list_price_cents"] == 999
        assert data["sale_price_cents"] == 799

    def test_clear_sale_price_does_not_clear_list_price(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"list_price_cents": 999, "sale_price_cents": 799},
        )
        response = client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"sale_price_cents": None},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sale_price_cents"] is None
        assert data["list_price_cents"] == 999

    def test_list_price_zero_accepted(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"list_price_cents": 0},
        )

        assert response.status_code == 200
        assert response.json()["list_price_cents"] == 0

    def test_list_price_negative_rejected(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"list_price_cents": -1},
        )
        assert response.status_code == 422

    def test_list_price_too_large_rejected(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"list_price_cents": 100000},
        )
        assert response.status_code == 422

    def test_sale_price_negative_rejected(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"sale_price_cents": -1},
        )
        assert response.status_code == 422

    def test_sale_price_too_large_rejected(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"sale_price_cents": 100000},
        )
        assert response.status_code == 422

    def test_wrong_author_returns_404(
        self, client: TestClient, ebook_id: str
    ):
        import uuid

        response = client.post(
            "/auth/register",
            json={
                "email": f"other-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "Other Author",
            },
        )
        other_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        response = client.patch(
            f"/ebooks/{ebook_id}", headers=other_headers,
            json={"list_price_cents": 999},
        )
        assert response.status_code == 404


class TestEbookVisibility:
    @pytest.fixture
    def ebook_id(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ) -> str:
        response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        return response.json()[0]["id"]

    def test_new_ebook_has_private_visibility(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.get(f"/ebooks/{ebook_id}", headers=auth_headers)
        assert response.json()["visibility"] == "private"
        assert response.json()["published_at"] is None

    def test_publish_sets_visibility(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["visibility"] == "published"

    def test_publish_sets_published_at(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)
        assert response.json()["published_at"] is not None

    def test_publish_twice_does_not_reset_published_at(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        first = client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)
        first_published_at = first.json()["published_at"].rstrip("Z")

        client.post(f"/ebooks/{ebook_id}/make-private", headers=auth_headers)
        second = client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)

        assert second.json()["published_at"].rstrip("Z") == first_published_at

    def test_unlist_sets_visibility(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.post(f"/ebooks/{ebook_id}/unlist", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["visibility"] == "unlisted"

    def test_make_private_sets_visibility(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)
        response = client.post(f"/ebooks/{ebook_id}/make-private", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["visibility"] == "private"

    def test_publish_wrong_owner_returns_404(
        self, client: TestClient, ebook_id: str
    ):
        import uuid
        response = client.post(
            "/auth/register",
            json={
                "email": f"attacker-vis-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        attacker_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        assert client.post(f"/ebooks/{ebook_id}/publish", headers=attacker_headers).status_code == 404

    def test_unlist_wrong_owner_returns_404(
        self, client: TestClient, ebook_id: str
    ):
        import uuid
        response = client.post(
            "/auth/register",
            json={
                "email": f"attacker-vis-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        attacker_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        assert client.post(f"/ebooks/{ebook_id}/unlist", headers=attacker_headers).status_code == 404

    def test_make_private_wrong_owner_returns_404(
        self, client: TestClient, ebook_id: str
    ):
        import uuid
        response = client.post(
            "/auth/register",
            json={
                "email": f"attacker-vis-{uuid.uuid4()}@example.com",
                "password": "password",
                "display_name": "Attacker",
            },
        )
        attacker_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        assert client.post(f"/ebooks/{ebook_id}/make-private", headers=attacker_headers).status_code == 404

    def test_publish_deleted_ebook_returns_404(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        client.delete(f"/ebooks/{ebook_id}", headers=auth_headers)
        response = client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)
        assert response.status_code == 404

    def test_publish_malformed_uuid(self, client: TestClient, auth_headers: dict):
        assert client.post("/ebooks/not-a-uuid/publish", headers=auth_headers).status_code == 422

    def test_unlist_malformed_uuid(self, client: TestClient, auth_headers: dict):
        assert client.post("/ebooks/not-a-uuid/unlist", headers=auth_headers).status_code == 422

    def test_make_private_malformed_uuid(self, client: TestClient, auth_headers: dict):
        assert client.post("/ebooks/not-a-uuid/make-private", headers=auth_headers).status_code == 422

    def test_publish_requires_auth(self, client: TestClient, ebook_id: str):
        assert client.post(f"/ebooks/{ebook_id}/publish").status_code == 401

    def test_unlist_requires_auth(self, client: TestClient, ebook_id: str):
        assert client.post(f"/ebooks/{ebook_id}/unlist").status_code == 401

    def test_make_private_requires_auth(self, client: TestClient, ebook_id: str):
        assert client.post(f"/ebooks/{ebook_id}/make-private").status_code == 401

    def test_book_fair_scenario(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Two ebooks under the same manuscript can have independent visibility."""
        paid = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        ).json()[0]["id"]

        free = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        ).json()[0]["id"]

        client.post(f"/ebooks/{paid}/publish", headers=auth_headers)
        client.post(f"/ebooks/{free}/unlist", headers=auth_headers)

        assert client.get(f"/ebooks/{paid}", headers=auth_headers).json()["visibility"] == "published"
        assert client.get(f"/ebooks/{free}", headers=auth_headers).json()["visibility"] == "unlisted"

    def test_cannot_change_visibility_after_manuscript_deleted(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ):
        """Soft-deleting a manuscript cascades to its ebooks; deleted ebooks cannot be modified."""
        ebook_id = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        ).json()[0]["id"]

        client.delete(f"/manuscripts/{ready_manuscript_id}", headers=auth_headers)

        assert client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers).status_code == 404


class TestDraftDownloadGate:
    @pytest.fixture
    def manuscript_with_ebook(
        self, client: TestClient, auth_headers: dict, sample_epub: bytes
    ) -> tuple[str, str]:
        """Ready manuscript with one generated ebook. Returns (manuscript_id, ebook_id)."""
        response = client.post(
            "/manuscripts/",
            headers=auth_headers,
            data={"title": "Gate Test Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
        )
        manuscript_id = response.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)
        gen = client.post(
            f"/ebooks/manuscripts/{manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        ebook_id = gen.json()[0]["id"]
        return manuscript_id, ebook_id

    def test_download_blocked_when_manuscript_in_draft(
        self, client: TestClient, auth_headers: dict, manuscript_with_ebook: tuple[str, str]
    ):
        manuscript_id, ebook_id = manuscript_with_ebook

        client.post(f"/manuscripts/{manuscript_id}/draft", headers=auth_headers)

        response = client.get(f"/ebooks/{ebook_id}/download")

        assert response.status_code == 403

    def test_download_round_trip(
        self, client: TestClient, auth_headers: dict, manuscript_with_ebook: tuple[str, str]
    ):
        manuscript_id, ebook_id = manuscript_with_ebook
        client.post(f"/ebooks/{ebook_id}/publish", headers=auth_headers)

        # READY — gate is open
        assert client.get(f"/ebooks/{ebook_id}/download").status_code != 403

        # Revert to DRAFT — gate closes
        client.post(f"/manuscripts/{manuscript_id}/draft", headers=auth_headers)
        assert client.get(f"/ebooks/{ebook_id}/download").status_code == 403

        # Mark READY again — gate reopens
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=auth_headers)
        assert client.get(f"/ebooks/{ebook_id}/download").status_code != 403


class TestDownloadVisibilityAPI:
    """Thin end-to-end checks for the download endpoint's visibility gate.

    Most of the gating logic (visibility branching, limit comparison, draft
    ordering) is covered directly against EbookService in TestGetForDownload
    (test_services.py). These only verify what requires real HTTP: exception
    to status-code mapping, bearer-token wiring via OptionalAuthorId, and the
    endpoint's own increment-after-gate control flow.
    """

    @pytest.fixture
    def ebook_id(
        self, client: TestClient, auth_headers: dict, ready_manuscript_id: str
    ) -> str:
        response = client.post(
            f"/ebooks/manuscripts/{ready_manuscript_id}/generate",
            headers=auth_headers,
            json={"output_formats": ["epub"]},
        )
        return response.json()[0]["id"]

    def test_private_download_unauthenticated_returns_403(
        self, client: TestClient, ebook_id: str
    ):
        response = client.get(f"/ebooks/{ebook_id}/download")
        assert response.status_code == 403

    def test_unlisted_download_limit_exceeded_returns_403(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        client.post(f"/ebooks/{ebook_id}/unlist", headers=auth_headers)
        client.patch(
            f"/ebooks/{ebook_id}", headers=auth_headers,
            json={"unlisted_download_limit": 1},
        )
        client.get(f"/ebooks/{ebook_id}/download")  # consumes the one allowed download

        response = client.get(f"/ebooks/{ebook_id}/download")

        assert response.status_code == 403

    def test_private_download_owner_succeeds(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        response = client.get(f"/ebooks/{ebook_id}/download", headers=auth_headers)
        assert response.status_code == 200

    def test_rejected_download_does_not_increment_count(
        self, client: TestClient, auth_headers: dict, ebook_id: str
    ):
        client.get(f"/ebooks/{ebook_id}/download")  # unauthenticated, private -> 403

        get_response = client.get(f"/ebooks/{ebook_id}", headers=auth_headers)

        assert get_response.json()["download_count"] == 0
