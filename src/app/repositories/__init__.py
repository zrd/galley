from .protocols import (
    AuthorRepository,
    DownloadRepository,
    EbookRepository,
    GenreRepository,
    ManuscriptRepository,
    SampleRepository,
    TagRepository,
)
from .sqlalchemy import (
    SQLAlchemyAuthorRepository,
    SQLAlchemyDownloadRepository,
    SQLAlchemyEbookRepository,
    SQLAlchemyGenreRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
    SQLAlchemyTagRepository,
    SQLAlchemyStoreRepository,
)

__all__ = [
    # Protocols
    "AuthorRepository",
    "DownloadRepository",
    "EbookRepository",
    "GenreRepository",
    "ManuscriptRepository",
    "SampleRepository",
    "TagRepository",
    # SQLAlchemy implementations
    "SQLAlchemyAuthorRepository",
    "SQLAlchemyDownloadRepository",
    "SQLAlchemyEbookRepository",
    "SQLAlchemyGenreRepository",
    "SQLAlchemyManuscriptRepository",
    "SQLAlchemySampleRepository",
    "SQLAlchemyTagRepository",
    "SQLAlchemyStoreRepository",
]
