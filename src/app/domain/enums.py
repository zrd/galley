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
