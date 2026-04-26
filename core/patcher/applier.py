"""Patch applier with audit logging."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any

from core.patcher.guard import PathGuard
from core.patcher.patch import PatchProposal


@dataclass
class PatchAuditLog:
    """Audit record for a patch application."""

    patch_summary: str
    action: str  # approved, rejected, applied
    files: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "patch_summary": self.patch_summary,
            "action": self.action,
            "files": self.files,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class PatchApplier:
    """
    Applies approved patch proposals to the filesystem.

    Responsibilities:
    1. Validate every edit through PathGuard
    2. Write changes atomically (file by file)
    3. Produce audit logs
    """

    def __init__(self, guard: PathGuard) -> None:
        self.guard = guard
        self._logs: list[PatchAuditLog] = []

    def apply(self, patch: PatchProposal) -> PatchAuditLog:
        """
        Apply a patch proposal after approval.

        Each file edit is validated before writing.
        Returns an audit log entry.
        """
        changed_files: list[str] = []
        errors: list[str] = []

        for edit in patch.edits:
            if edit.is_noop():
                continue
            try:
                target = self.guard.validate(edit.path)
                target.write_text(edit.new_content, encoding="utf-8")
                changed_files.append(str(target))
            except ValueError as e:
                errors.append(str(e))

        log = PatchAuditLog(
            patch_summary=patch.summary,
            action="applied",
            files=changed_files,
            details={"errors": errors} if errors else {},
        )
        self._logs.append(log)
        return log

    def reject(self, patch: PatchProposal) -> PatchAuditLog:
        """Record a rejection without applying changes."""
        log = PatchAuditLog(
            patch_summary=patch.summary,
            action="rejected",
            files=[e.path for e in patch.edits],
        )
        self._logs.append(log)
        return log

    def get_logs(self) -> list[PatchAuditLog]:
        return list(self._logs)
