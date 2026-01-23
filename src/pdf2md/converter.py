"""PDF to Markdown converter using LightOnOCR-2-1B."""

import io
from pathlib import Path

import logfire
import pypdfium2 as pdfium
from PIL import Image
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn

from pdf2md.ocr import get_backend_name, get_ocr_backend

# Configure logfire without prompting when no token is available.
logfire.configure(send_to_logfire="if-token-present")

console = Console()


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


def image_to_bytes(image: Image.Image) -> bytes:
    """Serialize a PIL image to PNG bytes."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def convert_pdf_to_markdown(pdf_path: Path, output_path: Path | None = None) -> str:
    """Convert a PDF file to Markdown using LightOnOCR-2-1B.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Optional path for output .md file. If None, uses pdf_path with .md extension

    Returns:
        The extracted markdown text
    """
    backend_name = get_backend_name()
    backend = get_ocr_backend()

    with logfire.span("convert_pdf_to_markdown", pdf_path=str(pdf_path), backend=backend_name):
        if output_path is None:
            output_path = pdf_path.with_suffix(".md")

        backend_label = f"{backend_name}"
        if backend_name == "local":
            device = getattr(backend, "device", "unknown")
            dtype = getattr(backend, "dtype", "unknown")
            backend_label = f"{backend_label} (device {device}, dtype {dtype})"
        console.print(f"[bold blue]Using backend:[/bold blue] {backend_label}")

        # Load model with progress indication
        if backend_name == "local" and hasattr(backend, "load"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Loading LightOnOCR-2-1B model...", total=None)
                backend.load()  # type: ignore[no-untyped-call]

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
                with logfire.span("process_page", page_number=i + 1, backend=backend_name):
                    text = backend.ocr_page(image_to_bytes(image), page_index=i)
                    markdown_parts.append(text)
                    progress.update(task, advance=1, description=f"[cyan]Processing page {i + 1}/{len(images)}...")

        # Combine all pages
        full_markdown = "\n\n---\n\n".join(markdown_parts)

        # Write output file
        output_path.write_text(full_markdown, encoding="utf-8")
        console.print(f"[bold green]✓[/bold green] Saved markdown to [bold]{output_path}[/bold]")

        return full_markdown
