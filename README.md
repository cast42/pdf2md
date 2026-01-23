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
- **zensical**: Documentation (mkdocstrings for API references)
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

### Hugging Face Inference Endpoint (Default)

By default, pdf2md sends OCR requests to a Hugging Face Inference Endpoint.

Quick setup:

1. Create a Hugging Face access token with read scope.
2. Choose either a hosted model (cheaper/free tier) or a dedicated endpoint.
3. Export the environment variables below (or put them in `.env`).

Required environment variables:

- `HF_TOKEN`: Hugging Face access token
- `HF_ENDPOINT_URL` (preferred) or `HF_MODEL_ID`

Note: the hosted Inference API currently does not list image-to-text providers for most
OCR models. If you see a 404 or “No inference provider is available” error, use a
dedicated endpoint.

Optional:

- `PDF2MD_BACKEND=local` to run locally (requires `local` extra)
- `HF_TIMEOUT_S` (default: 120)
- `HF_RETRIES` (default: 4)

To use the local backend:

```sh
uv sync --extra local
PDF2MD_BACKEND=local uv run pdf2md input.pdf
```

For detailed setup (including the cheapest GPU options), see `docs/huggingface.md`.

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
