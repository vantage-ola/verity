"""verity MCP server — expose proof-chain tools to any MCP-compatible editor."""

from __future__ import annotations

import os
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from verity import VeritySession, WalrusBackend, load_registry, save_registry
from verity.release import VerityReleaseError
from verity.session import VerityPushError
from verity.memwal import MemWalBackend
from verity.models import Registry
from verity.validate import validate


mcp = FastMCP(
    "verity",
    instructions=(
        "Use these tools to build and maintain a verity proof chain. "
        "A proof chain links Features → Claims → Tests → Evidence → Release. "
        "IMPORTANT: After every feature, fix, or code change, update verity.json — "
        "add the relevant feat:/clm:/tst:/evd: entries so the chain reflects what actually exists in the repo. "
        "When building the chain, add entities with neutral statuses first "
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
def verity_init(registry_path: str = ".verity/registry.json", repo_id: str = "repo:default") -> str:
    """Initialise a new verity.json proof-chain registry."""
    try:
        s = VeritySession(registry_path)
        s.init(repo_id=repo_id)
        return f"Initialised registry at {registry_path} with repo_id={repo_id}"
    except FileExistsError as e:
        return f"Error: {e}"


@mcp.tool()
def verity_add_feature(
    id: str,
    title: str,
    status: str = "active",
    registry_path: str = ".verity/registry.json",
) -> str:
    """Add a Feature to the proof chain. id must use the feat: prefix. status: active|deprecated|retired."""
    s = VeritySession(registry_path)
    f = s.add_feature(id, title, status=status)
    return f"Added feature {f.id!r}: {f.title}"


@mcp.tool()
def verity_add_claim(
    id: str,
    title: str,
    feature_id: str,
    tier: str = "T1",
    status: str = "open",
    registry_path: str = ".verity/registry.json",
) -> str:
    """Add a Claim to the proof chain. id must use the clm: prefix. Use status='open' initially."""
    s = VeritySession(registry_path)
    c = s.add_claim(id, title, feature_id=feature_id, tier=tier, status=status)
    return f"Added claim {c.id!r}: {c.title} (tier={c.tier}, status={c.status})"


@mcp.tool()
def verity_add_test(
    id: str,
    claim_id: str,
    kind: str = "unit",
    path: str = "",
    status: str = "pending",
    registry_path: str = ".verity/registry.json",
) -> str:
    """Add a Test to the proof chain. id must use the tst: prefix. Use status='pending' initially. kind: unit|integration."""
    s = VeritySession(registry_path)
    t = s.add_test(id, claim_id=claim_id, kind=kind, path=path, status=status)
    return f"Added test {t.id!r} (kind={t.kind}, path={t.path!r}, status={t.status})"


@mcp.tool()
def verity_add_evidence(
    id: str,
    test_id: str,
    artifact_path: str,
    kind: str = "test_run",
    status: str = "collected",
    registry_path: str = ".verity/registry.json",
) -> str:
    """Add Evidence to the proof chain. id must use the evd: prefix. Use status='collected' initially."""
    s = VeritySession(registry_path)
    e = s.add_evidence(id, test_id=test_id, artifact_path=artifact_path, kind=kind, status=status)
    return f"Added evidence {e.id!r}: {e.artifact_path} (status={e.status})"


@mcp.tool()
def verity_set_status(
    id: str,
    status: str,
    registry_path: str = ".verity/registry.json",
) -> str:
    """
    Promote an entity's status after the chain is fully wired.

    Feature:  active | deprecated | retired
    Claim:    open | verified | rejected   ← promote to 'verified' once test+evidence exist
    Test:     pending | passing | failing  ← promote to 'passing' once evidence exists
    Evidence: collected | passed | failed  ← promote to 'passed' once artifact is confirmed
    """
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


@mcp.tool()
def verity_set_status_batch(
    updates: list[dict],
    registry_path: str = ".verity/registry.json",
) -> str:
    """
    Promote multiple entities in one call — validate once, save once.

    updates: list of {"id": "<entity-id>", "status": "<new-status>"} dicts.

    Example:
        [{"id": "evd:auth.ci", "status": "passed"},
         {"id": "tst:auth.unit", "status": "passing"},
         {"id": "clm:auth.t1", "status": "verified"}]
    """
    reg = load_registry(Path(registry_path))
    all_entities = [*reg.features, *reg.claims, *reg.tests, *reg.evidence]
    index = {e.id: e for e in all_entities}

    applied: list[str] = []
    originals: dict[str, str] = {}

    for item in updates:
        eid = item.get("id", "")
        new_status = item.get("status", "")
        if not eid or not new_status:
            return f"Error: each update must have 'id' and 'status' keys, got {item!r}"
        entity = index.get(eid)
        if entity is None:
            return f"Error: no entity with id={eid!r} found in {registry_path}"
        originals[eid] = entity.status  # type: ignore[attr-defined]
        entity.status = new_status  # type: ignore[attr-defined]
        applied.append(f"{eid!r}: {originals[eid]} → {new_status}")

    errors = validate(reg)
    if errors:
        for eid, old in originals.items():
            index[eid].status = old  # type: ignore[attr-defined]
        return "Status updates rejected — validation errors:\n" + "\n".join(f"  - {e}" for e in errors)

    save_registry(reg, Path(registry_path))
    return "Updated:\n" + "\n".join(f"  {line}" for line in applied)


@mcp.tool()
def verity_validate(registry_path: str = ".verity/registry.json") -> str:
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
def verity_release(version: str, registry_path: str = ".verity/registry.json") -> str:
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
def verity_push(registry_path: str = ".verity/registry.json") -> str:
    """Push the registry to Walrus and return the blob_id. Requires WALRUS_PUBLISHER_URL env var."""
    try:
        s = _session(registry_path)
        blob_id = s.push()
        return f"Pushed. blob_id: {blob_id}"
    except (VerityPushError, FileNotFoundError) as e:
        return f"Error: {e}"


@mcp.tool()
def verity_pull(blob_id: str, registry_path: str = ".verity/registry.json", force: bool = False) -> str:
    """Pull a registry from Walrus by blob_id. Pass force=True to overwrite an existing file. Requires WALRUS_AGGREGATOR_URL env var."""
    try:
        s = _session(registry_path)
        s.pull(blob_id, force=force)
        return f"Pulled {blob_id!r} → {registry_path}"
    except FileExistsError as e:
        return f"Error: {e}"
    except (VerityPushError, FileNotFoundError) as e:
        return f"Error: {e}"


@mcp.tool()
def verity_log(registry_path: str = ".verity/registry.json") -> str:
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
def verity_status(registry_path: str = ".verity/registry.json") -> str:
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


@mcp.tool()
def verity_diff(blob_a: str, blob_b: str) -> str:
    """Show what changed between two Walrus blob snapshots of a proof chain. Requires WALRUS_AGGREGATOR_URL env var."""
    import json

    from verity.diff import diff_registries, format_diff
    from verity.models import Registry

    backend = WalrusBackend(
        publisher_url=os.getenv("WALRUS_PUBLISHER_URL", ""),
        aggregator_url=os.getenv("WALRUS_AGGREGATOR_URL", ""),
    )
    content_a = backend.fetch(blob_a)
    content_b = backend.fetch(blob_b)
    reg_a = Registry.model_validate(json.loads(content_a))
    reg_b = Registry.model_validate(json.loads(content_b))
    return format_diff(diff_registries(reg_a, reg_b, blob_a=blob_a, blob_b=blob_b))


@mcp.tool()
def verity_export(format: str = "sarif", registry_path: str = ".verity/registry.json") -> str:
    """Export the proof chain to a standard DevSecOps format. format: sarif, junit, or spdx."""
    from verity.export import export

    try:
        reg = load_registry(Path(registry_path))
        return export(reg, format)
    except ValueError as e:
        return f"Error: {e}"
    except FileNotFoundError as e:
        return f"Error: {e}"


@mcp.tool()
def verity_sign(key_path: str, registry_path: str = ".verity/registry.json") -> str:
    """Sign the latest push blob with an Ed25519 private key. key_path must point to a PEM private key generated by verity keygen."""
    try:
        from verity.signing import load_private_key, pubkey_to_b64, sign_blob
    except ImportError:  # pragma: no cover
        return "Error: signing support requires cryptography — run: pip install 'walrus-verity[sign]'"
    try:
        reg = load_registry(Path(registry_path))
    except FileNotFoundError as e:
        return f"Error: {e}"
    if not reg.pushes:
        return "Error: no pushes recorded. Run verity_push first."
    try:
        priv = load_private_key(Path(key_path))
    except FileNotFoundError:
        return f"Error: key not found: {key_path}"
    record = reg.pushes[-1]
    sig = sign_blob(record.blob_id, priv)
    pub_b64 = pubkey_to_b64(priv.public_key())
    reg.pushes[-1] = record.model_copy(update={"signature": sig, "signer_pubkey": pub_b64})
    save_registry(reg, Path(registry_path))
    return f"Signed blob {record.blob_id}\npubkey-b64: {pub_b64}"


@mcp.tool()
def verity_verify(blob_id: str, pubkey_b64: str = "") -> str:
    """Fetch a blob from Walrus, validate the chain, and optionally verify its signature. Reads WALRUS_AGGREGATOR_URL from env."""
    try:
        backend = WalrusBackend(
            publisher_url=os.getenv("WALRUS_PUBLISHER_URL", ""),
            aggregator_url=os.getenv("WALRUS_AGGREGATOR_URL", ""),
        )
        content = backend.fetch(blob_id)
        reg = Registry.model_validate(json.loads(content))
    except Exception as e:
        return f"Error fetching blob: {e}"

    errors = validate(reg)
    lines = [
        f"blob: {blob_id}",
        f"repo: {reg.repo_id}",
        f"features {len(reg.features)}  claims {len(reg.claims)} ({sum(1 for c in reg.claims if c.status == 'verified')} verified)"
        f"  tests {len(reg.tests)}  evidence {len(reg.evidence)}",
    ]
    if errors:
        lines.append("chain invalid ✗")
        lines.extend(f"  {e}" for e in errors)
        return "\n".join(lines)
    lines.append("chain valid ✓")

    attested_blob: str | None = None
    sig: str | None = None
    signer: str | None = pubkey_b64 or None
    for record in reversed(reg.pushes):
        if record.signature:
            sig = record.signature
            attested_blob = record.blob_id
            if not signer:
                signer = record.signer_pubkey
            break

    if sig and signer and attested_blob:
        try:
            from verity.signing import verify_blob
        except ImportError:  # pragma: no cover
            lines.append("Error: signing support requires cryptography — run: pip install 'walrus-verity[sign]'")
            return "\n".join(lines)
        if verify_blob(attested_blob, sig, signer):
            lines.append(f"signature valid ✓   attests: {attested_blob[:16]}…  signer: {signer[:16]}…")
        else:
            lines.append("signature invalid ✗")
    elif pubkey_b64:
        lines.append("no signature found in push records for this blob")

    return "\n".join(lines)


@mcp.tool()
def verity_recall(query: str, namespace: str = "verity") -> str:
    """Query MemWal with a natural language question. Returns the top matching memories registered during the last verity push --backend memwal. Requires MEMWAL_KEY and MEMWAL_ACCOUNT_ID env vars."""
    try:
        backend = MemWalBackend(namespace=namespace)
        return backend.recall(query, namespace=namespace)
    except ImportError:  # pragma: no cover
        return "Error: memwal package not installed — run: pip install 'walrus-verity[memwal]'"


def main() -> None:  # pragma: no cover
    mcp.run(transport="stdio")


if __name__ == "__main__":  # pragma: no cover
    main()
