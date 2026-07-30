"""
Tests for application settings (app.config.Settings).

Every Settings() construction here passes _env_file=None to isolate these
tests from whatever a developer's local .env happens to contain -- these
tests must only depend on explicitly set environment variables and the
class's own defaults.
"""

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsError

from app.config import Settings


class TestCorsOrigins:
    def test_default_when_unset(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("CORS_ORIGINS", raising=False)

        settings = Settings(_env_file=None)

        assert settings.CORS_ORIGINS == [
            "http://localhost:5173",
            "http://localhost:3000",
        ]

    def test_overridden_by_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("CORS_ORIGINS", '["https://example.com"]')

        settings = Settings(_env_file=None)

        assert settings.CORS_ORIGINS == ["https://example.com"]

    def test_bare_string_rejected(self, monkeypatch: pytest.MonkeyPatch):
        """pydantic-settings parses list[str] env vars as JSON, not a bare
        or comma-separated string. This locks in that the working format is
        a JSON array -- .env.example previously documented a bare-string
        format that crashed the app on startup."""
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

        with pytest.raises(SettingsError):
            Settings(_env_file=None)


class TestStorageBackend:
    def test_accepts_local(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("STORAGE_BACKEND", "local")

        settings = Settings(_env_file=None)

        assert settings.STORAGE_BACKEND == "local"

    def test_accepts_s3(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("STORAGE_BACKEND", "s3")

        settings = Settings(_env_file=None)

        assert settings.STORAGE_BACKEND == "s3"

    def test_rejects_unknown_value(self, monkeypatch: pytest.MonkeyPatch):
        """Fails fast at settings-construction time (app startup) rather
        than lazily the first time get_storage_backend() is called."""
        monkeypatch.setenv("STORAGE_BACKEND", "gcs")

        with pytest.raises(ValidationError):
            Settings(_env_file=None)
