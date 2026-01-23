from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError

from pdf2md.ocr.base import OcrBackend

TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class EndpointConfig:
    endpoint_url: str | None
    model_id: str | None
    token: str
    timeout_s: float
    retries: int


def _get_timeout() -> float:
    raw = os.getenv("HF_TIMEOUT_S", "120")
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid HF_TIMEOUT_S value: {raw!r}") from exc


def _get_retries() -> int:
    raw = os.getenv("HF_RETRIES", "4")
    try:
        retries = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid HF_RETRIES value: {raw!r}") from exc
    if retries < 0:
        raise RuntimeError("HF_RETRIES must be >= 0")
    return retries


def _load_config() -> EndpointConfig:
    endpoint_url = os.getenv("HF_ENDPOINT_URL")
    model_id = os.getenv("HF_MODEL_ID")
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is required for endpoint OCR.")
    if not endpoint_url and not model_id:
        raise RuntimeError("Set HF_ENDPOINT_URL or HF_MODEL_ID to use the endpoint backend.")
    return EndpointConfig(
        endpoint_url=endpoint_url,
        model_id=model_id,
        token=token,
        timeout_s=_get_timeout(),
        retries=_get_retries(),
    )


def _extract_generated_text(result: Any) -> str:
    if isinstance(result, list):
        if not result:
            return ""
        result = result[0]
    if isinstance(result, dict):
        return str(result.get("generated_text") or result.get("text") or result.get("caption") or "")
    for attr in ("generated_text", "image_to_text_output_generated_text", "text", "caption"):
        value = getattr(result, attr, None)
        if value:
            return str(value)
    return str(result) if result is not None else ""


def _status_code_from_error(exc: Exception) -> int | None:
    if isinstance(exc, HfHubHTTPError) and exc.response is not None:
        return exc.response.status_code
    response = getattr(exc, "response", None)
    if response is not None:
        return getattr(response, "status_code", None)
    return None


def _should_retry(exc: Exception) -> bool:
    status_code = _status_code_from_error(exc)
    if status_code is not None:
        return status_code in TRANSIENT_STATUS_CODES
    return isinstance(exc, requests.exceptions.RequestException)


class HfEndpointBackend(OcrBackend):
    """OCR backend that offloads inference to a Hugging Face endpoint."""

    def __init__(self) -> None:
        config = _load_config()
        self._config = config
        if config.endpoint_url:
            self._client = InferenceClient(
                base_url=config.endpoint_url,
                token=config.token,
                timeout=config.timeout_s,
            )
        else:
            self._client = InferenceClient(
                model=config.model_id,
                provider="hf-inference",
                token=config.token,
                timeout=config.timeout_s,
            )

    def ocr_page(self, image_bytes: bytes, *, page_index: int) -> str:
        last_error: Exception | None = None
        for attempt in range(self._config.retries + 1):
            try:
                result = self._client.image_to_text(image_bytes)
                text = _extract_generated_text(result)
                if not text:
                    raise RuntimeError("Empty response from endpoint OCR.")
                return text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if isinstance(exc, StopIteration):
                    raise RuntimeError(
                        "No inference provider is available for the configured model. "
                        "Try setting HF_ENDPOINT_URL for a dedicated endpoint or choose a model "
                        "supported by the Hugging Face Inference API."
                    ) from exc
                status_code = _status_code_from_error(exc)
                if status_code == 404 and not self._config.endpoint_url:
                    raise RuntimeError(
                        "The hosted Inference API does not serve this model. "
                        "Set HF_ENDPOINT_URL for a dedicated endpoint or choose a model "
                        "with an available inference provider."
                    ) from exc
                if attempt >= self._config.retries or not _should_retry(exc):
                    status_note = f" (status {status_code})" if status_code is not None else ""
                    detail = str(exc) or repr(exc)
                    raise RuntimeError(f"Endpoint OCR failed{status_note}: {detail}") from exc
                delay = min(0.5 * (2**attempt), 8.0)
                time.sleep(delay)
        if last_error is not None:
            raise last_error
        raise RuntimeError("Endpoint OCR failed without an explicit error.")
