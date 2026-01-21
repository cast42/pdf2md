"""PDF to Markdown converter using LightOnOCR-2-1B model."""

from pathlib import Path
from typing import Any, cast

import logfire
import pypdfium2 as pdfium
import torch
from PIL import Image
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from transformers.models.lighton_ocr import LightOnOcrForConditionalGeneration, LightOnOcrProcessor

# Configure logfire
logfire.configure()

console = Console()


def get_device_and_dtype() -> tuple[str, torch.dtype]:
    """Determine the best available device and dtype for inference.

    Returns:
        Tuple of (device string, torch dtype)
    """
    if torch.cuda.is_available():
        return "cuda", torch.bfloat16
    elif torch.backends.mps.is_available():
        return "mps", torch.float32
    else:
        # Use bfloat16 on CPU to save memory (approx 4GB for 2B model vs 8GB for float32)
        return "cpu", torch.bfloat16


def load_model(device: str, dtype: torch.dtype) -> tuple[LightOnOcrForConditionalGeneration, LightOnOcrProcessor]:
    """Load the LightOnOCR-2-1B model and processor.

    Args:
        device: Device to load model on ('cuda', 'mps', or 'cpu')
        dtype: Torch dtype for model weights

    Returns:
        Tuple of (model, processor)
    """
    with logfire.span("load_model", device=device, dtype=str(dtype)):
        model = LightOnOcrForConditionalGeneration.from_pretrained(
            "lightonai/LightOnOCR-2-1B",
            torch_dtype=dtype,
        )
        model = cast(Any, model).to(torch.device(device))
        model = cast(LightOnOcrForConditionalGeneration, model)
        processor = LightOnOcrProcessor.from_pretrained("lightonai/LightOnOCR-2-1B")
        return model, processor


def pdf_to_images(pdf_path: Path) -> list[Image.Image]:
    """Convert PDF pages to PIL Images.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of PIL Images, one per page
    """
    with logfire.span("pdf_to_images", pdf_path=str(pdf_path)):
        pdf = pdfium.PdfDocument(pdf_path)
        images = []
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            # Render at 300 DPI for good OCR quality
            bitmap = page.render(scale=300 / 72)
            pil_image = bitmap.to_pil()
            images.append(pil_image)
        return images


def process_image(
    image: Image.Image,
    model: LightOnOcrForConditionalGeneration,
    processor: LightOnOcrProcessor,
    device: str,
    dtype: torch.dtype,
) -> str:
    """Process a single image through the OCR model.

    Args:
        image: PIL Image to process
        model: LightOnOCR model
        processor: LightOnOCR processor
        device: Device for inference
        dtype: Torch dtype for tensors

    Returns:
        Extracted text from the image
    """
    with logfire.span("process_image"):
        conversation: list[dict[str, Any]] = [{"role": "user", "content": [{"type": "image", "image": image}]}]

        inputs = cast(
            dict[str, Any],
            processor.apply_chat_template(
                cast(list[dict[str, str]], conversation),
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ),
        )

        # Move inputs to device with appropriate dtype
        inputs = {
            k: v.to(device=device, dtype=dtype) if v.is_floating_point() else v.to(device) for k, v in inputs.items()
        }

        generation_config = inputs.pop("generation_config", None)
        max_new_tokens = inputs.pop("max_new_tokens", None)
        if generation_config is None:
            output_ids = model.generate(**inputs, max_new_tokens=max_new_tokens or 4096)
        else:
            generation_config = generation_config.copy()
            generation_config.max_new_tokens = max_new_tokens or 4096
            output_ids = model.generate(**inputs, generation_config=generation_config)
        generated_ids = output_ids[0, inputs["input_ids"].shape[-1] :]
        output_text = processor.decode(generated_ids, skip_special_tokens=True)

        return output_text


def convert_pdf_to_markdown(pdf_path: Path, output_path: Path | None = None) -> str:
    """Convert a PDF file to Markdown using LightOnOCR-2-1B.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Optional path for output .md file. If None, uses pdf_path with .md extension

    Returns:
        The extracted markdown text
    """
    with logfire.span("convert_pdf_to_markdown", pdf_path=str(pdf_path)):
        if output_path is None:
            output_path = pdf_path.with_suffix(".md")

        # Determine device and dtype
        device, dtype = get_device_and_dtype()
        console.print(f"[bold blue]Using device:[/bold blue] {device} with dtype {dtype}")

        # Load model with progress indication
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Loading LightOnOCR-2-1B model...", total=None)
            model, processor = load_model(device, dtype)

        console.print("[bold green]✓[/bold green] Model loaded successfully")

        # Convert PDF to images
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Converting PDF pages to images...", total=None)
            images = pdf_to_images(pdf_path)

        console.print(f"[bold green]✓[/bold green] Loaded {len(images)} page(s) from PDF")

        # Process each page with progress bar
        markdown_parts: list[str] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("[cyan]Processing pages...", total=len(images))

            for i, image in enumerate(images):
                with logfire.span("process_page", page_number=i + 1):
                    text = process_image(image, model, processor, device, dtype)
                    markdown_parts.append(text)
                    progress.update(task, advance=1, description=f"[cyan]Processing page {i + 1}/{len(images)}...")

        # Combine all pages
        full_markdown = "\n\n---\n\n".join(markdown_parts)

        # Write output file
        output_path.write_text(full_markdown, encoding="utf-8")
        console.print(f"[bold green]✓[/bold green] Saved markdown to [bold]{output_path}[/bold]")

        return full_markdown
