from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from verity.backends import StorageBackend
from verity.memwal import MemWalBackend, MemWalError
from verity.models import Claim, ContextEntry, Evidence, Feature, PushRecord, Registry, Test
from verity.registry import canonical_json, load_registry, registry_path, save_registry
from verity.release import VerityReleaseError, create_release
from verity.site import generate_html
from verity.validate import validate
from verity.walrus import WalrusBackend, WalrusError

app = typer.Typer(help="verity — proof-chain registry for AI agents")
add_app = typer.Typer(help="Add an entity to the registry")
context_app = typer.Typer(no_args_is_help=True, help="Manage project context entries.")
app.add_typer(add_app, name="add")
app.add_typer(context_app, name="context")


@app.callback()
def _load_env() -> None:
    load_dotenv()

BackendChoice = Annotated[str, typer.Option("--backend", "-b", help="Storage backend: walrus or memwal")]


def _load(directory: Path = Path(".")) -> tuple[Path, Registry]:
    path = registry_path(directory)
    if not path.exists():
        typer.echo(f"No verity.json found in {directory}. Run 'verity init' first.", err=True)
        raise typer.Exit(1)
    return path, load_registry(path)


def _save_validated(path: Path, registry: Registry) -> None:
    errors = validate(registry)
    if errors:
        for e in errors:
            typer.echo(f"  error: {e}", err=True)
        typer.echo("Registry has validation errors — not saved.", err=True)
        raise typer.Exit(1)
    save_registry(registry, path)


def _get_backend(backend_name: str, epochs: int = 5) -> StorageBackend:
    if backend_name == "memwal":
        try:
            return MemWalBackend()
        except MemWalError as e:
            typer.echo(f"MemWal config error: {e}", err=True)
            raise typer.Exit(1)
    return WalrusBackend(epochs=epochs)


@app.command()
def init(
    repo_id: Annotated[str, typer.Option("--repo-id", help="Registry repo ID")] = "repo:default",
    directory: Annotated[Path, typer.Argument()] = Path("."),
) -> None:
    """Create verity.json in the current directory."""
    path = registry_path(directory)
    if path.exists():
        typer.echo(f"{path} already exists.", err=True)
        raise typer.Exit(1)
    registry = Registry(repo_id=repo_id)
    save_registry(registry, path)
    typer.echo(f"Initialized {path}")


@add_app.command("feature")
def add_feature(
    id: Annotated[str, typer.Argument(help="Feature ID (e.g. feat:auth)")],
    title: Annotated[str, typer.Argument(help="Short title")],
) -> None:
    """Add a feature to the registry."""
    path, registry = _load()
    feature = Feature(id=id, title=title)
    registry.features.append(feature)
    _save_validated(path, registry)
    typer.echo(f"Added feature {id}")


@add_app.command("claim")
def add_claim(
    id: Annotated[str, typer.Argument(help="Claim ID (e.g. clm:auth.t1)")],
    title: Annotated[str, typer.Argument(help="Short title")],
    feature: Annotated[str, typer.Option("--feature", "-f", help="Parent feature ID")],
    tier: Annotated[str, typer.Option("--tier", help="Claim tier")] = "T1",
    status: Annotated[str, typer.Option("--status", help="open|verified|rejected")] = "open",
) -> None:
    """Add a claim to the registry."""
    path, registry = _load()
    claim = Claim(id=id, feature_id=feature, title=title, tier=tier, status=status)  # type: ignore[arg-type]
    registry.claims.append(claim)
    _save_validated(path, registry)
    typer.echo(f"Added claim {id}")


@add_app.command("test")
def add_test(
    id: Annotated[str, typer.Argument(help="Test ID (e.g. tst:auth.unit)")],
    title: Annotated[str, typer.Argument(help="Short title")],
    claim: Annotated[str, typer.Option("--claim", "-c", help="Parent claim ID")],
    kind: Annotated[str, typer.Option("--kind", "-k", help="unit or integration")] = "unit",
    path: Annotated[str, typer.Option("--path", "-p", help="Test file path")] = "",
    status: Annotated[str, typer.Option("--status", help="pending|passing|failing")] = "pending",
) -> None:
    """Add a test to the registry."""
    reg_path, registry = _load()
    test = Test(id=id, claim_id=claim, kind=kind, path=path, status=status)  # type: ignore[arg-type]
    registry.tests.append(test)
    _save_validated(reg_path, registry)
    typer.echo(f"Added test {id}")


