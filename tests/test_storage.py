"""
Tests for the storage backend.
"""

import tempfile
from pathlib import Path

import pytest

from app.storage import LocalStorageBackend, generate_file_key, get_content_type_for_format


class TestLocalStorageBackend:
    @pytest.fixture
    def storage(self) -> LocalStorageBackend:
        """Create a storage backend with a temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield LocalStorageBackend(temp_dir)

    @pytest.mark.asyncio
    async def test_upload_and_download(self, storage: LocalStorageBackend):
        content = b"Hello, World!"
        key = "test/hello.txt"

        # Upload
        result_key = await storage.upload(key, content, "text/plain")
        assert result_key == key

        # Download
        downloaded = await storage.download(key)
        assert downloaded == content

    @pytest.mark.asyncio
    async def test_exists(self, storage: LocalStorageBackend):
        key = "test/exists.txt"

        # Doesn't exist yet
        assert not await storage.exists(key)

        # Upload
        await storage.upload(key, b"content", "text/plain")

        # Now exists
        assert await storage.exists(key)

    @pytest.mark.asyncio
    async def test_delete(self, storage: LocalStorageBackend):
        key = "test/delete.txt"

        # Upload
        await storage.upload(key, b"content", "text/plain")
        assert await storage.exists(key)

        # Delete
        await storage.delete(key)
        assert not await storage.exists(key)

    @pytest.mark.asyncio
    async def test_get_size(self, storage: LocalStorageBackend):
        content = b"12345678901234567890"  # 20 bytes
        key = "test/size.txt"

        await storage.upload(key, content, "text/plain")

        size = await storage.get_size(key)
        assert size == 20

    @pytest.mark.asyncio
    async def test_download_nonexistent(self, storage: LocalStorageBackend):
        with pytest.raises(FileNotFoundError):
            await storage.download("nonexistent/file.txt")

    @pytest.mark.asyncio
    async def test_get_size_nonexistent(self, storage: LocalStorageBackend):
        with pytest.raises(FileNotFoundError):
            await storage.get_size("nonexistent/file.txt")

    @pytest.mark.asyncio
    async def test_nested_directories(self, storage: LocalStorageBackend):
        key = "a/b/c/d/deep.txt"
        content = b"deep content"

        await storage.upload(key, content, "text/plain")
        downloaded = await storage.download(key)

        assert downloaded == content

    @pytest.mark.asyncio
    async def test_content_type_stored(self, storage: LocalStorageBackend):
        key = "test/book.epub"

        await storage.upload(key, b"epub content", "application/epub+zip")

        content_type = await storage.get_content_type(key)
        assert content_type == "application/epub+zip"

    @pytest.mark.asyncio
    async def test_content_type_default(self, storage: LocalStorageBackend):
        """Test that content type defaults based on extension."""
        # Create file directly without metadata
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = LocalStorageBackend(temp_dir)
            full_path = Path(temp_dir) / "test.epub"
            full_path.write_bytes(b"content")

            content_type = await backend.get_content_type("test.epub")
            assert content_type == "application/epub+zip"


class TestFileKeyGeneration:
    def test_generate_file_key_format(self):
        from uuid import uuid4

        author_id = uuid4()
        key = generate_file_key(author_id, "mybook.epub", "manuscripts")

        assert key.startswith("manuscripts/")
        assert str(author_id) in key
        assert "mybook.epub" in key

    def test_generate_file_key_sanitizes_filename(self):
        from uuid import uuid4

        author_id = uuid4()
        key = generate_file_key(author_id, "my book (1).epub", "manuscripts")

        # Spaces and parentheses should be removed
        assert " " not in key
        assert "(" not in key
        assert ")" not in key

    def test_generate_file_key_unique(self):
        from uuid import uuid4

        author_id = uuid4()

        key1 = generate_file_key(author_id, "book.epub", "manuscripts")
        key2 = generate_file_key(author_id, "book.epub", "manuscripts")

        # Keys should be unique even for same input
        assert key1 != key2


class TestContentTypeMapping:
    def test_epub_content_type(self):
        assert get_content_type_for_format("epub") == "application/epub+zip"

    def test_pdf_content_type(self):
        assert get_content_type_for_format("pdf") == "application/pdf"

    def test_docx_content_type(self):
        content_type = get_content_type_for_format("docx")
        assert "word" in content_type.lower() or "document" in content_type.lower()

    def test_odt_content_type(self):
        content_type = get_content_type_for_format("odt")
        assert "opendocument" in content_type.lower()

    def test_unknown_format_default(self):
        assert get_content_type_for_format("xyz") == "application/octet-stream"
