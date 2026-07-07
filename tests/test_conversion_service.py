"""
Tests for ConversionService.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain import OutputFormat, SourceFormat
from app.services.conversion_service import ConversionError, ConversionService

RESOURCES = Path(__file__).parent / "resources"


def run(coro):
    return asyncio.run(coro)


class TestConversionServiceOdtToEpub:
    def test_valid_odt_produces_epub(self):
        source_data = (RESOURCES / "valid_odt.odt").read_bytes()
        service = ConversionService()
        result = run(service.convert(source_data, SourceFormat.ODT, OutputFormat.EPUB, title="Test"))
        assert len(result) >= ConversionService.MIN_OUTPUT_BYTES
        # EPUB files are ZIP archives starting with PK
        assert result[:2] == b"PK"

    def test_same_format_passthrough(self):
        source_data = (RESOURCES / "valid_odt.odt").read_bytes()
        service = ConversionService()
        result = run(service.convert(source_data, SourceFormat.EPUB, OutputFormat.EPUB))
        assert result == source_data


class TestConversionServiceSizeCheck:
    def test_raises_on_suspiciously_small_output(self):
        service = ConversionService()
        tiny_output = b"x" * 100

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_bytes", return_value=tiny_output):
                    with pytest.raises(ConversionError, match="minimum size"):
                        run(service.convert(b"data", SourceFormat.ODT, OutputFormat.EPUB))

    def test_accepts_output_at_minimum_size(self):
        service = ConversionService()
        min_output = b"x" * ConversionService.MIN_OUTPUT_BYTES

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_bytes", return_value=min_output):
                    result = run(service.convert(b"data", SourceFormat.ODT, OutputFormat.EPUB))
                    assert result == min_output


class TestConversionServiceStderr:
    def test_logs_stderr_on_success(self, caplog):
        import logging
        service = ConversionService()
        warning = b"[WARNING] some pandoc warning"
        valid_output = b"x" * ConversionService.MIN_OUTPUT_BYTES

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", warning))

        with caplog.at_level(logging.WARNING):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch.object(Path, "exists", return_value=True):
                    with patch.object(Path, "read_bytes", return_value=valid_output):
                        run(service.convert(b"data", SourceFormat.ODT, OutputFormat.EPUB))

        assert "some pandoc warning" in caplog.text

    def test_no_stderr_output_when_clean(self, caplog):
        import logging
        service = ConversionService()
        valid_output = b"x" * ConversionService.MIN_OUTPUT_BYTES

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with caplog.at_level(logging.WARNING):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch.object(Path, "exists", return_value=True):
                    with patch.object(Path, "read_bytes", return_value=valid_output):
                        run(service.convert(b"data", SourceFormat.ODT, OutputFormat.EPUB))

        assert caplog.text == ""

    def test_raises_on_nonzero_returncode(self):
        service = ConversionService()

        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"error from pandoc"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with pytest.raises(ConversionError, match="Pandoc conversion failed"):
                run(service.convert(b"data", SourceFormat.ODT, OutputFormat.EPUB))
