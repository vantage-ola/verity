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
from verity.memwal import MemWalError
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
# status
# ---------------------------------------------------------------------------

def test_status_empty_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--repo-id", "repo:test"])
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "repo:test" in result.stdout
    assert "features   0" in result.stdout
    assert "releases   0" in result.stdout
    assert "valid      ✓" in result.stdout


def test_status_shows_counts_and_breakdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _full_registry(tmp_path)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "features   1" in result.stdout
    assert "claims    1" in result.stdout
    assert "1 verified" in result.stdout
    assert "tests      1" in result.stdout
    assert "1 passing" in result.stdout
    assert "evidence   1" in result.stdout
    assert "1 passed" in result.stdout


def test_status_shows_latest_release(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _full_registry(tmp_path)
    runner.invoke(app, ["release", "1.0.0"])
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "releases   1" in result.stdout
    assert "rel:1.0.0" in result.stdout
    assert "not pushed" in result.stdout


def test_status_shows_blob_when_pushed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _full_registry(tmp_path)
    runner.invoke(app, ["release", "1.0.0"])
    reg_path = tmp_path / "verity.json"
    data = json.loads(reg_path.read_text())
    data["releases"][0]["walrus_blob_id"] = FAKE_BLOB
    reg_path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert FAKE_BLOB[:12] in result.stdout


def test_status_invalid_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    reg_path = tmp_path / "verity.json"
    data = json.loads(reg_path.read_text())
    data["claims"] = [{"id": "clm:x.t1", "feature_id": "feat:missing", "title": "bad", "tier": "T1", "status": "open"}]
    reg_path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "✗" in result.stdout
    assert "error" in result.stdout


def test_status_missing_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "verity init" in result.stderr


# ---------------------------------------------------------------------------
# track
# ---------------------------------------------------------------------------

def test_track_passed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "User auth"])
    result = runner.invoke(app, ["track", "feat:auth", "tests/test_auth.py"])
    assert result.exit_code == 0
    assert "Tracked feat:auth" in result.stdout
    data = json.loads((tmp_path / "verity.json").read_text())
    assert data["claims"][0]["id"] == "clm:auth.track"
    assert data["claims"][0]["status"] == "verified"
    assert data["tests"][0]["status"] == "passing"
    assert data["evidence"][0]["status"] == "passed"


def test_track_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "User auth"])
    result = runner.invoke(app, ["track", "feat:auth", "tests/test_auth.py", "--status", "failed"])
    assert result.exit_code == 0
    data = json.loads((tmp_path / "verity.json").read_text())
    assert data["claims"][0]["status"] == "open"
    assert data["tests"][0]["status"] == "failing"
    assert data["evidence"][0]["status"] == "failed"


def test_track_collected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "User auth"])
    result = runner.invoke(app, ["track", "feat:auth", "tests/test_auth.py", "--status", "collected"])
    assert result.exit_code == 0
    data = json.loads((tmp_path / "verity.json").read_text())
    assert data["claims"][0]["status"] == "open"
    assert data["tests"][0]["status"] == "pending"
    assert data["evidence"][0]["status"] == "collected"


def test_track_feature_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["track", "feat:missing", "tests/test.py"])
    assert result.exit_code == 1
    assert "feat:missing" in result.stderr


def test_track_missing_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["track", "feat:auth", "tests/test.py"])
    assert result.exit_code == 1
    assert "verity init" in result.stderr


def test_track_id_collision_increments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    runner.invoke(app, ["track", "feat:auth", "tests/test_auth.py"])
    result = runner.invoke(app, ["track", "feat:auth", "tests/test_auth2.py"])
    assert result.exit_code == 0
    data = json.loads((tmp_path / "verity.json").read_text())
    claim_ids = [c["id"] for c in data["claims"]]
    assert "clm:auth.track" in claim_ids
    assert "clm:auth.track.2" in claim_ids


def test_track_custom_title(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    runner.invoke(app, ["track", "feat:auth", "tests/test.py", "--title", "My custom claim"])
    data = json.loads((tmp_path / "verity.json").read_text())
    assert data["claims"][0]["title"] == "My custom claim"


def test_track_invalid_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "feature", "feat:auth", "Auth"])
    result = runner.invoke(app, ["track", "feat:auth", "tests/test.py", "--status", "badstatus"])
    assert result.exit_code == 1
    assert "Invalid status" in result.stderr


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
# install-skill
# ---------------------------------------------------------------------------

