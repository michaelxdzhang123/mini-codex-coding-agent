#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Please install uv first."
  exit 1
fi

uv sync

echo "Formatting with black..."
uv run black .

echo "Fixing imports/style with ruff..."
uv run ruff check . --fix
