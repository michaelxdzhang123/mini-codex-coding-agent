"""Patch proposal, diff, and approval system."""

from __future__ import annotations

from core.patcher.applier import PatchApplier, PatchAuditLog
from core.patcher.diff import DiffRenderer
from core.patcher.guard import PathGuard
from core.patcher.patch import FileEdit, PatchProposal

__all__ = [
    "DiffRenderer",
    "FileEdit",
    "PatchApplier",
    "PatchAuditLog",
    "PatchProposal",
    "PathGuard",
]
