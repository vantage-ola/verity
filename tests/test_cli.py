"""
End-to-end CLI tests using typer's CliRunner.

Each test that mutates state calls `monkeypatch.chdir(tmp_path)` so the
commands operate on isolated temporary directories instead of the repo root.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from verity.cli.main import app
from verity.registry import canonical_json
from verity.models import Registry

runner = CliRunner()

FAKE_BLOB = "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcdef"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _full_registry(tmp_path: Path) -> None:
    """Populate tmp_path with a valid registry that can be released."""
    runner.invoke(app, ["init", "--repo-id", "repo:test", str(tmp_path)])
    runner.invoke(app, ["add", "feature", "feat:auth", "User auth"])
    runner.invoke(app, ["add", "claim", "clm:auth.t1", "Login works", "--feature", "feat:auth"])
    runner.invoke(app, ["add", "test", "tst:auth.unit", "Unit", "--claim", "clm:auth.t1", "--kind", "unit", "--path", "t.py"])
    runner.invoke(app, ["add", "evidence", "evd:run1", "Run 1", "--test", "tst:auth.unit", "--artifact", "a.json", "--status", "passed"])
    # patch statuses for release
    reg_path = tmp_path / "verity.json"
    data = json.loads(reg_path.read_text())
    data["claims"][0]["status"] = "verified"
    data["tests"][0]["status"] = "passing"
    reg_path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def test_init_creates_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--repo-id", "repo:ci", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "verity.json").exists()
    assert "Initialized" in result.stdout


def test_init_default_repo_id(tmp_path: Path) -> None:
    runner.invoke(app, ["init", str(tmp_path)])
    data = json.loads((tmp_path / "verity.json").read_text())
    assert data["repo_id"] == "repo:default"


def test_init_fails_if_exists(tmp_path: Path) -> None:
    runner.invoke(app, ["init", str(tmp_path)])
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# add feature
# ---------------------------------------------------------------------------

def test_add_feature(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["add", "feature", "feat:auth", "User auth"])
    assert result.exit_code == 0
    assert "Added feature feat:auth" in result.stdout


def test_add_feature_bad_prefix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["add", "feature", "bad:auth", "Bad"])
    assert result.exit_code == 1


def test_add_feature_no_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    assert result.exit_code == 1
    assert "verity init" in result.stderr


# ---------------------------------------------------------------------------
# add claim
# ---------------------------------------------------------------------------

def test_add_claim(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    result = runner.invoke(app, ["add", "claim", "clm:auth.t1", "Login works", "--feature", "feat:auth"])
    assert result.exit_code == 0
    assert "Added claim clm:auth.t1" in result.stdout


def test_add_claim_broken_link_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["add", "claim", "clm:auth.t1", "Bad", "--feature", "feat:missing"])
    assert result.exit_code == 1
    assert "validation errors" in result.stderr


# ---------------------------------------------------------------------------
# add test
# ---------------------------------------------------------------------------

def test_add_test(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    runner.invoke(app, ["add", "claim", "clm:auth.t1", "C", "--feature", "feat:auth"])
    result = runner.invoke(app, ["add", "test", "tst:auth.unit", "Unit", "--claim", "clm:auth.t1"])
    assert result.exit_code == 0
    assert "Added test tst:auth.unit" in result.stdout


# ---------------------------------------------------------------------------
# add evidence
# ---------------------------------------------------------------------------

def test_add_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    runner.invoke(app, ["add", "claim", "clm:auth.t1", "C", "--feature", "feat:auth"])
    runner.invoke(app, ["add", "test", "tst:auth.unit", "U", "--claim", "clm:auth.t1"])
    result = runner.invoke(app, ["add", "evidence", "evd:run1", "R1", "--test", "tst:auth.unit", "--artifact", "a.json"])
    assert result.exit_code == 0
    assert "Added evidence evd:run1" in result.stdout


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def test_validate_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_validate_broken_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    # add a claim referencing a non-existent feature directly in JSON
    reg_path = tmp_path / "verity.json"
    data = json.loads(reg_path.read_text())
    data["claims"].append({"id": "clm:x.t1", "feature_id": "feat:missing", "title": "bad", "tier": "T1", "status": "open"})
    reg_path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    assert "error(s)" in result.stdout


# ---------------------------------------------------------------------------
# release
# ---------------------------------------------------------------------------

def test_release_succeeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _full_registry(tmp_path)
    result = runner.invoke(app, ["release", "0.1.0"])
    assert result.exit_code == 0
    assert "rel:0.1.0" in result.stdout


def test_release_fails_no_verified_claims(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    runner.invoke(app, ["add", "claim", "clm:auth.t1", "C", "--feature", "feat:auth"])
    result = runner.invoke(app, ["release", "0.1.0"])
    assert result.exit_code == 1
    assert "Release failed" in result.stderr


# ---------------------------------------------------------------------------
# push
# ---------------------------------------------------------------------------

def test_push_walrus_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    body = {"newlyCreated": {"blobObject": {"blobId": FAKE_BLOB}}}
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.put.return_value = _mock_resp(200, body)
        result = runner.invoke(app, ["push"])
    assert result.exit_code == 0
    assert FAKE_BLOB in result.stdout


def test_push_records_in_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    body = {"newlyCreated": {"blobObject": {"blobId": FAKE_BLOB}}}
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.put.return_value = _mock_resp(200, body)
        runner.invoke(app, ["push"])
    result = runner.invoke(app, ["log"])
    assert FAKE_BLOB in result.stdout


def test_push_stores_blob_id_in_release(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _full_registry(tmp_path)
    runner.invoke(app, ["release", "0.1.0"])
    body = {"newlyCreated": {"blobObject": {"blobId": FAKE_BLOB}}}
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.put.return_value = _mock_resp(200, body)
        runner.invoke(app, ["push"])
    data = json.loads((tmp_path / "verity.json").read_text())
    assert data["releases"][0]["walrus_blob_id"] == FAKE_BLOB


def test_push_walrus_error_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.put.return_value = _mock_resp(500, {"error": "down"})
        result = runner.invoke(app, ["push"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# pull
# ---------------------------------------------------------------------------

def test_pull_restores_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    remote_registry = Registry(repo_id="repo:remote")
    content = canonical_json(remote_registry).encode()
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = _mock_get_resp(200, content)
        result = runner.invoke(app, ["pull", FAKE_BLOB])
    assert result.exit_code == 0
    assert "Restored" in result.stdout
    data = json.loads((tmp_path / "verity.json").read_text())
    assert data["repo_id"] == "repo:remote"


def test_pull_error_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = _mock_get_resp(404, b"not found")
        result = runner.invoke(app, ["pull", FAKE_BLOB])
    assert result.exit_code == 1


def test_pull_creates_parent_directory(tmp_path: Path) -> None:
    target = tmp_path / "new" / "nested" / "dir"
    remote_registry = Registry(repo_id="repo:remote")
    content = canonical_json(remote_registry).encode()
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = _mock_get_resp(200, content)
        result = runner.invoke(app, ["pull", FAKE_BLOB, "--dir", str(target)])
    assert result.exit_code == 0
    assert (target / "verity.json").exists()


# ---------------------------------------------------------------------------
# context
# ---------------------------------------------------------------------------

def test_context_set_and_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["context", "set", "arch", "5-layer proof chain"])
    assert result.exit_code == 0
    assert "Set" in result.stdout
    result = runner.invoke(app, ["context", "list"])
    assert "arch" in result.stdout
    assert "5-layer proof chain" in result.stdout


def test_context_set_upserts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["context", "set", "arch", "old value"])
    runner.invoke(app, ["context", "set", "arch", "new value"])
    result = runner.invoke(app, ["context", "list"])
    assert "new value" in result.stdout
    assert "old value" not in result.stdout


def test_context_remove(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["context", "set", "arch", "some text"])
    result = runner.invoke(app, ["context", "remove", "arch"])
    assert result.exit_code == 0
    assert "Removed" in result.stdout
    result = runner.invoke(app, ["context", "list"])
    assert "arch" not in result.stdout


def test_context_remove_missing_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["context", "remove", "nonexistent"])
    assert result.exit_code == 1


def test_context_list_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["context", "list"])
    assert result.exit_code == 0
    assert "No context entries" in result.stdout


def test_context_persisted_in_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["context", "set", "decisions", "chose Option A"])
    data = json.loads((tmp_path / "verity.json").read_text())
    assert any(e["key"] == "decisions" for e in data["context"])


# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------

def test_log_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["log"])
    assert result.exit_code == 0
    assert "No pushes" in result.stdout


def test_log_shows_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    # inject a push record directly
    reg_path = tmp_path / "verity.json"
    data = json.loads(reg_path.read_text())
    data["pushes"] = [{"blob_id": "blob-abc", "timestamp": "2024-01-01T00:00:00Z", "backend": "walrus"}]
    reg_path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    result = runner.invoke(app, ["log"])
    assert "blob-abc" in result.stdout
    assert "walrus" in result.stdout


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _mock_resp(status_code: int, body: dict) -> MagicMock:
    import json as _json
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.text = _json.dumps(body)
    resp.content = _json.dumps(body).encode()
    return resp


def _mock_get_resp(status_code: int, content: bytes) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.text = content.decode(errors="replace")
    return resp
