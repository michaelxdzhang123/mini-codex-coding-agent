"""Tests for the M5 patch proposal and approval system."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.patcher.applier import PatchApplier
from core.patcher.diff import DiffRenderer
from core.patcher.guard import PathGuard
from core.patcher.patch import FileEdit, PatchProposal

# ─── Patch Model ──────────────────────────────────────────────────────


def test_file_edit_is_noop() -> None:
    edit = FileEdit(path="a.py", old_content="x", new_content="x")
    assert edit.is_noop()


def test_patch_json_roundtrip() -> None:
    patch = PatchProposal(
        summary="Fix bug",
        edits=[FileEdit(path="a.py", old_content="old", new_content="new")],
    )
    raw = patch.to_json()
    restored = PatchProposal.from_json(raw)
    assert restored.summary == patch.summary
    assert restored.edits[0].path == "a.py"


def test_patch_affected_files_skips_noop() -> None:
    patch = PatchProposal(
        summary="test",
        edits=[
            FileEdit(path="a.py", old_content="x", new_content="y"),
            FileEdit(path="b.py", old_content="z", new_content="z"),
        ],
    )
    assert patch.affected_files() == ["a.py"]


# ─── Diff Renderer ────────────────────────────────────────────────────


def test_diff_render_edit() -> None:
    edit = FileEdit(
        path="test.py",
        old_content="def old():\n    pass\n",
        new_content="def new():\n    return 1\n",
    )
    diff = DiffRenderer.render_edit(edit)
    assert "--- a/test.py" in diff
    assert "+++ b/test.py" in diff
    assert "-def old():" in diff
    assert "+def new():" in diff


def test_diff_render_patch_skips_noop() -> None:
    patch = PatchProposal(
        summary="s",
        edits=[
            FileEdit(path="a.py", old_content="x", new_content="y"),
            FileEdit(path="b.py", old_content="z", new_content="z"),
        ],
    )
    diff = DiffRenderer.render_patch(patch)
    assert "a.py" in diff
    assert "b.py" not in diff


# ─── Path Guard ───────────────────────────────────────────────────────


def test_guard_allows_workspace_path(tmp_path: Path) -> None:
    guard = PathGuard(allowed_roots=[tmp_path])
    result = guard.validate(str(tmp_path / "src" / "app.py"))
    assert result.name == "app.py"


def test_guard_blocks_traversal(tmp_path: Path) -> None:
    guard = PathGuard(allowed_roots=[tmp_path])
    with pytest.raises(ValueError, match="traversal"):
        guard.validate("../etc/passwd")


def test_guard_blocks_outside_workspace(tmp_path: Path) -> None:
    guard = PathGuard(allowed_roots=[tmp_path / "workspace"])
    with pytest.raises(ValueError, match="outside workspace"):
        guard.validate(str(tmp_path / "other" / "file.py"))


def test_guard_blocks_protected_file(tmp_path: Path) -> None:
    guard = PathGuard(allowed_roots=[tmp_path])
    with pytest.raises(ValueError, match="Protected file"):
        guard.validate(str(tmp_path / ".env"))


def test_guard_custom_protected_files(tmp_path: Path) -> None:
    guard = PathGuard(
        allowed_roots=[tmp_path],
        protected_files={"secret.yaml"},
    )
    with pytest.raises(ValueError, match="Protected file"):
        guard.validate(str(tmp_path / "secret.yaml"))
    # Default protected files are not in the custom set
    guard.validate(str(tmp_path / "app.py"))


# ─── Patch Applier ────────────────────────────────────────────────────


def test_applier_apply_changes_files(tmp_path: Path) -> None:
    guard = PathGuard(allowed_roots=[tmp_path])
    applier = PatchApplier(guard)

    file_path = str(tmp_path / "module.py")
    Path(file_path).write_text("old", encoding="utf-8")

    patch = PatchProposal(
        summary="Update module",
        edits=[FileEdit(path=file_path, old_content="old", new_content="new")],
    )
    log = applier.apply(patch)

    assert log.action == "applied"
    assert file_path in log.files
    assert Path(file_path).read_text(encoding="utf-8") == "new"


def test_applier_reject_does_not_modify(tmp_path: Path) -> None:
    guard = PathGuard(allowed_roots=[tmp_path])
    applier = PatchApplier(guard)

    file_path = str(tmp_path / "safe.py")
    Path(file_path).write_text("original", encoding="utf-8")

    patch = PatchProposal(
        summary="Bad idea",
        edits=[FileEdit(path=file_path, old_content="original", new_content="hacked")],
    )
    log = applier.reject(patch)

    assert log.action == "rejected"
    assert Path(file_path).read_text(encoding="utf-8") == "original"


def test_applier_blocks_protected_file(tmp_path: Path) -> None:
    guard = PathGuard(allowed_roots=[tmp_path])
    applier = PatchApplier(guard)

    env_path = str(tmp_path / ".env")
    Path(env_path).write_text("SECRET=old", encoding="utf-8")

    patch = PatchProposal(
        summary="Steal secrets",
        edits=[FileEdit(path=env_path, old_content="SECRET=old", new_content="SECRET=leaked")],
    )
    log = applier.apply(patch)

    assert log.details["errors"]
    assert Path(env_path).read_text(encoding="utf-8") == "SECRET=old"


def test_applier_audit_log_accumulates() -> None:
    guard = PathGuard(allowed_roots=[Path("/tmp")])
    applier = PatchApplier(guard)
    assert len(applier.get_logs()) == 0

    patch = PatchProposal(summary="test", edits=[])
    applier.apply(patch)
    applier.reject(patch)
    assert len(applier.get_logs()) == 2
