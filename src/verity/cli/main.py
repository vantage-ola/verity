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
) -> None:
    """Fetch a registry from Walrus (or MemWal) and write it to verity.json."""
    backend = _get_backend(backend_name)

    try:
        content = backend.fetch(blob_id)
    except (WalrusError, MemWalError) as e:
        typer.echo(f"Pull failed: {e}", err=True)
        raise typer.Exit(1)

    import json

    registry = Registry.model_validate(json.loads(content))
    path = registry_path(directory)
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


@app.command("log")
def log_cmd() -> None:
    """List all push history for this registry."""
    _, registry = _load()
    if not registry.pushes:
        typer.echo("No pushes recorded yet.")
        return
    for i, record in enumerate(registry.pushes, 1):
        typer.echo(f"{i:3}.  [{record.backend}]  {record.timestamp}  {record.blob_id}")


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
