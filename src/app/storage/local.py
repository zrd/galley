"""
Local filesystem storage backend for development and testing.

This implementation stores files on the local filesystem, mimicking
the interface of cloud storage services like S3.
"""

from pathlib import Path

import aiofiles
import aiofiles.os

from .protocol import UnsafeStorageKey


class LocalStorageBackend:
    """Local filesystem storage backend."""

    def __init__(self, base_path: str | Path) -> None:
        """
        Initialize the local storage backend.

        Args:
            base_path: The base directory for storing files
        """
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        self.base_path = base_path.resolve()

    def _get_full_path(self, key: str) -> Path:
        """Get the full filesystem path for a storage key."""
        # Normalize the key to prevent directory traversal
        trial_key = (self.base_path / key).resolve()
        try:
            _ = trial_key.relative_to(self.base_path)
            return trial_key
        except ValueError:
            raise UnsafeStorageKey(key)

    async def upload(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload a file to local storage."""
        full_path = self._get_full_path(key)

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)

        # Store content type in a sidecar file (useful for serving)
        meta_path = full_path.with_suffix(full_path.suffix + ".meta")
        async with aiofiles.open(meta_path, "w") as f:
            await f.write(content_type)

        return key

    async def download(self, key: str) -> bytes:
        """Download a file from local storage."""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, key: str) -> None:
        """Delete a file from local storage."""
        full_path = self._get_full_path(key)

        if full_path.exists():
            await aiofiles.os.remove(full_path)

        # Also remove metadata file if it exists
        meta_path = full_path.with_suffix(full_path.suffix + ".meta")
        if meta_path.exists():
            await aiofiles.os.remove(meta_path)

    async def exists(self, key: str) -> bool:
        """Check if a file exists in local storage."""
        full_path = self._get_full_path(key)
        return full_path.exists()

    async def get_size(self, key: str) -> int:
        """Get the size of a file in bytes."""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        stat = await aiofiles.os.stat(full_path)
        return stat.st_size

    async def get_content_type(self, key: str) -> str:
        """Get the content type of a stored file."""
        full_path = self._get_full_path(key)
        meta_path = full_path.with_suffix(full_path.suffix + ".meta")

        if meta_path.exists():
            async with aiofiles.open(meta_path) as f:
                return await f.read()

        # Default content type based on extension
        ext = full_path.suffix.lower()
        content_types = {
            ".epub": "application/epub+zip",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".odt": "application/vnd.oasis.opendocument.text",
            ".jpg": "image/jpeg",
            ".png": "image/png",
        }
        return content_types.get(ext, "application/octet-stream")

    async def get_url(self, key: str) -> str:
        local_path = self._get_full_path(key)
        if local_path.exists():
            return str(local_path)
        else:
            raise FileNotFoundError(key)
