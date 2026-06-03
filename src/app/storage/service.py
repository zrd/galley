"""
Storage service that provides access to the configured storage backend.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from app.config import settings

from .local import LocalStorageBackend
from .protocol import StorageBackend


@lru_cache
def get_storage_backend() -> StorageBackend:
    """
    Get the configured storage backend.

    Returns the appropriate storage backend based on STORAGE_BACKEND setting.
    Currently supports:
    - "local": LocalStorageBackend (filesystem-based)
    - "s3": S3StorageBackend (AWS S3) - not yet implemented

    Returns:
        The configured storage backend instance
    """
    if settings.STORAGE_BACKEND == "local":
        return LocalStorageBackend(settings.LOCAL_STORAGE_PATH)
    elif settings.STORAGE_BACKEND == "s3":
        raise NotImplementedError("S3 storage backend not yet implemented")
    else:
        raise ValueError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")


def generate_file_key(
    author_id: uuid.UUID,
    filename: str,
    file_type: str = "manuscripts",
) -> str:
    """
    Generate a unique storage key for a file.

    The key format is: {file_type}/{author_id}/{timestamp}_{hash}_{filename}

    Args:
        author_id: The author's UUID
        filename: The original filename
        file_type: The type of file (manuscripts, ebooks, etc.)

    Returns:
        A unique storage key
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_hash = hashlib.sha256(
        f"{author_id}{timestamp}{uuid.uuid4()}".encode()
    ).hexdigest()[:12]

    # Sanitize filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")

    return f"{file_type}/{author_id}/{timestamp}_{unique_hash}_{safe_filename}"


def get_content_type_for_format(format_str: str) -> str:
    """
    Get the MIME content type for a file format.

    Args:
        format_str: The format string (e.g., "epub", "pdf")

    Returns:
        The MIME content type
    """
    content_types = {
        "epub": "application/epub+zip",
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "odt": "application/vnd.oasis.opendocument.text",
        "jpg": "image/jpeg",
        "png": "image/png",
    }
    return content_types.get(format_str.lower(), "application/octet-stream")


def validate_image(content: bytes, size_limit_mb: float = 5) -> str:
    """
    Validate an image by type (JPEG, PNG) and size

    Args:
        content: The image data
        size_limit_mb: The maximum allowed image size, in MB

    Returns:
        The MIME content type
    """
    if len(content) > size_limit_mb * 1024 * 1024:
        raise ValueError(f"Image content size limit exceeded ({size_limit_mb:g} MB)")

    if content[:3] == b"\xff\xd8\xff":
        content_type = "image/jpeg"
    elif content[:8] == b"\x89PNG\r\n\x1a\n":
        content_type = "image/png"
    else:
        raise ValueError("Image content type not in (JPEG, PNG)")

    return content_type
