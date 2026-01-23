"""Tests for the pdf2md converter module."""

from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pdf2md.converter import convert_pdf_to_markdown


class DummyBackend:
    def __init__(self, results: list[str]) -> None:
        self.results = results
        self.calls: list[int] = []

    def ocr_page(self, image_bytes: bytes, *, page_index: int) -> str:
        self.calls.append(page_index)
        return self.results[page_index]


class TestConversion:
    """Integration tests for PDF conversion."""

    def test_convert_simple_pdf(self, tmp_path):
        """Should convert a simple PDF to Markdown correctly."""
        pdf_path = Path("tests/data/test.pdf")
        if not pdf_path.exists():
            pdf_path = Path(__file__).parent / "data" / "test.pdf"

        assert pdf_path.exists(), f"Test artifact not found at {pdf_path}"

        output_path = tmp_path / "test.md"
        images = [Image.new("RGB", (2, 2), color="white"), Image.new("RGB", (2, 2), color="black")]
        backend = DummyBackend(["Hello World!", "test PDF"])

        with (
            patch("pdf2md.converter.get_ocr_backend", return_value=backend),
            patch("pdf2md.converter.get_backend_name", return_value="endpoint"),
            patch("pdf2md.converter.pdf_to_images", return_value=images),
        ):
            markdown = convert_pdf_to_markdown(pdf_path, output_path)

        assert output_path.exists()
        expected_snippets = ["Hello World!", "test PDF"]
        for snippet in expected_snippets:
            assert snippet in markdown, f"Expected '{snippet}' in output markdown"

        assert output_path.read_text(encoding="utf-8") == markdown
        assert backend.calls == [0, 1]
