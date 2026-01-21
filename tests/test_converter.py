"""Tests for the pdf2md converter module."""

from pathlib import Path
from unittest.mock import patch

import torch

from pdf2md.converter import convert_pdf_to_markdown, get_device_and_dtype


class TestConversion:
    """Integration tests for PDF conversion."""

    def test_convert_simple_pdf(self, tmp_path):
        """Should convert a simple PDF to Markdown correctly."""
        # Locate the test data relative to the project root
        pdf_path = Path("tests/data/test.pdf")
        if not pdf_path.exists():
            # If running from inside tests/ or similar, try to adjust or skip
            # But usually tests are run from root.
            # Fallback for some IDEs: look relative to this file
            pdf_path = Path(__file__).parent / "data" / "test.pdf"

        assert pdf_path.exists(), f"Test artifact not found at {pdf_path}"

        output_path = tmp_path / "test.md"

        # Run conversion
        markdown = convert_pdf_to_markdown(pdf_path, output_path)

        # Verify output file exists
        assert output_path.exists()

        # Verify content
        expected_snippets = ["Hello World!", "test PDF"]
        for snippet in expected_snippets:
            assert snippet in markdown, f"Expected '{snippet}' in output markdown"

        # Verify file content matches returned string
        assert output_path.read_text(encoding="utf-8") == markdown


class TestGetDeviceAndDtype:
    """Tests for device and dtype selection."""

    def test_returns_tuple(self):
        """Should return a tuple of (device, dtype)."""
        result = get_device_and_dtype()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_device_is_string(self):
        """Device should be a string."""
        device, _ = get_device_and_dtype()
        assert isinstance(device, str)
        assert device in ("cuda", "mps", "cpu")

    def test_dtype_is_torch_dtype(self):
        """Dtype should be a torch dtype."""
        _, dtype = get_device_and_dtype()
        assert dtype in (torch.bfloat16, torch.float32)

    @patch("torch.cuda.is_available", return_value=True)
    def test_cuda_when_available(self, mock_cuda):
        """Should use CUDA when available."""
        device, dtype = get_device_and_dtype()
        assert device == "cuda"
        assert dtype == torch.bfloat16

    @patch("torch.cuda.is_available", return_value=False)
    @patch("torch.backends.mps.is_available", return_value=True)
    def test_mps_when_cuda_unavailable(self, mock_mps, mock_cuda):
        """Should use MPS when CUDA unavailable but MPS available."""
        device, dtype = get_device_and_dtype()
        assert device == "mps"
        assert dtype == torch.float32

    @patch("torch.cuda.is_available", return_value=False)
    @patch("torch.backends.mps.is_available", return_value=False)
    def test_cpu_fallback(self, mock_mps, mock_cuda):
        """Should fall back to CPU when no GPU available, using bfloat16 for memory efficiency."""
        device, dtype = get_device_and_dtype()
        assert device == "cpu"
        assert dtype == torch.bfloat16
