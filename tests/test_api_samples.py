"""
Integration tests for sample API endpoints.
"""

import io

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register a user and return auth headers."""
    import uuid

    email = f"sample-test-{uuid.uuid4()}@example.com"
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
def manuscript_id(client: TestClient, auth_headers: dict, sample_epub: bytes) -> str:
    """Create a manuscript and return its ID."""
    response = client.post(
        "/manuscripts/",
        headers=auth_headers,
        data={"title": "Test Book for Samples", "source_format": "epub"},
        files={"file": ("book.epub", io.BytesIO(sample_epub), "application/epub+zip")},
    )
    return response.json()["id"]


class TestCreateSample:
    def test_create_sample_success(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Free Preview",
                "excerpt_start": "Chapter 1",
                "excerpt_end": "Chapter 3",
                "promo_header": "Enjoy this free sample!",
                "promo_footer": "Buy the full book at example.com",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Free Preview"
        assert data["excerpt_start"] == "Chapter 1"
        assert data["excerpt_end"] == "Chapter 3"
        assert data["promo_header"] == "Enjoy this free sample!"
        assert data["promo_footer"] == "Buy the full book at example.com"
        assert data["manuscript_id"] == manuscript_id

    def test_create_sample_minimal(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Quick Sample",
                "excerpt_start": "1",
                "excerpt_end": "10",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["promo_header"] is None
        assert data["promo_footer"] is None

    def test_create_sample_wrong_manuscript(self, client: TestClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.post(
            f"/samples/manuscripts/{fake_id}/samples",
            headers=auth_headers,
            json={
                "title": "Orphan Sample",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )

        assert response.status_code == 404


class TestListSamples:
    def test_list_samples_empty(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        response = client.get(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_list_samples_with_items(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        # Create samples
        for i in range(3):
            client.post(
                f"/samples/manuscripts/{manuscript_id}/samples",
                headers=auth_headers,
                json={
                    "title": f"Sample {i}",
                    "excerpt_start": f"Chapter {i}",
                    "excerpt_end": f"Chapter {i + 1}",
                },
            )

        response = client.get(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert len(response.json()) == 3


class TestGetSample:
    def test_get_sample_success(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        # Create sample
        create_response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Get Test Sample",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )
        sample_id = create_response.json()["id"]

        # Get it
        response = client.get(f"/samples/{sample_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["id"] == sample_id
        assert response.json()["title"] == "Get Test Sample"

    def test_get_sample_not_found(self, client: TestClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/samples/{fake_id}", headers=auth_headers)

        assert response.status_code == 404


class TestUpdateSample:
    def test_update_sample_success(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        # Create sample
        create_response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Original Sample",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )
        sample_id = create_response.json()["id"]

        # Update it
        response = client.put(
            f"/samples/{sample_id}",
            headers=auth_headers,
            json={
                "title": "Updated Sample",
                "excerpt_start": "2",
                "excerpt_end": "10",
                "promo_footer": "New promo!",
            },
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Sample"
        assert response.json()["excerpt_start"] == "2"
        assert response.json()["excerpt_end"] == "10"
        assert response.json()["promo_footer"] == "New promo!"


class TestDeleteSample:
    def test_delete_sample_success(
        self, client: TestClient, auth_headers: dict, manuscript_id: str
    ):
        # Create sample
        create_response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Delete Me",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )
        sample_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/samples/{sample_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/samples/{sample_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestSampleOwnership:
    """Tests verifying that users cannot access other users' samples."""

    @pytest.fixture
    def other_user_headers(self, client: TestClient) -> dict[str, str]:
        """Register a second user and return their auth headers."""
        import uuid

        email = f"other-sample-{uuid.uuid4()}@example.com"
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "testpassword",
                "display_name": "Other Author",
            },
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_sample_wrong_owner(
        self,
        client: TestClient,
        auth_headers: dict,
        manuscript_id: str,
        other_user_headers: dict,
    ):
        """User cannot get another user's sample."""
        # Create sample as first user
        create_response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Private Sample",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )
        sample_id = create_response.json()["id"]

        # Try to get it as second user
        response = client.get(f"/samples/{sample_id}", headers=other_user_headers)

        assert response.status_code == 404  # Returns 404 to not leak existence

    def test_update_sample_wrong_owner(
        self,
        client: TestClient,
        auth_headers: dict,
        manuscript_id: str,
        other_user_headers: dict,
    ):
        """User cannot update another user's sample."""
        # Create sample as first user
        create_response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Original Title",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )
        sample_id = create_response.json()["id"]

        # Try to update it as second user
        response = client.put(
            f"/samples/{sample_id}",
            headers=other_user_headers,
            json={"title": "Hacked Title"},
        )

        assert response.status_code == 404

        # Verify original is unchanged
        get_response = client.get(f"/samples/{sample_id}", headers=auth_headers)
        assert get_response.json()["title"] == "Original Title"

    def test_delete_sample_wrong_owner(
        self,
        client: TestClient,
        auth_headers: dict,
        manuscript_id: str,
        other_user_headers: dict,
    ):
        """User cannot delete another user's sample."""
        # Create sample as first user
        create_response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Protected Sample",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )
        sample_id = create_response.json()["id"]

        # Try to delete it as second user
        response = client.delete(f"/samples/{sample_id}", headers=other_user_headers)

        assert response.status_code == 404

        # Verify it still exists for owner
        get_response = client.get(f"/samples/{sample_id}", headers=auth_headers)
        assert get_response.status_code == 200

    def test_list_samples_wrong_owner(
        self,
        client: TestClient,
        auth_headers: dict,
        manuscript_id: str,
        other_user_headers: dict,
    ):
        """User cannot list samples for another user's manuscript."""
        # Create sample as first user
        client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=auth_headers,
            json={
                "title": "Secret Sample",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )

        # Try to list samples as second user
        response = client.get(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=other_user_headers,
        )

        assert response.status_code == 404

    def test_create_sample_wrong_manuscript_owner(
        self,
        client: TestClient,
        manuscript_id: str,
        other_user_headers: dict,
    ):
        """User cannot create a sample on another user's manuscript."""
        response = client.post(
            f"/samples/manuscripts/{manuscript_id}/samples",
            headers=other_user_headers,
            json={
                "title": "Unauthorized Sample",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )

        assert response.status_code == 404


class TestInputValidation:
    """Tests for malformed input handling in sample endpoints."""

    def test_get_sample_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Malformed UUID should return 404, not 500."""
        response = client.get("/samples/not-a-uuid", headers=auth_headers)

        assert response.status_code == 404

    def test_update_sample_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Update with malformed UUID should return 404."""
        response = client.put(
            "/samples/not-a-uuid",
            headers=auth_headers,
            json={"title": "New Title"},
        )

        assert response.status_code == 404

    def test_delete_sample_malformed_uuid(self, client: TestClient, auth_headers: dict):
        """Delete with malformed UUID should return 404."""
        response = client.delete("/samples/not-a-uuid", headers=auth_headers)

        assert response.status_code == 404

    def test_list_samples_malformed_manuscript_uuid(
        self, client: TestClient, auth_headers: dict
    ):
        """List samples with malformed manuscript UUID should return 404."""
        response = client.get(
            "/samples/manuscripts/not-a-uuid/samples",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_create_sample_malformed_manuscript_uuid(
        self, client: TestClient, auth_headers: dict
    ):
        """Create sample with malformed manuscript UUID should return 404."""
        response = client.post(
            "/samples/manuscripts/not-a-uuid/samples",
            headers=auth_headers,
            json={
                "title": "Test Sample",
                "excerpt_start": "1",
                "excerpt_end": "5",
            },
        )

        assert response.status_code == 404