@add_app.command("evidence")
def add_evidence(
    id: Annotated[str, typer.Argument(help="Evidence ID (e.g. evd:auth.run1)")],
    title: Annotated[str, typer.Argument(help="Short title")],
    test: Annotated[str, typer.Option("--test", "-t", help="Parent test ID")],
    kind: Annotated[str, typer.Option("--kind", "-k", help="Evidence kind")] = "test_run",
    artifact: Annotated[str, typer.Option("--artifact", "-a", help="Artifact path")] = "",
    status: Annotated[str, typer.Option("--status", "-s", help="Evidence status")] = "collected",
) -> None:
    """Add evidence to the registry."""
    reg_path, registry = _load()
    evd = Evidence(id=id, test_id=test, kind=kind, artifact_path=artifact, status=status)  # type: ignore[arg-type]
    registry.evidence.append(evd)
    _save_validated(reg_path, registry)
    typer.echo(f"Added evidence {id}")


def _unique_track_id(prefix: str, slug: str, existing: set[str]) -> str:
    base = f"{prefix}:{slug}.track"
    if base not in existing:
        return base
    for i in range(2, 1000):
        candidate = f"{base}.{i}"
        if candidate not in existing:
            return candidate
    raise RuntimeError("too many track IDs")  # pragma: no cover


@app.command("track")
def track_cmd(
    feature_id: Annotated[str, typer.Argument(help="Feature ID (e.g. feat:auth)")],
    test_path: Annotated[str, typer.Argument(help="Test file path (e.g. tests/test_auth.py)")],
    status: Annotated[str, typer.Option("--status", "-s", help="Outcome: passed|failed|collected")] = "passed",
    title: Annotated[str | None, typer.Option("--title", help="Claim title (auto-derived from feature if omitted)")] = None,
    kind: Annotated[str, typer.Option("--kind", "-k", help="Test kind: unit|integration")] = "unit",
) -> None:
    """Auto-create claim, test, and evidence for a feature in one step."""
    path, registry = _load()

    feat_map = {f.id: f for f in registry.features}
    if feature_id not in feat_map:
        typer.echo(
            f"Feature '{feature_id}' not found. Add it first with: verity add feature {feature_id} \"Title\"",
            err=True,
        )
        raise typer.Exit(1)

    if status not in ("passed", "failed", "collected"):
        typer.echo(f"Invalid status '{status}'. Use: passed, failed, or collected", err=True)
        raise typer.Exit(1)

    slug = feature_id.removeprefix("feat:")
    clm_id = _unique_track_id("clm", slug, {c.id for c in registry.claims})
    tst_id = _unique_track_id("tst", slug, {t.id for t in registry.tests})
    evd_id = _unique_track_id("evd", slug, {e.id for e in registry.evidence})

    if status == "passed":
        clm_status, tst_status, evd_status = "verified", "passing", "passed"
    elif status == "failed":
        clm_status, tst_status, evd_status = "open", "failing", "failed"
    else:
        clm_status, tst_status, evd_status = "open", "pending", "collected"

    clm_title = title or feat_map[feature_id].title

    registry.claims.append(Claim(id=clm_id, feature_id=feature_id, title=clm_title, tier="T1", status=clm_status))  # type: ignore[arg-type]
    registry.tests.append(Test(id=tst_id, claim_id=clm_id, kind=kind, path=test_path, status=tst_status))  # type: ignore[arg-type]
    registry.evidence.append(Evidence(id=evd_id, test_id=tst_id, kind="test_run", artifact_path=test_path, status=evd_status))  # type: ignore[arg-type]

    errors = validate(registry)
    if errors:
        for e in errors:
            typer.echo(f"  error: {e}", err=True)
        typer.echo("Registry has validation errors — not saved.", err=True)
        raise typer.Exit(1)
    save_registry(registry, path)

    typer.echo(f"Tracked {feature_id} via {test_path}")
    typer.echo(f"  {clm_id}  ({clm_status})")
    typer.echo(f"  {tst_id}  ({tst_status})")
    typer.echo(f"  {evd_id}  ({evd_status})")


@app.command("validate")
def validate_cmd() -> None:
    """Validate the registry — check all links and required fields."""
    _, registry = _load()
    errors = validate(registry)
    if errors:
        for e in errors:
            typer.echo(f"  {e}")
        typer.echo(f"\n{len(errors)} error(s) found.")
        raise typer.Exit(1)
    typer.echo("OK")


