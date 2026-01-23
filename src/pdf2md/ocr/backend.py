from __future__ import annotations

import os

from pdf2md.ocr.base import OcrBackend


def get_backend_name() -> str:
    """Return the configured backend name."""
    backend = os.getenv("PDF2MD_BACKEND", "endpoint").strip().lower()
    return backend or "endpoint"


def _create_endpoint_backend() -> OcrBackend:
    from pdf2md.ocr.hf_endpoint import HfEndpointBackend

    return HfEndpointBackend()


def _create_local_backend() -> OcrBackend:
    from pdf2md.ocr.local import LocalBackend

    return LocalBackend()


def get_ocr_backend() -> OcrBackend:
    """Construct the OCR backend based on environment configuration."""
    backend = get_backend_name()
    if backend == "endpoint":
        return _create_endpoint_backend()
    if backend == "local":
        return _create_local_backend()
    raise ValueError(f"Unsupported PDF2MD_BACKEND '{backend}'. Expected 'endpoint' or 'local'.")