def test_install_skill_claude_creates_claude_md(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    result = runner.invoke(app, ["install-skill"])
    assert result.exit_code == 0
    assert "Claude Code" in result.stdout
    claude_md = tmp_path / ".claude" / "CLAUDE.md"
    assert claude_md.exists()
    assert "verity" in claude_md.read_text()


def test_install_skill_claude_appends_to_existing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    claude_md = tmp_path / ".claude" / "CLAUDE.md"
    claude_md.parent.mkdir(parents=True)
    claude_md.write_text("# existing content\n")
    runner.invoke(app, ["install-skill"])
    content = claude_md.read_text()
    assert "existing content" in content
    assert "verity" in content


def test_install_skill_claude_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    runner.invoke(app, ["install-skill"])
    result = runner.invoke(app, ["install-skill"])
    assert result.exit_code == 0
    assert "already installed" in result.stdout


def test_install_skill_cursor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install-skill", "--tool", "cursor"])
    assert result.exit_code == 0
    assert "cursor" in result.stdout
    assert (tmp_path / ".cursorrules").exists()


def test_install_skill_windsurf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install-skill", "--tool", "windsurf"])
    assert result.exit_code == 0
    assert (tmp_path / ".windsurfrules").exists()


def test_install_skill_codex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install-skill", "--tool", "codex"])
    assert result.exit_code == 0
    assert (tmp_path / "AGENTS.md").exists()


def test_install_skill_aider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install-skill", "--tool", "aider"])
    assert result.exit_code == 0
    assert (tmp_path / "CONVENTIONS.md").exists()


def test_install_skill_project_appends_to_existing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / ".cursorrules"
    target.write_text("# existing rules\n")
    runner.invoke(app, ["install-skill", "--tool", "cursor"])
    content = target.read_text()
    assert "existing rules" in content
    assert "verity" in content


def test_install_skill_project_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["install-skill", "--tool", "cursor"])
    result = runner.invoke(app, ["install-skill", "--tool", "cursor"])
    assert result.exit_code == 0
    assert "already installed" in result.stdout


def test_install_skill_unknown_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install-skill", "--tool", "vscode"])
    assert result.exit_code == 1
    assert "Unknown tool" in result.stderr or "Unknown tool" in result.stdout


def test_install_skill_missing_skill_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("verity.cli.main._SKILL_FILE", tmp_path / "nonexistent.md")
    result = runner.invoke(app, ["install-skill", "--tool", "cursor"])
    assert result.exit_code == 1
    assert "not found" in result.stderr or "not found" in result.stdout


def test_install_skill_content_includes_proof_chain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["install-skill", "--tool", "codex"])
    content = (tmp_path / "AGENTS.md").read_text()
    assert "feature" in content
    assert "claim" in content
    assert "evidence" in content


# ---------------------------------------------------------------------------
# recall
# ---------------------------------------------------------------------------

def test_recall_cmd_prints_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    with patch("verity.cli.main.MemWalBackend") as MockBackend:
        mock_instance = MagicMock()
        mock_instance.recall.return_value = "You have 2 features: auth, export."
        MockBackend.return_value = mock_instance
        monkeypatch.setenv("MEMWAL_KEY", "0xkey")
        monkeypatch.setenv("MEMWAL_ACCOUNT_ID", "0xacc")
        result = runner.invoke(app, ["recall", "what features have we built"])
    assert result.exit_code == 0
    assert "You have 2 features" in result.stdout


def test_recall_cmd_missing_memwal_key(monkeypatch: pytest.MonkeyPatch) -> None:
    with patch("verity.cli.main.MemWalBackend") as MockBackend:
        MockBackend.side_effect = MemWalError("MemWal key is required")
        result = runner.invoke(app, ["recall", "any query"])
    assert result.exit_code == 1
    assert "config error" in result.output.lower() or "config error" in (result.stderr or "").lower()


def test_recall_cmd_custom_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    with patch("verity.cli.main.MemWalBackend") as MockBackend:
        mock_instance = MagicMock()
        mock_instance.recall.return_value = "answer"
        MockBackend.return_value = mock_instance
        monkeypatch.setenv("MEMWAL_KEY", "0xkey")
        monkeypatch.setenv("MEMWAL_ACCOUNT_ID", "0xacc")
        result = runner.invoke(app, ["recall", "query", "--namespace", "my-project"])
    assert result.exit_code == 0
    call_kwargs = MockBackend.call_args.kwargs
    assert call_kwargs.get("namespace") == "my-project"
    mock_instance.recall.assert_called_once_with("query", namespace="my-project")


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
