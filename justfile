#!/usr/bin/env just --justfile
export PATH := join(justfile_directory(), ".env", "bin") + ":" + env_var('PATH')

set dotenv-load
set positional-arguments

@_:
    just --list

# Convert a PDF file to Markdown using LightOnOCR-2-1B (e.g., just test.pdf)
[no-cd]
@pdf pdf_file:
    PYTHONPATH=src uv run pdf2md "$1"

[group('qa')]
test *args:
    uv run -m pytest -q {{args}}

[group('qa')]
lint *args:
    uv run ruff check --fix {{args}}

[group('qa')]
format *args:
    uv run ruff format {{args}}

[group('qa')]
typing *args:
    uv run ty check {{args}}

[group('qa')]
check *args:
    # Run pre-commit hooks against all files
    uv run pre-commit run --all-files

[group('docs')]
docs *args:
    uv run zensical build {{args}}

# Run converts of pdf file as argument to markdown
run *args:
    PYTHONPATH=src uv run pdf2md {{args}}

# Remove temporary files
[group('lifecycle')]
clean:
    rm -rf .venv .pytest_cache .ruff_cache .uv-cache
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    find . -type d -name "__pycache__" -exec rm -r {} +

# Update dependencies
[group('lifecycle')]
update:
    # Upgrade all dependencies in the lock file but leave the .venv
    uv lock --upgrade

# Ensure project virtualenv is up to date
[group('lifecycle')]
install:
    if [ "${PDF2MD_BACKEND:-}" = "local" ]; then \
        uv sync --dev --extra local; \
    else \
        uv sync --dev; \
    fi
    uv run pre-commit install
