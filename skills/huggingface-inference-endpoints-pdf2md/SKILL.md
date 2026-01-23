---
name: huggingface-inference-endpoints-pdf2md
description: Offload pdf2md OCR inference to Hugging Face Inference Endpoints (GPU) using uv.
---

# Skill: Offload pdf2md OCR inference to Hugging Face Inference Endpoints (GPU) using uv

## Repo target

This skill is for <https://github.com/cast42/pdf2md> (Python package, src layout, uv/uv.lock, justfile, CLI `uv run pdf2md ...`).  [oai_citation:1‡GitHub](https://github.com/cast42/pdf2md)

## Goal

Refactor pdf2md so the OCR model inference runs on a Hugging Face **Inference Endpoint** (GPU-backed),
instead of loading/running the model locally with torch/transformers.

The local machine should only:

- render PDF pages to images (existing behavior)
- send images to the endpoint
- receive OCR markdown/text results and write the output file

## Non-goals

- Do not change the CLI interface unless unavoidable.
- Do not introduce a new packaging system (keep uv + pyproject + uv.lock).
- Do not require local CUDA/MPS/torch for the endpoint path.

## Configuration (env vars)

Required:

- `HF_TOKEN`: Hugging Face access token (read at runtime, never logged)
- One of:
  - `HF_ENDPOINT_URL`: endpoint URL (preferred for Inference Endpoints)
  - `HF_MODEL_ID`: model id (fallback if using hosted API)

Optional:

- `PDF2MD_BACKEND`: `endpoint` (default) or `local` (for dev/backward compat)
- `HF_TIMEOUT_S`: request timeout seconds (default 120)
- `HF_RETRIES`: transient retry attempts (default 4)

## Dependency rules (uv / pyproject)

1. Add `huggingface_hub` as a runtime dependency (InferenceClient).
2. If endpoint mode is the default, make heavy ML deps optional:
   - keep `torch`, `transformers`, and any VLM-specific deps only under an extra like `[project.optional-dependencies].local`
   - keep the default install lightweight for users who only use endpoints
3. Update `uv.lock` accordingly (via uv workflow used in the repo, e.g. the existing `just update` or `uv lock`).

## Code refactor plan (must follow)

### 1) Introduce an OCR backend interface

Create a small abstraction in `src/pdf2md/ocr/` (or similar) that hides how OCR is performed.

- `OcrBackend` protocol (or simple class) with a method like:
  - `ocr_page(image_bytes: bytes, *, page_index: int) -> str`   # returns markdown/text

### 2) Implement endpoint backend

Create `src/pdf2md/ocr/hf_endpoint.py`:

- Build an `InferenceClient` using:
  - `InferenceClient(base_url=HF_ENDPOINT_URL, token=HF_TOKEN)` when HF_ENDPOINT_URL is set
  - else `InferenceClient(model=HF_MODEL_ID, token=HF_TOKEN)`

- Send the page image as bytes.
  - Prefer an InferenceClient method that supports image input for VLM/OCR.
  - If the endpoint uses a custom handler, call a generic HTTP route (but still keep auth/timeout/retry).

- Implement retry with exponential backoff for transient failures (429, 5xx).
- Enforce timeout (from HF_TIMEOUT_S).

### 3) Keep (optional) local backend for parity

If you keep local inference as an option:

- Move current local model loading/inference into `src/pdf2md/ocr/local.py`
- It must only be imported/used when `PDF2MD_BACKEND=local`
- Endpoint mode must not import torch/transformers at import-time.

### 4) Wire the backend into the existing pipeline

Where pdf2md currently does per-page model inference, replace with:

- render PDF page → image (existing pypdfium2 flow)
- convert image to bytes (PNG or JPEG)
- call backend.ocr_page(image_bytes, page_index=i)
- accumulate markdown results
- write output (existing behavior)

### 5) CLI behavior

Keep the existing CLI command `pdf2md <input.pdf> [-o output.md]` working.
Add (optional) flags only if needed:

- `--backend endpoint|local` (maps to PDF2MD_BACKEND)
- `--endpoint-url` (maps to HF_ENDPOINT_URL, but prefer env vars)

Default should be `endpoint` to satisfy the goal “use HF GPU”.

### 6) Logging and observability

- Never print HF_TOKEN
- If logfire is present, log:
  - backend type (endpoint/local)
  - pages processed
  - total time
  - per-page latency (optional)
- Avoid logging raw OCR text by default (can be huge / sensitive)

## Tests (must add)

Add a test that does NOT require network by default:

- Unit test for “backend selection” (env var chooses correct backend)
- Unit test for “endpoint request builder” using mocking (no real HTTP)

Add an integration smoke test that is opt-in:

- Marked with pytest marker `integration`
- Runs only if HF_ENDPOINT_URL (or HF_MODEL_ID) + HF_TOKEN are set
- Converts a tiny 1-page PDF fixture and asserts non-empty output

## Done criteria

- `uv run pdf2md test.pdf` works with endpoint backend without local torch/transformers required.
- Default backend is endpoint (unless explicitly set otherwise).
- Dependencies managed through pyproject + uv.lock (no requirements.txt).
- Tests added: selection + request construction (mocked), plus optional integration test.

## Suggested code snippets

### Backend selection

```python
import os

def get_backend_name() -> str:
    return os.getenv("PDF2MD_BACKEND", "endpoint").strip().lower()
```
