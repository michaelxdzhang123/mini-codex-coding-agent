.PHONY: help dev worker test lint format db-init db-migrate db-upgrade clean

# =========================
# Default
# =========================

help:
	@echo "Available commands:"
	@echo "  make dev           - Start Flask dev server"
	@echo "  make worker        - Start background worker"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run lint checks"
	@echo "  make format        - Format code"
	@echo "  make db-init       - Initialize database (first time)"
	@echo "  make db-migrate    - Create new migration"
	@echo "  make db-upgrade    - Apply migrations"
	@echo "  make clean         - Clean cache files"

# =========================
# Core (safe commands)
# =========================

dev:
	uv sync
	FLASK_APP=app uv run flask run --debug

worker:
	uv sync
	uv run python worker/runner.py

test:
	uv sync
	uv run pytest

lint:
	uv sync
	uv run ruff check .

format:
	uv sync
	uv run black .
	uv run ruff check . --fix

# =========================
# Database (Alembic)
# =========================

db-init:
	uv sync
	uv run alembic init migrations

db-migrate:
	uv sync
	uv run alembic revision --autogenerate -m "auto migration"

db-upgrade:
	uv sync
	uv run alembic upgrade head

# =========================
# Utility
# =========================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

.PHONY: index-knowledge query-knowledge

index-knowledge:
	uv sync
	uv run python -m core.rag.indexer

query-knowledge:
	uv sync
	uv run python -m core.rag.retriever --query "$(QUERY)"
