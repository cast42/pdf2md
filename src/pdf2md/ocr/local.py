from __future__ import annotations

import importlib
import io
from typing import Any

import logfire
from PIL import Image

from pdf2md.ocr.base import OcrBackend


def _load_local_deps() -> tuple[Any, Any, Any]:
    """Load local ML dependencies at runtime."""
    try:
        torch = importlib.import_module("torch")
        lighton_module = importlib.import_module("transformers.models.lighton_ocr")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Local backend requires torch and transformers. Install with the 'local' extra.") from exc
    model_cls = getattr(lighton_module, "LightOnOcrForConditionalGeneration", None)
    processor_cls = getattr(lighton_module, "LightOnOcrProcessor", None)
    if model_cls is None or processor_cls is None:
        raise RuntimeError("Transformers LightOn OCR classes are unavailable in this environment.")
    return torch, model_cls, processor_cls


def get_device_and_dtype(torch_module: Any) -> tuple[str, Any]:
    """Determine the best available device and dtype for inference."""
    if torch_module.cuda.is_available():
        return "cuda", torch_module.bfloat16
    if torch_module.backends.mps.is_available():
        return "mps", torch_module.float32
    return "cpu", torch_module.bfloat16


class LocalBackend(OcrBackend):
    """OCR backend that runs LightOnOCR locally."""

    def __init__(self) -> None:
        self._torch, self._model_cls, self._processor_cls = _load_local_deps()
        self.device, self.dtype = get_device_and_dtype(self._torch)
        self._model: Any | None = None
        self._processor: Any | None = None

    def load(self) -> None:
        if self._model is not None and self._processor is not None:
            return
        with logfire.span("load_model", device=self.device, dtype=str(self.dtype)):
            model = self._model_cls.from_pretrained(
                "lightonai/LightOnOCR-2-1B",
                torch_dtype=self.dtype,
            )
            model = model.to(self._torch.device(self.device))
            self._model = model
            self._processor = self._processor_cls.from_pretrained("lightonai/LightOnOCR-2-1B")

    def ocr_page(self, image_bytes: bytes, *, page_index: int) -> str:
        self.load()
        assert self._model is not None
        assert self._processor is not None

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        with logfire.span("process_image", page_number=page_index + 1):
            conversation: list[dict[str, Any]] = [{"role": "user", "content": [{"type": "image", "image": image}]}]

            inputs = self._processor.apply_chat_template(
                conversation,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            )

            inputs = {
                k: v.to(device=self.device, dtype=self.dtype) if v.is_floating_point() else v.to(self.device)
                for k, v in inputs.items()
            }

            generation_config = inputs.pop("generation_config", None)
            max_new_tokens = inputs.pop("max_new_tokens", None)
            if generation_config is None:
                output_ids = self._model.generate(**inputs, max_new_tokens=max_new_tokens or 4096)
            else:
                generation_config = generation_config.copy()
                generation_config.max_new_tokens = max_new_tokens or 4096
                output_ids = self._model.generate(**inputs, generation_config=generation_config)
            generated_ids = output_ids[0, inputs["input_ids"].shape[-1] :]
            return self._processor.decode(generated_ids, skip_special_tokens=True)
