# pdf2md

Convert PDF files to Markdown using [LightOnOCR-2-1B](https://huggingface.co/lightonai/LightOnOCR-2-1B), a state-of-the-art OCR model.

## Features

- **Fast OCR**: Uses LightOnOCR-2-1B, an efficient 1B-parameter vision-language model
- **Multi-platform**: Supports CUDA, Apple Silicon (MPS), and CPU backends
- **Progress tracking**: Rich progress bars show conversion status
- **Observability**: Built-in Logfire integration for monitoring

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for package management
- [just](https://github.com/casey/just) for command running

## Installation

```sh
# Clone the repository
git clone https://github.com/cast42/pdf2md.git
cd pdf2md

# Install dependencies
just install
```

## Usage

### Convert a PDF to Markdown

```sh
# Using just (recommended)
just pdf test.pdf

# Or using the CLI directly
uv run pdf2md test.pdf

# Specify custom output path
uv run pdf2md input.pdf -o output.md
```

### Example

```sh
$ just pdf document.pdf
Converting: document.pdf
Using device: mps with dtype torch.float32
✓ Model loaded successfully
✓ Loaded 5 page(s) from PDF
Processing page 5/5... ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:01:23
✓ Saved markdown to document.md
```

## Development

This project uses modern Python tooling:

- **uv**: Package and dependency management
- **ruff**: Linting and formatting
- **ty**: Type checking
- **pytest**: Testing
- **zensical**: Documentation
- **logfire**: Observability

### Available Commands

```sh
just              # List all available commands
just pdf <file>   # Convert PDF to Markdown
just test         # Run tests
just lint         # Run linter with auto-fix
just format       # Format code
just typing       # Run type checker
just check        # Run all pre-commit hooks
just install      # Install dependencies
just update       # Update dependencies
just clean        # Remove temporary files
```

### Running Tests

```sh
just test
```

### Code Quality

```sh
# Run all checks
just check

# Or individually
just lint
just typing
```

## Configuration

### Logfire (Optional)

To enable cloud logging with Logfire:

1. Get a token from [Logfire](https://logfire.pydantic.dev/docs/how-to-guides/create-write-tokens/)
2. Copy `.env.example` to `.env`
3. Add your token: `LOGFIRE_TOKEN=your-token-here`

Without a token, logging only appears in console output.

## How It Works

1. **PDF Loading**: Uses `pypdfium2` to render PDF pages as images at 300 DPI
2. **Model Inference**: Each page image is processed by LightOnOCR-2-1B
3. **Output**: Extracted text from all pages is concatenated and saved as Markdown

## Performance

- On Apple M4: ~5+ seconds per page (MPS backend)
- On NVIDIA H100: ~0.17 seconds per page (CUDA backend)
- CPU fallback available for systems without GPU

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [LightOn AI](https://www.lighton.ai/) for the LightOnOCR-2-1B model
- [Hugging Face](https://huggingface.co/) for the transformers library
