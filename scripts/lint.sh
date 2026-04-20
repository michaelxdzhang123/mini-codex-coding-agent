#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Please install uv first."
  exit 1
fi

uv sync

echo "Running ruff..."
uv run ruff check .

echo "Running black --check..."
uv run black --check .

echo "Running mypy..."
uv run mypy app core worker
