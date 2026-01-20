"""Tests for the pdf2md CLI module."""

import sys
from unittest.mock import patch

from pdf2md.cli import main


class TestCLI:
    """Tests for the command-line interface."""

    def test_missing_file_returns_error(self, tmp_path):
        """Should return error code 1 for non-existent file."""
        non_existent = tmp_path / "does_not_exist.pdf"
        with patch.object(sys, "argv", ["pdf2md", str(non_existent)]):
            result = main()
        assert result == 1

    def test_non_pdf_file_returns_error(self, tmp_path):
        """Should return error code 1 for non-PDF file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")
        with patch.object(sys, "argv", ["pdf2md", str(txt_file)]):
            result = main()
        assert result == 1

    def test_valid_pdf_calls_converter(self, tmp_path):
        """Should call converter for valid PDF file."""
        pdf_file = tmp_path / "test.pdf"
        # Create a minimal "PDF" file (just for testing file existence check)
        pdf_file.write_bytes(b"%PDF-1.4")

        with (
            patch.object(sys, "argv", ["pdf2md", str(pdf_file)]),
            patch("pdf2md.cli.convert_pdf_to_markdown") as mock_convert,
        ):
            mock_convert.return_value = "# Test"
            result = main()

        assert result == 0
        mock_convert.assert_called_once_with(pdf_file, None)

    def test_output_option(self, tmp_path):
        """Should pass output path to converter."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        output_file = tmp_path / "output.md"

        with (
            patch.object(sys, "argv", ["pdf2md", str(pdf_file), "-o", str(output_file)]),
            patch("pdf2md.cli.convert_pdf_to_markdown") as mock_convert,
        ):
            mock_convert.return_value = "# Test"
            result = main()

        assert result == 0
        mock_convert.assert_called_once_with(pdf_file, output_file)
