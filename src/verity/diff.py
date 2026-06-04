"""Structured diff between two verity Registry snapshots."""

from __future__ import annotations

from verity.models import Registry


def diff_registries(
    a: Registry,
    b: Registry,
    *,
    blob_a: str = "",
    blob_b: str = "",
) -> str:
    """Return a human-readable diff between two Registry objects."""
    lines: list[str] = []
    header_a = f"--- {blob_a or 'registry-a'}  (repo:{a.repo_id})" if blob_a else f"--- registry-a  (repo:{a.repo_id})"
    header_b = f"+++ {blob_b or 'registry-b'}  (repo:{b.repo_id})" if blob_b else f"+++ registry-b  (repo:{b.repo_id})"
    lines.append(header_a)
    lines.append(header_b)

    families: list[tuple[str, list, list]] = [
        ("features", list(a.features), list(b.features)),
        ("claims", list(a.claims), list(b.claims)),
        ("tests", list(a.tests), list(b.tests)),
        ("evidence", list(a.evidence), list(b.evidence)),
        ("releases", list(a.releases), list(b.releases)),
    ]

    added = removed = changed = 0
    family_blocks: list[str] = []

    for family_name, a_list, b_list in families:
        a_map = {e.id: e for e in a_list}
        b_map = {e.id: e for e in b_list}

        block: list[str] = []

        for eid, entity in b_map.items():
            if eid not in a_map:
                added += 1
                label = _label(entity)
                block.append(f"  + {eid}  {label}")

        for eid, entity in a_map.items():
            if eid not in b_map:
                removed += 1
                block.append(f"  - {eid}")

        for eid in a_map:
            if eid in b_map:
                old = a_map[eid]
                new = b_map[eid]
                change = _entity_change(old, new)
                if change:
                    changed += 1
                    block.append(f"  ~ {eid}  {change}")

        n = len(block)
        noun = "change" if n == 1 else "changes"
        family_blocks.append(f"\n{family_name} ({n} {noun})")
        family_blocks.extend(block)

    lines.extend(family_blocks)

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
