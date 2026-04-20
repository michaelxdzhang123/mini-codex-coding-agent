# Mini Web Codex (Flask Edition)

A minimal internal coding agent for small engineering teams in China.

This project provides a web-based interface to:
- submit coding tasks
- inspect local repositories
- generate plans
- propose code edits
- run safe checks
- review diffs and logs

---

## Tech Stack

- Python 3.11+
- Flask
- Jinja2
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- RQ / Celery (background jobs)

---

## Project Structure

```text
app/        Flask app (UI + API)
core/       agent logic and tools
worker/     background jobs
configs/    whitelist and rules
docs/       documentation
tests/      tests
