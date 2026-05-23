from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from verity.models import Claim, Evidence, Feature, Registry, Test
from verity.registry import load_registry, registry_path, save_registry
from verity.release import VerityReleaseError, create_release
from verity.validate import validate

app = typer.Typer(help="verity — proof-chain registry for AI agents")
add_app = typer.Typer(help="Add an entity to the registry")
app.add_typer(add_app, name="add")


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
) -> None:
    """Add a claim to the registry."""
    path, registry = _load()
    claim = Claim(id=id, feature_id=feature, title=title, tier=tier)  # type: ignore[arg-type]
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
) -> None:
    """Add a test to the registry."""
    reg_path, registry = _load()
    test = Test(id=id, claim_id=claim, kind=kind, path=path)  # type: ignore[arg-type]
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
