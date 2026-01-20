"""Command-line interface for pdf2md."""

import argparse
import sys
from pathlib import Path

from rich.console import Console

from pdf2md.converter import convert_pdf_to_markdown

console = Console()


def main() -> int:
    """Main entry point for the pdf2md CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog="pdf2md",
        description="Convert PDF files to Markdown using LightOnOCR-2-1B",
    )
    parser.add_argument(
        "pdf_file",
        type=Path,
        help="Path to the PDF file to convert",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path for the Markdown file (default: same as input with .md extension)",
    )

    args = parser.parse_args()

    pdf_path: Path = args.pdf_file
    output_path: Path | None = args.output

    # Validate input file
    if not pdf_path.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {pdf_path}")
        return 1

    if not pdf_path.suffix.lower() == ".pdf":
        console.print(f"[bold red]Error:[/bold red] File must be a PDF: {pdf_path}")
        return 1

    try:
        console.print(f"[bold]Converting:[/bold] {pdf_path}")
        convert_pdf_to_markdown(pdf_path, output_path)
        return 0
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
