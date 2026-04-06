from enum import Enum


class ManuscriptState(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


class SourceFormat(str, Enum):
    EPUB = "epub"
    PDF = "pdf"
    DOCX = "docx"
    ODT = "odt"


class OutputFormat(str, Enum):
    EPUB = "epub"
    PDF = "pdf"


class Visibility(str, Enum):
    PRIVATE = "private"         # Only author can see
    UNLISTED = "unlisted"       # Accessible via direct link, not in store
    PUBLISHED = "published"     # Visible in store
