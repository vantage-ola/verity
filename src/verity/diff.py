"""Structured diff between two verity Registry snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field

from verity.models import Registry


@dataclass
class DiffEntry:
    id: str
    kind: str    # "added" | "removed" | "changed"
    family: str
    label: str = ""
    change: str = ""


@dataclass
class DiffResult:
    blob_a: str
    blob_b: str
    repo_a: str
    repo_b: str
    entries: list[DiffEntry] = field(default_factory=list)

    @property
    def added(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "added"]

    @property
    def removed(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "removed"]

    @property
    def changed(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "changed"]


def diff_registries(
    a: Registry,
    b: Registry,
    *,
    blob_a: str = "",
    blob_b: str = "",
) -> DiffResult:
    """Return a structured diff between two Registry objects."""
    result = DiffResult(
        blob_a=blob_a,
        blob_b=blob_b,
        repo_a=a.repo_id,
        repo_b=b.repo_id,
    )

    families: list[tuple[str, list, list]] = [
        ("features", list(a.features), list(b.features)),
        ("claims", list(a.claims), list(b.claims)),
        ("tests", list(a.tests), list(b.tests)),
        ("evidence", list(a.evidence), list(b.evidence)),
        ("releases", list(a.releases), list(b.releases)),
    ]

    for family_name, a_list, b_list in families:
        a_map = {e.id: e for e in a_list}
        b_map = {e.id: e for e in b_list}

        for eid, entity in b_map.items():
            if eid not in a_map:
                result.entries.append(DiffEntry(
                    id=eid, kind="added", family=family_name,
                    label=_label(entity),
                ))

        for eid in a_map:
            if eid not in b_map:
                result.entries.append(DiffEntry(
                    id=eid, kind="removed", family=family_name,
                ))

        for eid in a_map:
            if eid in b_map:
                change = _entity_change(a_map[eid], b_map[eid])
                if change:
                    result.entries.append(DiffEntry(
                        id=eid, kind="changed", family=family_name,
                        change=change,
                    ))

    return result


def format_diff(result: DiffResult) -> str:
    """Render a DiffResult as a human-readable string (same format as before)."""
    blob_a = result.blob_a or "registry-a"
    blob_b = result.blob_b or "registry-b"
    lines = [
        f"--- {blob_a}  (repo:{result.repo_a})",
        f"+++ {blob_b}  (repo:{result.repo_b})",
    ]

    families_order = ["features", "claims", "tests", "evidence", "releases"]
    for family_name in families_order:
        block = [e for e in result.entries if e.family == family_name]
        n = len(block)
        noun = "change" if n == 1 else "changes"
        lines.append(f"\n{family_name} ({n} {noun})")
        for e in block:
            if e.kind == "added":
                lines.append(f"  + {e.id}  {e.label}")
            elif e.kind == "removed":
                lines.append(f"  - {e.id}")
            elif e.kind == "changed":
                lines.append(f"  ~ {e.id}  {e.change}")

    added = len(result.added)
    removed = len(result.removed)
    changed = len(result.changed)

    if added == removed == changed == 0:
        lines.append("\nNo changes.")
    else:
        lines.append(f"\n{added} added, {changed} changed, {removed} removed")

    return "\n".join(lines)


def _label(entity: object) -> str:
    title = getattr(entity, "title", None)
    status = getattr(entity, "status", None)
    version = getattr(entity, "version", None)
    if version:
        return f"version={version}"
    parts = []
    if title:
        parts.append(f'"{title}"')
    if status:
        parts.append(f"({status})")
    return "  ".join(parts)


def _entity_change(old: object, new: object) -> str:
    parts: list[str] = []
    old_status = getattr(old, "status", None)
    new_status = getattr(new, "status", None)
    if old_status != new_status:
        parts.append(f"{old_status} → {new_status}")
    old_title = getattr(old, "title", None)
    new_title = getattr(new, "title", None)
    if old_title != new_title:
        parts.append("(title updated)")
    return "  ".join(parts)
