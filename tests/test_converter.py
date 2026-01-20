"""Tests for the pdf2md converter module."""

from unittest.mock import patch

import torch

from pdf2md.converter import get_device_and_dtype


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
        """Should fall back to CPU when no GPU available."""
        device, dtype = get_device_and_dtype()
        assert device == "cpu"
        assert dtype == torch.float32
