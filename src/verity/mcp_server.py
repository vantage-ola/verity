"""verity MCP server — expose proof-chain tools to any MCP-compatible editor."""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from verity import VeritySession, WalrusBackend, load_registry, save_registry
from verity.release import VerityReleaseError
from verity.session import VerityPushError

mcp = FastMCP(
    "verity",
    instructions=(
        "Use these tools to build and maintain a verity proof chain. "
        "A proof chain links Features → Claims → Tests → Evidence → Release. "
        "IMPORTANT: When building via these tools, add entities with neutral statuses first "
        "(open, pending, collected), wire the full chain, then call verity_set_status to promote "
        "(verified, passing, passed). Never set verified/passing before downstream entities exist. "
        "Always call verity_validate before verity_release. "
        "Pass blob_id as the handoff token between agents."
    ),
)


def _session(registry_path: str) -> VeritySession:
    backend = None
    if os.getenv("WALRUS_PUBLISHER_URL"):
        backend = WalrusBackend(
            publisher_url=os.environ["WALRUS_PUBLISHER_URL"],
            aggregator_url=os.getenv("WALRUS_AGGREGATOR_URL", ""),
        )
    return VeritySession(registry_path, backend=backend)


@mcp.tool()
def verity_init(registry_path: str = "verity.json", repo_id: str = "repo:default") -> str:
    """Initialise a new verity.json proof-chain registry."""
    try:
        s = VeritySession(registry_path)
        s.init(repo_id=repo_id)
        return f"Initialised registry at {registry_path} with repo_id={repo_id}"
    except FileExistsError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def verity_add_feature(
    id: str,
    title: str,
    status: str = "active",
    registry_path: str = "verity.json",
) -> str:
    """Add a Feature to the proof chain. id must use the feat: prefix. status: active|deprecated|retired."""
    try:
        s = VeritySession(registry_path)
        f = s.add_feature(id, title, status=status)
        return f"Added feature {f.id!r}: {f.title}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def verity_add_claim(
    id: str,
    title: str,
    feature_id: str,
    tier: str = "T1",
    status: str = "open",
    registry_path: str = "verity.json",
) -> str:
    """Add a Claim to the proof chain. id must use the clm: prefix. Use status='open' initially."""
    try:
        s = VeritySession(registry_path)
        c = s.add_claim(id, title, feature_id=feature_id, tier=tier, status=status)
        return f"Added claim {c.id!r}: {c.title} (tier={c.tier}, status={c.status})"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def verity_add_test(
    id: str,
    claim_id: str,
    kind: str = "unit",
    path: str = "",
    status: str = "pending",
    registry_path: str = "verity.json",
) -> str:
    """Add a Test to the proof chain. id must use the tst: prefix. Use status='pending' initially. kind: unit|integration."""
    try:
        s = VeritySession(registry_path)
        t = s.add_test(id, claim_id=claim_id, kind=kind, path=path, status=status)
        return f"Added test {t.id!r} (kind={t.kind}, path={t.path!r}, status={t.status})"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def verity_add_evidence(
    id: str,
    test_id: str,
    artifact_path: str,
    kind: str = "test_run",
    status: str = "collected",
    registry_path: str = "verity.json",
) -> str:
    """Add Evidence to the proof chain. id must use the evd: prefix. Use status='collected' initially."""
    try:
        s = VeritySession(registry_path)
        e = s.add_evidence(id, test_id=test_id, artifact_path=artifact_path, kind=kind, status=status)
        return f"Added evidence {e.id!r}: {e.artifact_path} (status={e.status})"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def verity_set_status(
    id: str,
    status: str,
    registry_path: str = "verity.json",
) -> str:
    """
    Promote an entity's status after the chain is fully wired.

    Feature:  active | deprecated | retired
    Claim:    open | verified | rejected   ← promote to 'verified' once test+evidence exist
    Test:     pending | passing | failing  ← promote to 'passing' once evidence exists
    Evidence: collected | passed | failed  ← promote to 'passed' once artifact is confirmed
    """
    try:
        reg = load_registry(Path(registry_path))
        entity: object | None = None
        for family, attr in [
            (reg.features, "status"),
            (reg.claims, "status"),
            (reg.tests, "status"),
            (reg.evidence, "status"),
        ]:
            for item in family:
                if item.id == id:
                    entity = item
                    break
            if entity is not None:
                break

        if entity is None:
            return f"Error: no entity with id={id!r} found in {registry_path}"

        old = entity.status  # type: ignore[attr-defined]
        entity.status = status  # type: ignore[attr-defined]

        # Validate before saving to catch bad transitions (e.g. verified with no linked test)
        from verity.validate import validate

        errors = validate(reg)
        if errors:
            entity.status = old  # type: ignore[attr-defined]
            return "Status update rejected — validation errors:\n" + "\n".join(f"  - {e}" for e in errors)

        save_registry(reg, Path(registry_path))
        return f"Updated {id!r}: {old} → {status}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def verity_validate(registry_path: str = "verity.json") -> str:
    """Validate the proof chain. Returns 'OK' or a list of validation errors."""
    try:
        s = VeritySession(registry_path)
        errors = s.validate()
        if not errors:
            return "OK"
        return "Errors:\n" + "\n".join(f"  - {e}" for e in errors)
    except FileNotFoundError as e:
        return f"Error: {e}"


