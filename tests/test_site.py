from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from verity.cli.main import app
from verity.models import PushRecord, Registry
from verity.site import generate_html

runner = CliRunner()

FAKE_BLOB = "site-AbCdEfGhIjKlMnOpQrStUvWxYz"


# ---------------------------------------------------------------------------
# generate_html unit tests
# ---------------------------------------------------------------------------

def test_generate_html_contains_repo_id(minimal_registry: Registry) -> None:
    html = generate_html(minimal_registry)
    assert minimal_registry.repo_id in html


def test_generate_html_contains_features(minimal_registry: Registry) -> None:
    html = generate_html(minimal_registry)
    assert "feat:auth" in html
    assert "User authentication" in html


def test_generate_html_contains_claims(minimal_registry: Registry) -> None:
    html = generate_html(minimal_registry)
    assert "clm:auth.t1" in html
    assert "Login works" in html


def test_generate_html_contains_tests(minimal_registry: Registry) -> None:
    html = generate_html(minimal_registry)
    assert "tst:auth.unit" in html


def test_generate_html_contains_evidence(minimal_registry: Registry) -> None:
    html = generate_html(minimal_registry)
    assert "evd:auth.run1" in html


def test_generate_html_contains_releases() -> None:
    from verity.models import Claim, Evidence, Feature, Registry, Test

    feature = Feature(id="feat:x", title="X feature")
    claim = Claim(id="clm:x.t1", feature_id="feat:x", title="X claim", status="verified")
    test = Test(id="tst:x.unit", claim_id="clm:x.t1", kind="unit", path="", status="passing")
    evidence = Evidence(id="evd:x.run1", test_id="tst:x.unit", artifact_path="", status="passed")
    registry = Registry(
        repo_id="repo:test",
        features=[feature],
        claims=[claim],
        tests=[test],
        evidence=[evidence],
    )
    from verity.release import create_release
    create_release(registry, "1.0.0")
    html = generate_html(registry)
    assert "rel:1.0.0" in html
    assert "v1.0.0" in html


def test_generate_html_contains_push_log(minimal_registry: Registry) -> None:
    minimal_registry.pushes.append(
        PushRecord(blob_id=FAKE_BLOB, timestamp="2026-05-23T12:00:00Z", backend="walrus")
    )
    html = generate_html(minimal_registry)
    assert FAKE_BLOB in html
    assert "walrus" in html


def test_generate_html_is_valid_html(minimal_registry: Registry) -> None:
    html = generate_html(minimal_registry)
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_generate_html_empty_registry() -> None:
    registry = Registry(repo_id="repo:empty")
    html = generate_html(registry)
    assert "repo:empty" in html
    assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# CLI site command
# ---------------------------------------------------------------------------

def test_site_cmd_saves_file(tmp_path: Path, minimal_registry: Registry) -> None:
    verity_dir = tmp_path / "proj"
    verity_dir.mkdir()
    from verity.registry import save_registry, registry_path
    save_registry(minimal_registry, registry_path(verity_dir))

    out_file = tmp_path / "proof.html"
    result = runner.invoke(app, ["site", "--dir", str(verity_dir), "--output", str(out_file)])
    assert result.exit_code == 0, result.output
    assert out_file.exists()
    assert minimal_registry.repo_id in out_file.read_text()


def test_site_cmd_prints_html_when_no_flags(tmp_path: Path, minimal_registry: Registry) -> None:
    from verity.registry import save_registry, registry_path
    save_registry(minimal_registry, registry_path(tmp_path))

    result = runner.invoke(app, ["site", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "<!DOCTYPE html>" in result.output


def test_site_cmd_push(tmp_path: Path, minimal_registry: Registry) -> None:
    from verity.registry import save_registry, registry_path
    save_registry(minimal_registry, registry_path(tmp_path))

    with patch("verity.cli.main.WalrusBackend") as MockBackend:
        MockBackend.return_value.store.return_value = FAKE_BLOB
        result = runner.invoke(app, ["site", "--dir", str(tmp_path), "--push"])

    assert result.exit_code == 0, result.output
    assert FAKE_BLOB in result.output
    assert "url:" in result.output


def test_site_cmd_push_walrus_error(tmp_path: Path, minimal_registry: Registry) -> None:
    from verity.registry import save_registry, registry_path
    from verity.walrus import WalrusError
    save_registry(minimal_registry, registry_path(tmp_path))

    with patch("verity.cli.main.WalrusBackend") as MockBackend:
        MockBackend.return_value.store.side_effect = WalrusError("publisher down")
        result = runner.invoke(app, ["site", "--dir", str(tmp_path), "--push"])

    assert result.exit_code != 0


def test_site_cmd_no_registry(tmp_path: Path) -> None:
    result = runner.invoke(app, ["site", "--dir", str(tmp_path)])
    assert result.exit_code != 0
