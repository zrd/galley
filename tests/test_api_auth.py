"""
Integration tests for authentication API endpoints.
"""

import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.security.auth import create_access_token, create_refresh_token


def unique_email(prefix: str = "test") -> str:
    """Generate a unique email address for testing."""
    return f"{prefix}-{uuid.uuid4()}@example.com"


class TestRegister:
    def test_register_success(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": unique_email("newuser"),
                "password": "securepassword123",
                "display_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client: TestClient):
        email = unique_email("duplicate")
        # First registration
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "password123",
                "display_name": "First User",
            },
        )

        # Second registration with same email
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "password456",
                "display_name": "Second User",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422  # Validation error


class TestLogin:
    def test_login_success(self, client: TestClient):
        email = unique_email("logintest")
        # Register first
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "mypassword",
                "display_name": "Login Test",
            },
        )

        # Then login
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "mypassword",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self, client: TestClient):
        email = unique_email("wrongpw")
        # Register first
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "correctpassword",
                "display_name": "Test User",
            },
        )

        # Login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post(
            "/auth/login",
            json={
                "email": unique_email("nonexistent"),
                "password": "password",
            },
        )

        assert response.status_code == 401


class TestRefresh:
    def test_refresh_token_success(self, client: TestClient):
        # Register to get tokens
        register_response = client.post(
            "/auth/register",
            json={
                "email": unique_email("refreshtest"),
                "password": "password123",
                "display_name": "Refresh Test",
            },
        )
        refresh_token = register_response.json()["refresh_token"]

        # Use refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_access_token_fails(self, client: TestClient):
        # Register to get tokens
        register_response = client.post(
            "/auth/register",
            json={
                "email": unique_email("refreshfail"),
                "password": "password123",
                "display_name": "Refresh Fail Test",
            },
        )
        access_token = register_response.json()["access_token"]

        # Try to use access token as refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401

    def test_refresh_with_invalid_token(self, client: TestClient):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401


class TestAuthenticatedEndpoints:
    def test_access_protected_endpoint_without_token(self, client: TestClient):
        response = client.get("/authors/me")
        assert response.status_code == 401

    def test_access_protected_endpoint_with_valid_token(self, client: TestClient):
        email = unique_email("protected")
        # Register to get token
        register_response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "password123",
                "display_name": "Protected Test",
            },
        )
        access_token = register_response.json()["access_token"]

        # Access protected endpoint
        response = client.get(
            "/authors/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == email

    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient):
        response = client.get(
            "/authors/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401


class TestInputValidation:
    """Tests for malformed input handling in auth endpoints."""

    def test_register_empty_email(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": "",
                "password": "password123",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_whitespace_email(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": "   ",
                "password": "password123",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_empty_password(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": unique_email("emptypass"),
                "password": "",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_empty_display_name(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": unique_email("emptyname"),
                "password": "password123",
                "display_name": "",
            },
        )

        # May be 422 (validation) or 400 (business rule) depending on implementation
        assert response.status_code in (400, 422)

    def test_register_whitespace_display_name(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": unique_email("wsname"),
                "password": "password123",
                "display_name": "   ",
            },
        )

        # May be 422 (validation) or 400 (business rule) depending on implementation
        assert response.status_code in (400, 422)

    def test_register_missing_email_field(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "password": "password123",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_missing_password_field(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": unique_email("nopass"),
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422

    def test_login_empty_email(self, client: TestClient):
        response = client.post(
            "/auth/login",
            json={
                "email": "",
                "password": "password123",
            },
        )

        assert response.status_code == 422

    def test_login_empty_password(self, client: TestClient):
        response = client.post(
            "/auth/login",
            json={
                "email": unique_email("loginempty"),
                "password": "",
            },
        )

        assert response.status_code == 422

    def test_refresh_empty_token(self, client: TestClient):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": ""},
        )

        assert response.status_code in (401, 422)


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_expired_access_token_rejected(self, client: TestClient):
        """Expired access token should return 401."""
        # Create an already-expired token
        author_id = uuid.uuid4()
        expired_token = create_access_token(
            author_id, expires_delta=timedelta(seconds=-1)
        )

        response = client.get(
            "/authors/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_expired_refresh_token_rejected(self, client: TestClient):
        """Expired refresh token should return 401."""
        # Create an already-expired refresh token
        author_id = uuid.uuid4()
        expired_token = create_refresh_token(
            author_id, expires_delta=timedelta(seconds=-1)
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": expired_token},
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_access_token_valid_until_expiry(self, client: TestClient):
        """Access token should work before expiration."""
        # Register to create a real user and get a valid token
        email = unique_email("expiry-test")
        register_response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "password123",
                "display_name": "Expiry Test",
            },
        )
        access_token = register_response.json()["access_token"]

        # Token should be valid immediately after creation
        response = client.get(
            "/authors/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == email

    def test_refresh_token_valid_until_expiry(self, client: TestClient):
        """Refresh token should work before expiration."""
        # Register to get a valid refresh token
        register_response = client.post(
            "/auth/register",
            json={
                "email": unique_email("refresh-expiry"),
                "password": "password123",
                "display_name": "Refresh Test",
            },
        )
        refresh_token = register_response.json()["refresh_token"]

        # Refresh token should be valid immediately
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_expired_token_on_manuscript_endpoint(self, client: TestClient):
        """Expired token should be rejected on resource endpoints too."""
        author_id = uuid.uuid4()
        expired_token = create_access_token(
            author_id, expires_delta=timedelta(seconds=-1)
        )

        response = client.get(
            "/manuscripts/",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_expired_token_on_ebook_endpoint(self, client: TestClient):
        """Expired token should be rejected on ebook endpoints."""
        author_id = uuid.uuid4()
        expired_token = create_access_token(
            author_id, expires_delta=timedelta(seconds=-1)
        )

        response = client.get(
            "/ebooks/",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
