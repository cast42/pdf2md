from __future__ import annotations

from pdf2md.ocr.backend import get_backend_name, get_ocr_backend
from pdf2md.ocr.base import OcrBackend

__all__ = ["OcrBackend", "get_backend_name", "get_ocr_backend"]
