from __future__ import annotations

from typing import Protocol


class OcrBackend(Protocol):
    """Backend protocol for OCR inference."""

    def ocr_page(self, image_bytes: bytes, *, page_index: int) -> str:
        """Run OCR for a single page image and return markdown/text."""
        raise NotImplementedError