@app.command()
def release(
    version: Annotated[str, typer.Argument(help="Release version (e.g. 0.1.0)")],
) -> None:
    """Create a release snapshot (fail-closed: all verified claims must have passed evidence)."""
    path, registry = _load()
    try:
        rel = create_release(registry, version)
    except VerityReleaseError as e:
        typer.echo(f"Release failed: {e}", err=True)
        raise typer.Exit(1)
    save_registry(registry, path)
    typer.echo(f"Released {rel.id} at {rel.timestamp}")
    typer.echo(f"  claims: {', '.join(rel.claim_ids)}")


@app.command("push")
def push_cmd(
    epochs: Annotated[int, typer.Option("--epochs", help="Walrus storage epochs")] = 5,
    backend_name: BackendChoice = "walrus",
) -> None:
    """Upload registry to Walrus (or MemWal); print blob ID and record it locally."""
    path, registry = _load()
    errors = validate(registry)
    if errors:
        for e in errors:
            typer.echo(f"  error: {e}", err=True)
        typer.echo("Fix validation errors before pushing.", err=True)
        raise typer.Exit(1)

    backend = _get_backend(backend_name, epochs=epochs)
    content = canonical_json(registry).encode("utf-8")

    try:
        blob_id = backend.store(content)
    except (WalrusError, MemWalError) as e:
        typer.echo(f"Push failed: {e}", err=True)
        raise typer.Exit(1)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    registry.pushes.append(PushRecord(blob_id=blob_id, timestamp=timestamp, backend=backend_name))  # type: ignore[arg-type]
    if registry.releases:
        registry.releases[-1].walrus_blob_id = blob_id
    save_registry(registry, path)

    typer.echo(f"blob: {blob_id}")


@app.command("pull")
def pull_cmd(
    blob_id: Annotated[str, typer.Argument(help="Walrus blob ID")],
    directory: Annotated[Path, typer.Option("--dir", help="Target directory")] = Path("."),
    backend_name: BackendChoice = "walrus",
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing verity.json")] = False,
) -> None:
    """Fetch a registry from Walrus (or MemWal) and write it to verity.json."""
    backend = _get_backend(backend_name)

    path = registry_path(directory)
    if not force and path.exists():
        typer.echo(f"Error: {path} already exists. Use --force to overwrite.", err=True)
        raise typer.Exit(1)

    try:
        content = backend.fetch(blob_id)
    except (WalrusError, MemWalError) as e:
        typer.echo(f"Pull failed: {e}", err=True)
        raise typer.Exit(1)

    import json

    registry = Registry.model_validate(json.loads(content))
    path.parent.mkdir(parents=True, exist_ok=True)
    save_registry(registry, path)
    typer.echo(f"Restored registry from {blob_id}")
    typer.echo(
        f"  {len(registry.features)} feature(s), "
        f"{len(registry.claims)} claim(s), "
        f"{len(registry.releases)} release(s)"
    )


TESTNET_AGGREGATOR = "https://aggregator.walrus-testnet.walrus.space"


@app.command("site")
def site_cmd(
    directory: Annotated[Path, typer.Option("--dir", help="Registry directory")] = Path("."),
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Save HTML to file")] = None,
    push: Annotated[bool, typer.Option("--push", help="Push HTML to Walrus and print URL")] = False,
    epochs: Annotated[int, typer.Option("--epochs", help="Walrus storage epochs")] = 5,
) -> None:
    """Generate a human-readable HTML proof page from verity.json."""
    _, registry = _load(directory)
    html = generate_html(registry)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
        typer.echo(f"Saved to {output}")

    if push:
        backend = WalrusBackend(epochs=epochs)
        try:
            blob_id = backend.store(html.encode("utf-8"))
        except WalrusError as e:
            typer.echo(f"Push failed: {e}", err=True)
            raise typer.Exit(1)
        aggregator = os.environ.get("WALRUS_AGGREGATOR_URL", TESTNET_AGGREGATOR)
        url = f"{aggregator.rstrip('/')}/v1/blobs/{blob_id}"
        typer.echo(f"blob: {blob_id}")
        typer.echo(f"url:  {url}")

    if not output and not push:
        typer.echo(html)


