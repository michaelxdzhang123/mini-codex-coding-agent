"""Patch data models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class FileEdit:
    """A single file change within a patch proposal."""

    path: str
    old_content: str
    new_content: str

    def is_noop(self) -> bool:
        return self.old_content == self.new_content


@dataclass
class PatchProposal:
    """A proposed set of file edits awaiting review."""

    summary: str
    edits: list[FileEdit] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "summary": self.summary,
                "edits": [
                    {"path": e.path, "old_content": e.old_content, "new_content": e.new_content}
                    for e in self.edits
                ],
            },
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def from_json(cls, raw: str) -> PatchProposal:
        data = json.loads(raw)
        return cls(
            summary=data.get("summary", ""),
            edits=[
                FileEdit(path=e["path"], old_content=e["old_content"], new_content=e["new_content"])
                for e in data.get("edits", [])
            ],
        )

    def affected_files(self) -> list[str]:
        return [e.path for e in self.edits if not e.is_noop()]
