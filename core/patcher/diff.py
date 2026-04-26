"""Diff rendering for patch proposals."""

from __future__ import annotations

import difflib

from core.patcher.patch import FileEdit, PatchProposal


class DiffRenderer:
    """
    Render unified diffs for patch proposals.

    Uses Python's built-in difflib for consistent, readable output.
    """

    @staticmethod
    def render_edit(edit: FileEdit) -> str:
        """Render a unified diff for a single file edit."""
        old_lines = edit.old_content.splitlines(keepends=True)
        new_lines = edit.new_content.splitlines(keepends=True)

        # Ensure lines end with newline for clean diff output
        if old_lines and not old_lines[-1].endswith("\n"):
            old_lines[-1] += "\n"
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{edit.path}",
            tofile=f"b/{edit.path}",
        )
        return "".join(diff)

    @classmethod
    def render_patch(cls, patch: PatchProposal) -> str:
        """Render unified diffs for all edits in a patch."""
        parts: list[str] = []
        for edit in patch.edits:
            if edit.is_noop():
                continue
            diff = cls.render_edit(edit)
            if diff:
                parts.append(diff)
        return "\n".join(parts)