@context_app.command("set")
def context_set(
    key: Annotated[str, typer.Argument(help="Context entry key")],
    value: Annotated[str, typer.Argument(help="Context entry value")],
    directory: Annotated[Path, typer.Option("--dir", help="Registry directory")] = Path("."),
) -> None:
    """Set (upsert) a project context entry."""
    path, registry = _load(directory)
    for entry in registry.context:
        if entry.key == key:
            entry.value = value
            save_registry(registry, path)
            typer.echo(f"Updated: {key}")
            return
    registry.context.append(ContextEntry(key=key, value=value))
    save_registry(registry, path)
    typer.echo(f"Set: {key}")


@context_app.command("list")
def context_list(
    directory: Annotated[Path, typer.Option("--dir", help="Registry directory")] = Path("."),
) -> None:
    """List all project context entries."""
    _, registry = _load(directory)
    if not registry.context:
        typer.echo("No context entries. Use 'verity context set KEY VALUE' to add some.")
        return
    for entry in registry.context:
        typer.echo(f"{entry.key}: {entry.value}")


@context_app.command("remove")
def context_remove(
    key: Annotated[str, typer.Argument(help="Context entry key to remove")],
    directory: Annotated[Path, typer.Option("--dir", help="Registry directory")] = Path("."),
) -> None:
    """Remove a context entry by key."""
    path, registry = _load(directory)
    before = len(registry.context)
    registry.context = [e for e in registry.context if e.key != key]
    if len(registry.context) == before:
        typer.echo(f"No entry found with key: {key}", err=True)
        raise typer.Exit(1)
    save_registry(registry, path)
    typer.echo(f"Removed: {key}")


@app.command("status")
def status_cmd(
    directory: Annotated[Path, typer.Argument()] = Path("."),
) -> None:
    """Show a compact health summary of the registry."""
    _, registry = _load(directory)
    errors = validate(registry)

    c_verified = sum(1 for c in registry.claims if c.status == "verified")
    c_open = sum(1 for c in registry.claims if c.status == "open")
    t_passing = sum(1 for t in registry.tests if t.status == "passing")
    t_failing = sum(1 for t in registry.tests if t.status == "failing")
    e_passed = sum(1 for e in registry.evidence if e.status == "passed")
    e_failed = sum(1 for e in registry.evidence if e.status == "failed")

    claim_detail = f"  ({c_verified} verified, {c_open} open)" if registry.claims else ""
    test_detail = (
        f"  ({t_passing} passing, {t_failing} failing)" if t_failing
        else f"  ({t_passing} passing)" if registry.tests
        else ""
    )
    evd_detail = (
        f"  ({e_passed} passed, {e_failed} failed)" if e_failed
        else f"  ({e_passed} passed)" if registry.evidence
        else ""
    )

    latest_rel = registry.releases[-1] if registry.releases else None

    typer.echo(f"{registry.repo_id}  schema {registry.schema_version}")
    typer.echo(f"features   {len(registry.features)}   claims    {len(registry.claims)}{claim_detail}")
    typer.echo(f"tests      {len(registry.tests)}{test_detail}")
    typer.echo(f"evidence   {len(registry.evidence)}{evd_detail}")

    if latest_rel:
        blob_short = (latest_rel.walrus_blob_id[:12] + "…") if latest_rel.walrus_blob_id else "not pushed"
        typer.echo(f"releases   {len(registry.releases)}   latest: {latest_rel.id}  blob: {blob_short}")
    else:
        typer.echo("releases   0")

    if errors:
        typer.echo(f"valid      ✗  ({len(errors)} error(s))")
        raise typer.Exit(1)
    else:
        typer.echo("valid      ✓")


@app.command("log")
def log_cmd() -> None:
    """List all push history for this registry."""
    _, registry = _load()
    if not registry.pushes:
        typer.echo("No pushes recorded yet.")
        return
    for i, record in enumerate(registry.pushes, 1):
        typer.echo(f"{i:3}.  [{record.backend}]  {record.timestamp}  {record.blob_id}")


@app.command("diff")
def diff_cmd(
    blob_a: Annotated[str, typer.Argument(help="First blob ID")],
    blob_b: Annotated[str, typer.Argument(help="Second blob ID")],
    backend: BackendChoice = "walrus",
) -> None:
    """Show what changed between two Walrus blob snapshots of a proof chain."""
    import json as _json

    from verity.diff import diff_registries, format_diff

    b = _get_backend(backend)
    try:
        content_a = b.fetch(blob_a)
        content_b = b.fetch(blob_b)
    except Exception as e:
        typer.echo(f"Fetch failed: {e}", err=True)
        raise typer.Exit(1)
    reg_a = Registry.model_validate(_json.loads(content_a))
    reg_b = Registry.model_validate(_json.loads(content_b))
    typer.echo(format_diff(diff_registries(reg_a, reg_b, blob_a=blob_a, blob_b=blob_b)))


@app.command("export")
def export_cmd(
    format: Annotated[str, typer.Option("--format", "-f", help="Export format: sarif, junit, or spdx")] = "sarif",
    directory: Annotated[Path, typer.Option("--dir", help="Registry directory")] = Path("."),
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file (default: stdout)")] = None,
) -> None:
    """Export the proof chain to a standard DevSecOps format (SARIF, JUnit XML, SPDX)."""
    from verity.export import export

    _, registry = _load(directory)
    try:
        result = export(registry, format)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)
    if output:
        output.write_text(result, encoding="utf-8")
        typer.echo(f"Exported to {output}")
    else:
        typer.echo(result)


@app.command("keygen")
def keygen_cmd(
    key: Annotated[Path, typer.Option("--key", help="Private key output path")] = Path.home() / ".verity" / "signing.key",
    pubkey: Annotated[Path, typer.Option("--pubkey", help="Public key output path")] = Path.home() / ".verity" / "signing.pub",
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing key files")] = False,
) -> None:
    """Generate an Ed25519 signing keypair for signing proof chain blobs."""
    try:
        from verity.signing import generate_keypair, pubkey_to_b64, save_private_key, save_public_key
    except ImportError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)
    if key.exists() and not force:
        typer.echo(f"Key already exists: {key}  (use --force to overwrite)", err=True)
        raise typer.Exit(1)
    priv, pub = generate_keypair()
    save_private_key(priv, key)
    save_public_key(pub, pubkey)
    typer.echo(f"Private key: {key}")
    typer.echo(f"Public key:  {pubkey}")
    typer.echo(f"pubkey-b64:  {pubkey_to_b64(pub)}")


@app.command("sign")
def sign_cmd(
    key: Annotated[Path, typer.Option("--key", help="Path to Ed25519 private key")] = Path.home() / ".verity" / "signing.key",
    directory: Annotated[Path, typer.Option("--dir", help="Registry directory")] = Path("."),
) -> None:
    """Sign the latest push blob with an Ed25519 private key."""
    try:
        from verity.signing import load_private_key, pubkey_to_b64, sign_blob
    except ImportError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)
    path, registry = _load(directory)
    if not registry.pushes:
        typer.echo("No pushes recorded. Run 'verity push' first.", err=True)
        raise typer.Exit(1)
    try:
        priv = load_private_key(key)
    except FileNotFoundError:
        typer.echo(f"Key not found: {key}  (run 'verity keygen' to create one)", err=True)
        raise typer.Exit(1)
    record = registry.pushes[-1]
    sig = sign_blob(record.blob_id, priv)
    pub_b64 = pubkey_to_b64(priv.public_key())
    registry.pushes[-1] = record.model_copy(update={"signature": sig, "signer_pubkey": pub_b64})
    save_registry(registry, path)
    typer.echo(f"Signed blob  {record.blob_id}")
    typer.echo(f"pubkey-b64:  {pub_b64}")


