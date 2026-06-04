set shell := ["bash", "-cu"]

project_root := `pwd`

# List available recipes
default:
	@just --list

# ============================================================================
# Setup
# ============================================================================

# Sync the environment with dev and lint dependencies
[group('setup')]
setup:
	uv sync --extra lint --group dev

# Install UV package manager
[group('setup')]
get-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

# Build the Python package
[group('setup')]
build:
	uv build

# ============================================================================
# Quality
# ============================================================================

# Run the test suite
# Usage: just test [path] — e.g. just test tests/test_parallel.py
[group('quality')]
test *PATH:
	uv run --no-sync pytest {{ if PATH == "" { "tests" } else { PATH } }} --disable-warnings

# Lint with ruff
[group('quality')]
lint:
	uv run --no-sync ruff check .

# Format with ruff
[group('quality')]
format:
	uv run --no-sync ruff format .

# Type-check with ty
[group('quality')]
typecheck:
	uv run --no-sync ty check src tests

# Run all pre-commit hooks on all files
[group('quality')]
pre-commit:
	uv run --no-sync pre-commit run --all-files

# ============================================================================
# Utilities
# ============================================================================

# Clean generated files and caches
[group('utility')]
clean:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "Cleaning generated files and caches..."
	rm -rf dist
	rm -rf .pytest_cache .mypy_cache .ruff_cache .hypothesis
	rm -rf htmlcov .coverage .coverage.*
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	echo "Done."
