# Architecture

## 1. Overview

This project is a minimal web-based coding agent for small engineering teams.

Phase 1 focuses on:
- Flask-based web UI
- Controlled local repository access
- Task planning
- Safe file editing
- Safe command execution

No IDE integration (VS Code) in this phase.

---

## 2. System Architecture

```text
Browser (User)
    │
    ▼
Flask Web App (UI + API)
    │
    ├── Services Layer
    │     ├── Task Service
    │     ├── Repo Service
    │     ├── Planning Service
    │
    ├── Core Agent Layer
    │     ├── Planner
    │     ├── Context Builder
    │     ├── Patch Generator
    │     ├── Tool Orchestrator
    │
    ├── Tools Layer
    │     ├── File Tools
    │     ├── Search Tools
    │     ├── Git Tools
    │     ├── Shell Tools (whitelisted)
    │
    ├── Safety Layer
    │     ├── Path Guard
    │     ├── Command Guard
    │
    ├── LLM Layer
    │     ├── Adapter
    │     ├── Mock Provider
    │
    ▼
Worker (RQ / Celery)
    │
    ▼
Local Workspace (Git Repo)
