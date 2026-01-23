"""Tests for OCR backend selection and endpoint usage."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pdf2md.converter import convert_pdf_to_markdown
from pdf2md.ocr import backend as backend_module
from pdf2md.ocr import hf_endpoint


def test_backend_name_defaults_to_endpoint(monkeypatch):
    monkeypatch.delenv("PDF2MD_BACKEND", raising=False)
    assert backend_module.get_backend_name() == "endpoint"


def test_backend_selection_uses_env(monkeypatch):
    monkeypatch.setenv("PDF2MD_BACKEND", "local")
    sentinel = object()
    monkeypatch.setattr(backend_module, "_create_local_backend", lambda: sentinel)
    assert backend_module.get_ocr_backend() is sentinel


def test_endpoint_backend_builds_client_with_base_url(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "test-token")
    monkeypatch.setenv("HF_ENDPOINT_URL", "https://example.com")
    monkeypatch.delenv("HF_MODEL_ID", raising=False)

    captured: dict[str, object] = {}

    class DummyClient:
        def __init__(self, *, base_url=None, model=None, token=None, timeout=None):
            captured["base_url"] = base_url
            captured["model"] = model
            captured["token"] = token
            captured["timeout"] = timeout

        def image_to_text(self, image):
            return type("Result", (), {"generated_text": "ok"})()

    monkeypatch.setattr(hf_endpoint, "InferenceClient", DummyClient)

    backend = hf_endpoint.HfEndpointBackend()
    assert backend.ocr_page(b"image-bytes", page_index=0) == "ok"
    assert captured["base_url"] == "https://example.com"
    assert captured["model"] is None
    assert captured["token"] == "test-token"


@pytest.mark.integration
def test_endpoint_integration(tmp_path, monkeypatch):
    token = os.getenv("HF_TOKEN")
    endpoint_url = os.getenv("HF_ENDPOINT_URL")
    model_id = os.getenv("HF_MODEL_ID")
    if not token or not (endpoint_url or model_id):
        pytest.skip("HF_TOKEN + HF_ENDPOINT_URL/HF_MODEL_ID required for integration test.")

    monkeypatch.setenv("PDF2MD_BACKEND", "endpoint")

    pdf_path = Path("tests/data/test.pdf")
    if not pdf_path.exists():
        pdf_path = Path(__file__).parent / "data" / "test.pdf"

    output_path = tmp_path / "endpoint.md"
    markdown = convert_pdf_to_markdown(pdf_path, output_path)

    assert output_path.exists()
    assert markdown.strip()
