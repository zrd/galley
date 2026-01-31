"""
Document conversion service using Pandoc.

Provides format conversion between supported document formats:
- EPUB
- PDF
- DOCX
- ODT
"""

import asyncio
import tempfile
from pathlib import Path

from app.domain import OutputFormat, SourceFormat


class ConversionError(Exception):
    """Raised when document conversion fails."""

    pass


class ConversionService:
    """
    Service for converting documents between formats using Pandoc.

    Pandoc must be installed on the system for this service to work.
    """

    # Mapping of source formats to Pandoc input format names
    INPUT_FORMATS = {
        SourceFormat.EPUB: "epub",
        SourceFormat.PDF: "pdf",
        SourceFormat.DOCX: "docx",
        SourceFormat.ODT: "odt",
    }

    # Mapping of output formats to Pandoc output format names
    OUTPUT_FORMATS = {
        OutputFormat.EPUB: "epub",
        OutputFormat.PDF: "pdf",
    }

    # File extensions for each format
    EXTENSIONS = {
        SourceFormat.EPUB: ".epub",
        SourceFormat.PDF: ".pdf",
        SourceFormat.DOCX: ".docx",
        SourceFormat.ODT: ".odt",
        OutputFormat.EPUB: ".epub",
        OutputFormat.PDF: ".pdf",
    }

    async def convert(
        self,
        source_data: bytes,
        source_format: SourceFormat,
        output_format: OutputFormat,
        title: str | None = None,
    ) -> bytes:
        """
        Convert a document from one format to another.

        Args:
            source_data: The source document as bytes
            source_format: The format of the source document
            output_format: The desired output format
            title: Optional title for the output document

        Returns:
            The converted document as bytes

        Raises:
            ConversionError: If conversion fails
        """
        # If formats are the same, return as-is
        if source_format.value == output_format.value:
            return source_data

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write source file
            source_ext = self.EXTENSIONS[source_format]
            source_file = temp_path / f"source{source_ext}"
            source_file.write_bytes(source_data)

            # Prepare output file
            output_ext = self.EXTENSIONS[output_format]
            output_file = temp_path / f"output{output_ext}"

            # Build pandoc command
            cmd = [
                "pandoc",
                str(source_file),
                "-o",
                str(output_file),
            ]

            # Add title metadata if provided
            if title:
                cmd.extend(["--metadata", f"title={title}"])

            # Add format-specific options
            if output_format == OutputFormat.PDF:
                # Use a PDF engine that's commonly available
                cmd.extend(["--pdf-engine=xelatex"])
            elif output_format == OutputFormat.EPUB:
                # EPUB-specific options
                cmd.extend(["--epub-chapter-level=1"])

            # Run pandoc
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode("utf-8", errors="replace")
                    raise ConversionError(f"Pandoc conversion failed: {error_msg}")

            except FileNotFoundError:
                raise ConversionError(
                    "Pandoc is not installed. Please install Pandoc to enable format conversion."
                )

            # Read output file
            if not output_file.exists():
                raise ConversionError("Conversion produced no output file")

            return output_file.read_bytes()

    async def check_pandoc_available(self) -> bool:
        """Check if Pandoc is installed and available."""
        try:
            process = await asyncio.create_subprocess_exec(
                "pandoc",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except FileNotFoundError:
            return False


# Singleton instance
_conversion_service: ConversionService | None = None


def get_conversion_service() -> ConversionService:
    """Get the singleton ConversionService instance."""
    global _conversion_service
    if _conversion_service is None:
        _conversion_service = ConversionService()
    return _conversion_service
