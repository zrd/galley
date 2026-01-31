from .in_memory import (
    InMemoryAuthorRepository,
    InMemoryDownloadRepository,
    InMemoryEbookRepository,
    InMemoryManuscriptRepository,
    InMemorySampleRepository,
)
from .protocols import (
    AuthorRepository,
    DownloadRepository,
    EbookRepository,
    ManuscriptRepository,
    SampleRepository,
)
from .sqlalchemy import (
    SQLAlchemyAuthorRepository,
    SQLAlchemyDownloadRepository,
    SQLAlchemyEbookRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
)

__all__ = [
    # Protocols
    "AuthorRepository",
    "DownloadRepository",
    "EbookRepository",
    "ManuscriptRepository",
    "SampleRepository",
    # In-memory implementations
    "InMemoryAuthorRepository",
    "InMemoryDownloadRepository",
    "InMemoryEbookRepository",
    "InMemoryManuscriptRepository",
    "InMemorySampleRepository",
    # SQLAlchemy implementations
    "SQLAlchemyAuthorRepository",
    "SQLAlchemyDownloadRepository",
    "SQLAlchemyEbookRepository",
    "SQLAlchemyManuscriptRepository",
    "SQLAlchemySampleRepository",
]