@mcp.tool()
def verity_release(version: str, registry_path: str = "verity.json") -> str:
    """Create a fail-closed release snapshot. All verified claims must have passed evidence."""
    try:
        s = VeritySession(registry_path)
        rel = s.release(version)
        n = len(rel.claim_ids)
        return f"Released {rel.id} — {n} claim(s) at {rel.timestamp}"
    except VerityReleaseError as e:
        return f"Release failed: {e}"
    except FileNotFoundError as e:
        return f"Error: {e}"


@mcp.tool()
def verity_push(registry_path: str = "verity.json") -> str:
    """Push the registry to Walrus and return the blob_id. Requires WALRUS_PUBLISHER_URL env var."""
    try:
        s = _session(registry_path)
        blob_id = s.push()
        return f"Pushed. blob_id: {blob_id}"
    except (VerityPushError, FileNotFoundError) as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def verity_pull(blob_id: str, registry_path: str = "verity.json") -> str:
    """Pull a registry from Walrus by blob_id. Requires WALRUS_AGGREGATOR_URL env var."""
    try:
        s = _session(registry_path)
        s.pull(blob_id)
        return f"Pulled {blob_id!r} → {registry_path}"
    except (VerityPushError, FileNotFoundError) as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def verity_log(registry_path: str = "verity.json") -> str:
    """Return the full push history for the registry."""
    try:
        s = VeritySession(registry_path)
        records = s.log()
        if not records:
            return "No pushes yet."
        lines = [
            f"{i + 1:>3}. [{r.backend}]  {r.timestamp}  {r.blob_id}"
            for i, r in enumerate(records)
        ]
        return "\n".join(lines)
    except FileNotFoundError as e:
        return f"Error: {e}"


@mcp.tool()
def verity_status(registry_path: str = "verity.json") -> str:
    """Return a summary of the current proof chain: entity counts, validation status, latest push."""
    try:
        s = VeritySession(registry_path)
        reg = s.registry()
        errors = s.validate()
        valid = "yes" if not errors else f"no — {len(errors)} error(s)"
        latest_push = reg.pushes[-1].blob_id if reg.pushes else "none"
        lines = [
            f"repo_id:   {reg.repo_id}",
            f"features:  {len(reg.features)}",
            f"claims:    {len(reg.claims)}",
            f"tests:     {len(reg.tests)}",
            f"evidence:  {len(reg.evidence)}",
            f"releases:  {len(reg.releases)}",
            f"pushes:    {len(reg.pushes)}",
            f"valid:     {valid}",
            f"latest:    {latest_push}",
        ]
        return "\n".join(lines)
    except FileNotFoundError as e:
        return f"Error: {e}"


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
