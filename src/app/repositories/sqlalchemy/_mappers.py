from app.db.models import (
    AuthorModel,
    DownloadModel,
    EbookModel,
    GenreModel,
    ManuscriptModel,
    SampleModel,
    TagModel,
)
from app.domain import Author, Download, Ebook, Genre, Manuscript, Sample, Tag


def author_model_to_domain(model: AuthorModel) -> Author:
    return Author(
        id=model.id,
        email=model.email,
        display_name=model.display_name,
        bio=model.bio,
        website=model.website,
        avatar_key=model.avatar_key,
        is_public=model.is_public,
        password_hash=model.password_hash,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )


def manuscript_model_to_domain(model: ManuscriptModel) -> Manuscript:
    return Manuscript(
        id=model.id,
        author_id=model.author_id,
        title=model.title,
        description=model.description,
        genres=[genre_model_to_domain(g) for g in model.genres],
        tags=[tag_model_to_domain(t) for t in model.tags],
        source_format=model.source_format,
        source_file_key=model.source_file_key,
        cover_image_key=model.cover_image_key,
        state=model.state,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def sample_model_to_domain(model: SampleModel) -> Sample:
    return Sample(
        id=model.id,
        manuscript_id=model.manuscript_id,
        title=model.title,
        excerpt_start=model.excerpt_start,
        excerpt_end=model.excerpt_end,
        promo_header=model.promo_header,
        promo_footer=model.promo_footer,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def ebook_model_to_domain(model: EbookModel) -> Ebook:
    return Ebook(
        id=model.id,
        manuscript_id=model.manuscript_id,
        sample_id=model.sample_id,
        output_format=model.output_format,
        list_price_cents=model.list_price_cents,
        sale_price_cents=model.sale_price_cents,
        price_currency=model.price_currency,
        file_key=model.file_key,
        file_size_bytes=model.file_size_bytes,
        download_filename=model.download_filename,
        download_count=model.download_count,
        visibility=model.visibility,
        unlisted_download_limit=model.unlisted_download_limit,
        created_at=model.created_at,
        published_at=model.published_at,
        deleted_at=model.deleted_at,
    )


def download_model_to_domain(model: DownloadModel) -> Download:
    return Download(
        id=model.id,
        ebook_id=model.ebook_id,
        downloaded_at=model.downloaded_at,
        ip_hash=model.ip_hash,
        tracking_code=model.tracking_code,
        deleted_at=model.deleted_at,
    )


def genre_model_to_domain(model: GenreModel) -> Genre:
    return Genre(
        id=model.id,
        name=model.name,
        slug=model.slug,
        description=model.description,
        parent_id=model.parent_id,
    )


def tag_model_to_domain(model: TagModel) -> Tag:
    return Tag(
        id=model.id,
        name=model.name,
        slug=model.slug,
        owner_id=model.owner_id,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )
