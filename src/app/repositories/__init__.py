from .protocols import (
    AuthorRepository,
    DownloadRepository,
    EbookRepository,
    GenreRepository,
    ManuscriptRepository,
    SampleRepository,
)
from .sqlalchemy import (
    SQLAlchemyAuthorRepository,
    SQLAlchemyDownloadRepository,
    SQLAlchemyEbookRepository,
    SQLAlchemyGenreRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
)

__all__ = [
    # Protocols
    "AuthorRepository",
    "DownloadRepository",
    "EbookRepository",
    "GenreRepository",
    "ManuscriptRepository",
    "SampleRepository",
    # SQLAlchemy implementations
    "SQLAlchemyAuthorRepository",
    "SQLAlchemyDownloadRepository",
    "SQLAlchemyEbookRepository",
    "SQLAlchemyGenreRepository",
    "SQLAlchemyManuscriptRepository",
    "SQLAlchemySampleRepository",
]
