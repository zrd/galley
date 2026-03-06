import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import ManuscriptState, OutputFormat, SourceFormat

from .base import Base


class AuthorModel(Base):
    __tablename__ = "authors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )

    # Relationships
    manuscripts: Mapped[list["ManuscriptModel"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


class ManuscriptModel(Base):
    __tablename__ = "manuscripts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("authors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_format: Mapped[SourceFormat] = mapped_column(
        Enum(SourceFormat, name="source_format", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    source_file_key: Mapped[str] = mapped_column(String(512), nullable=False)
    state: Mapped[ManuscriptState] = mapped_column(
        Enum(ManuscriptState, name="manuscript_state", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ManuscriptState.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )

    # Relationships
    author: Mapped["AuthorModel"] = relationship(back_populates="manuscripts")
    genres: Mapped[list["GenreModel"]] = relationship(
        secondary="manuscript_genres",
        back_populates="manuscripts"
    )
    samples: Mapped[list["SampleModel"]] = relationship(
        back_populates="manuscript", cascade="all, delete-orphan"
    )
    ebooks: Mapped[list["EbookModel"]] = relationship(
        back_populates="manuscript", cascade="all, delete-orphan"
    )


class SampleModel(Base):
    __tablename__ = "samples"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("manuscripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    excerpt_start: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt_end: Mapped[str] = mapped_column(String(255), nullable=False)
    promo_header: Mapped[str | None] = mapped_column(Text, nullable=True)
    promo_footer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )

    # Relationships
    manuscript: Mapped["ManuscriptModel"] = relationship(back_populates="samples")
    ebooks: Mapped[list["EbookModel"]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )


class EbookModel(Base):
    __tablename__ = "ebooks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("manuscripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sample_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    output_format: Mapped[OutputFormat] = mapped_column(
        Enum(OutputFormat, name="output_format", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    file_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    download_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    download_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )

    # Relationships
    manuscript: Mapped["ManuscriptModel"] = relationship(back_populates="ebooks")
    sample: Mapped["SampleModel | None"] = relationship(back_populates="ebooks")
    downloads: Mapped[list["DownloadModel"]] = relationship(
        back_populates="ebook", cascade="all, delete-orphan"
    )


class DownloadModel(Base):
    __tablename__ = "downloads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ebook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tracking_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    ebook: Mapped["EbookModel"] = relationship(back_populates="downloads")


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("genres.id"), nullable=True)

    # Relationships
    parent: Mapped["GenreModel | None"] = relationship(
        "GenreModel", back_populates="children", remote_side="GenreModel.id"
    )
    children: Mapped[list["GenreModel"]] = relationship("GenreModel", back_populates="parent")
    manuscripts: Mapped[list["ManuscriptModel"]] = relationship(
        secondary="manuscript_genres",
        back_populates="genres"
    )


class ManuscriptGenreModel(Base):
    __tablename__ = "manuscript_genres"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("manuscripts.id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True
    )
