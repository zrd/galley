"""
Ebook generation service.

Handles generating ebooks from manuscripts, including:
- Full ebook generation
- Sample ebook generation with excerpts and promotional content
"""

from uuid import UUID

from app.domain import Ebook, Manuscript, OutputFormat, Sample
from app.repositories import InMemoryEbookRepository
from app.storage import generate_file_key, get_content_type_for_format, get_storage_backend

from .conversion_service import ConversionService, get_conversion_service


class GenerationError(Exception):
    """Raised when ebook generation fails."""

    pass


class GenerationService:
    """
    Service for generating ebooks from manuscripts.
    """

    def __init__(
        self,
        ebook_repo: InMemoryEbookRepository,
        conversion_service: ConversionService | None = None,
    ) -> None:
        self.ebook_repo = ebook_repo
        self.conversion_service = conversion_service or get_conversion_service()

    async def generate_full_ebook(
        self,
        manuscript: Manuscript,
        output_format: OutputFormat,
    ) -> Ebook:
        """
        Generate a full ebook from a manuscript.

        Args:
            manuscript: The manuscript to generate from
            output_format: The desired output format

        Returns:
            The generated Ebook entity

        Raises:
            GenerationError: If generation fails
        """
        if not manuscript.can_generate_ebook():
            raise GenerationError(
                f"Manuscript must be in READY state to generate ebook (current: {manuscript.state.value})"
            )

        # Download source file
        storage = get_storage_backend()
        source_data = await storage.download(manuscript.source_file_key)

        # Convert to output format
        output_data = await self.conversion_service.convert(
            source_data=source_data,
            source_format=manuscript.source_format,
            output_format=output_format,
            title=manuscript.title,
        )

        # Upload generated ebook
        file_key = generate_file_key(
            manuscript.author_id,
            f"{manuscript.title}.{output_format.value}",
            "ebooks",
        )
        content_type = get_content_type_for_format(output_format.value)
        await storage.upload(file_key, output_data, content_type)

        # Create ebook record
        ebook = Ebook(
            manuscript_id=manuscript.id,
            output_format=output_format,
            file_key=file_key,
            file_size_bytes=len(output_data),
            sample_id=None,
        )

        return self.ebook_repo.add(ebook)

    async def generate_sample_ebook(
        self,
        manuscript: Manuscript,
        sample: Sample,
        output_format: OutputFormat,
    ) -> Ebook:
        """
        Generate a sample ebook from a manuscript and sample definition.

        This is a simplified implementation that:
        1. Downloads the source manuscript
        2. Converts to output format
        3. Adds promo header/footer (where supported)

        Note: Full excerpt extraction based on start/end markers requires
        format-specific parsing which will be implemented in a future version.
        For now, this generates the full book with promo content.

        Args:
            manuscript: The source manuscript
            sample: The sample definition
            output_format: The desired output format

        Returns:
            The generated sample Ebook entity

        Raises:
            GenerationError: If generation fails
        """
        if not manuscript.can_generate_ebook():
            raise GenerationError(
                f"Manuscript must be in READY state to generate sample (current: {manuscript.state.value})"
            )

        # Download source file
        storage = get_storage_backend()
        source_data = await storage.download(manuscript.source_file_key)

        # TODO: Implement actual excerpt extraction based on sample.excerpt_start/end
        # For now, we convert the full document and note this limitation

        # Convert to output format
        output_data = await self.conversion_service.convert(
            source_data=source_data,
            source_format=manuscript.source_format,
            output_format=output_format,
            title=f"{manuscript.title} - {sample.title}",
        )

        # TODO: Inject promo_header and promo_footer into the output
        # This requires format-specific manipulation (e.g., modifying EPUB XML)

        # Upload generated sample ebook
        file_key = generate_file_key(
            manuscript.author_id,
            f"{manuscript.title}_sample_{sample.title}.{output_format.value}",
            "samples",
        )
        content_type = get_content_type_for_format(output_format.value)
        await storage.upload(file_key, output_data, content_type)

        # Create ebook record
        ebook = Ebook(
            manuscript_id=manuscript.id,
            output_format=output_format,
            file_key=file_key,
            file_size_bytes=len(output_data),
            sample_id=sample.id,
        )

        return self.ebook_repo.add(ebook)
