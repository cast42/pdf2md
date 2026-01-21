# pdf2md

Convert PDF files to Markdown using LightOnOCR-2-1B, with a CLI wrapper and typed converter utilities.

## Overview

pdf2md includes:

- A CLI entry point (`pdf2md`) that renders PDFs into Markdown
- Converter utilities for model loading and OCR processing
- Structured logging via [Pydantic Logfire](https://pydantic.dev/logfire)
- Quality gates powered by Ruff, Ty, and pytest

## Usage

Run the CLI with:

```sh
uv run pdf2md path/to/document.pdf
```

## Documentation

- [API reference](reference.md) for modules, classes, and functions
- [Tests](tests.md) for the test suite and what each test covers

## Quality Gates

Use the `just` recipes to lint, type-check, test, and build project documentation:

```sh
just check   # lint + type-check
just test    # run the pytest suite
just docs    # build documentation with zensical
```
