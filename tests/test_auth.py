"""
Tests for authentication module.
"""

from uuid import uuid4

import pytest

from app.security.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "mysecretpassword"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_different_hashes_for_same_password(self):
        password = "mysecretpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Bcrypt generates different salts each time
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    def test_create_and_decode_access_token(self):
        author_id = uuid4()
        token = create_access_token(author_id)

        payload = decode_token(token)

        assert payload["sub"] == str(author_id)
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        author_id = uuid4()
        token = create_refresh_token(author_id)

        payload = decode_token(token)

        assert payload["sub"] == str(author_id)
        assert payload["type"] == "refresh"
