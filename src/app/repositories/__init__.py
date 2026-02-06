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
    # SQLAlchemy implementations
    "SQLAlchemyAuthorRepository",
    "SQLAlchemyDownloadRepository",
    "SQLAlchemyEbookRepository",
    "SQLAlchemyManuscriptRepository",
    "SQLAlchemySampleRepository",
]
