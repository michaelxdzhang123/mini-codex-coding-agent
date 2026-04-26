"""Audit logging for command execution."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionLog:
    """Audit record for a single command execution."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    command: str = ""
    status: str = ""  # pending, approved, denied, running, success, failure, timeout, rejected
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    approved_by: str | None = None
    working_directory: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "approved_by": self.approved_by,
            "working_directory": self.working_directory,
            "details": self.details,
        }
