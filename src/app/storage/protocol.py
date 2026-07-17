from typing import Protocol


class UnsafeStorageKey(ValueError):
    """A storage key/filename would escape the storage root."""


class StorageBackend(Protocol):
    """Protocol for file storage backends (local filesystem, S3, etc.)."""

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Upload a file to storage.

        Args:
            key: The storage key/path for the file
            data: The file contents as bytes
            content_type: MIME type of the file

        Returns:
            The storage key where the file was stored
        """
        ...

    async def download(self, key: str) -> bytes:
        """
        Download a file from storage.

        Args:
            key: The storage key/path for the file

        Returns:
            The file contents as bytes

        Raises:
            FileNotFoundError: If the file does not exist
        """
        ...

    async def delete(self, key: str) -> None:
        """
        Delete a file from storage.

        Args:
            key: The storage key/path for the file
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            key: The storage key/path for the file

        Returns:
            True if the file exists, False otherwise
        """
        ...

    async def get_size(self, key: str) -> int:
        """
        Get the size of a file in bytes.

        Args:
            key: The storage key/path for the file

        Returns:
            The file size in bytes

        Raises:
            FileNotFoundError: If the file does not exist
        """
        ...

    async def get_url(self, key: str) -> str:
        """
        Get the URL for a filesystem asset.

        Args:
            key: The storage key/path for the file

        Returns:
            The URL where the HTTP server can find the asset

        Raises:
            FileNotFoundError: If the file does not exist
        """
        ...