@app.command("verify")
def verify_cmd(
    blob_id: Annotated[str, typer.Argument(help="Walrus blob ID to fetch and verify")],
    pubkey_b64: Annotated[str, typer.Option("--pubkey-b64", help="Base64 public key for signature verification")] = "",
    backend: BackendChoice = "walrus",
) -> None:
    """Fetch a blob from Walrus, validate the chain, and check its signature."""
    import json as _json

    b = _get_backend(backend)
    try:
        content = b.fetch(blob_id)
    except Exception as e:
        typer.echo(f"Fetch failed: {e}", err=True)
        raise typer.Exit(1)
    reg = Registry.model_validate(_json.loads(content))
    errors = validate(reg)
    feat_count = len(reg.features)
    claim_count = len(reg.claims)
    verified_count = sum(1 for c in reg.claims if c.status == "verified")
    test_count = len(reg.tests)
    evd_count = len(reg.evidence)
    typer.echo(f"blob: {blob_id}")
    typer.echo(f"repo: {reg.repo_id}")
    typer.echo(
        f"features {feat_count}  claims {claim_count} ({verified_count} verified)"
        f"  tests {test_count}  evidence {evd_count}"
    )
    if errors:
        for err in errors:
            typer.echo(f"  chain error: {err}", err=True)
        typer.echo("chain invalid ✗", err=True)
        raise typer.Exit(1)
    typer.echo("chain valid ✓")

    # find the most recent signed push record in this chain's history
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
        except ImportError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1)
        if verify_blob(attested_blob, sig, signer):
            typer.echo(f"signature valid ✓   attests: {attested_blob[:16]}…  signer: {signer[:16]}…")
        else:
            typer.echo("signature invalid ✗", err=True)
            raise typer.Exit(1)
    elif pubkey_b64:
        typer.echo("no signature found in push records for this blob", err=True)
        raise typer.Exit(1)


@app.command("recall")
def recall_cmd(
    query: Annotated[str, typer.Argument(help="Natural language question to ask MemWal")],
    namespace: Annotated[str | None, typer.Option("--namespace", "-n", help="MemWal namespace override")] = None,
) -> None:
    """Query MemWal with a natural language question and print the answer."""
    _ns = namespace or os.environ.get("MEMWAL_NAMESPACE", "verity")
    try:
        backend = MemWalBackend(namespace=_ns)
    except MemWalError as e:
        typer.echo(f"MemWal config error: {e}", err=True)
        raise typer.Exit(1)
    try:
        answer = backend.recall(query, namespace=_ns)
    except MemWalError as e:
        typer.echo(f"Recall failed: {e}", err=True)
        raise typer.Exit(1)
    typer.echo(answer)


_SKILL_FILE = Path(__file__).parent.parent / "skills" / "SKILL.md"
_SKILL_MARKER = "<!-- verity-skill -->"
_TOOL_CHOICES = ["claude", "cursor", "windsurf", "aider", "codex"]


def _skill_content() -> str:
    if not _SKILL_FILE.exists():
        typer.echo("Skill file not found in package installation.", err=True)
        raise typer.Exit(1)
    return _SKILL_FILE.read_text(encoding="utf-8")


def _install_claude() -> None:
    claude_md = Path.home() / ".claude" / "CLAUDE.md"
    ref = f"@{_SKILL_FILE.resolve()}"
    if claude_md.exists():
        existing = claude_md.read_text(encoding="utf-8")
        if str(_SKILL_FILE.resolve()) in existing:
            typer.echo("verity skill already installed in ~/.claude/CLAUDE.md")
            return
        claude_md.write_text(existing.rstrip() + f"\n\n# verity\n{ref}\n", encoding="utf-8")
    else:
        claude_md.parent.mkdir(parents=True, exist_ok=True)
        claude_md.write_text(f"# verity\n{ref}\n", encoding="utf-8")
    typer.echo("Installed for Claude Code → ~/.claude/CLAUDE.md")
    typer.echo(f"  {ref}")


def _install_project(tool: str) -> None:
    targets = {
        "cursor": Path(".cursorrules"),
        "windsurf": Path(".windsurfrules"),
        "aider": Path("CONVENTIONS.md"),
        "codex": Path("AGENTS.md"),
    }
    target = targets[tool]
    content = _skill_content()
    block = f"\n\n{_SKILL_MARKER}\n{content}\n"
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if _SKILL_MARKER in existing:
            typer.echo(f"verity skill already installed in {target}")
            return
        target.write_text(existing.rstrip() + block, encoding="utf-8")
    else:
        target.write_text(block.lstrip(), encoding="utf-8")
    typer.echo(f"Installed for {tool} → {target}")


@app.command("install-skill")
def install_skill_cmd(
    tool: Annotated[str, typer.Option("--tool", "-t", help="claude | cursor | windsurf | aider | codex")] = "claude",
) -> None:
    """Install the verity context skill into your AI coding assistant."""
    if tool not in _TOOL_CHOICES:
        typer.echo(f"Unknown tool '{tool}'. Choose from: {', '.join(_TOOL_CHOICES)}", err=True)
        raise typer.Exit(1)
    if tool == "claude":
        _install_claude()
    else:
        _install_project(tool)
