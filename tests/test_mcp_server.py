"""Tests for the verity MCP server tools."""

from __future__ import annotations

import json
from pathlib import Path


from verity.mcp_server import (
    verity_add_claim,
    verity_add_evidence,
    verity_add_feature,
    verity_add_test,
    verity_init,
    verity_log,
    verity_pull,
    verity_push,
    verity_release,
    verity_set_status,
    verity_status,
    verity_validate,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _reg_path(tmp_path: Path) -> str:
    return str(tmp_path / "verity.json")


def _build_clean_chain(tmp_path: Path) -> str:
    """Build a fully valid chain and return the registry path."""
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:auth", "Auth", registry_path=rp)
    verity_add_claim("clm:auth.t1", "Login works", feature_id="feat:auth", registry_path=rp)
    verity_add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", registry_path=rp)
    verity_add_evidence("evd:auth.ci", test_id="tst:auth.unit", artifact_path="artifacts/auth.json", registry_path=rp)
    verity_set_status("evd:auth.ci", "passed", registry_path=rp)
    verity_set_status("tst:auth.unit", "passing", registry_path=rp)
    verity_set_status("clm:auth.t1", "verified", registry_path=rp)
    return rp


# ---------------------------------------------------------------------------
# verity_init
# ---------------------------------------------------------------------------


def test_init_creates_registry(tmp_path):
    rp = _reg_path(tmp_path)
    result = verity_init(registry_path=rp)
    assert "Initialised" in result
    assert Path(rp).exists()


def test_init_returns_error_if_exists(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_init(registry_path=rp)
    assert "Error" in result


# ---------------------------------------------------------------------------
# verity_add_feature / claim / test / evidence
# ---------------------------------------------------------------------------


def test_add_feature(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_add_feature("feat:auth", "Auth", registry_path=rp)
    assert "feat:auth" in result


def test_add_feature_bad_prefix(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_add_feature("bad:auth", "Auth", registry_path=rp)
    assert "Error" in result


def test_add_claim(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:auth", "Auth", registry_path=rp)
    result = verity_add_claim("clm:auth.t1", "Login works", feature_id="feat:auth", registry_path=rp)
    assert "clm:auth.t1" in result


def test_add_test(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:auth", "Auth", registry_path=rp)
    verity_add_claim("clm:auth.t1", "Login works", feature_id="feat:auth", registry_path=rp)
    result = verity_add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", registry_path=rp)
    assert "tst:auth.unit" in result


def test_add_evidence(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:auth", "Auth", registry_path=rp)
    verity_add_claim("clm:auth.t1", "Login works", feature_id="feat:auth", registry_path=rp)
    verity_add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="t.py", registry_path=rp)
    result = verity_add_evidence("evd:auth.ci", test_id="tst:auth.unit", artifact_path="a.json", registry_path=rp)
    assert "evd:auth.ci" in result


# ---------------------------------------------------------------------------
# verity_set_status
# ---------------------------------------------------------------------------


def test_set_status_promotes_chain(tmp_path):
    rp = _build_clean_chain(tmp_path)
    # after _build_clean_chain statuses are already promoted; verify validate passes
    result = verity_validate(registry_path=rp)
    assert result == "OK"


def test_set_status_unknown_id(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_set_status("clm:nonexistent", "verified", registry_path=rp)
    assert "Error" in result or "no entity" in result


def test_set_status_rejects_premature_verified(tmp_path):
    """Setting claim to verified before test+evidence exist should fail validation."""
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:x", "X", registry_path=rp)
    verity_add_claim("clm:x.t1", "X works", feature_id="feat:x", registry_path=rp)
    # No test or evidence — trying to set verified should be rejected
    result = verity_set_status("clm:x.t1", "verified", registry_path=rp)
    assert "rejected" in result.lower() or "error" in result.lower()


# ---------------------------------------------------------------------------
# verity_validate
# ---------------------------------------------------------------------------


def test_validate_clean(tmp_path):
    rp = _build_clean_chain(tmp_path)
    assert verity_validate(registry_path=rp) == "OK"


def test_validate_missing_file(tmp_path):
    result = verity_validate(registry_path=str(tmp_path / "missing.json"))
    assert "Error" in result


# ---------------------------------------------------------------------------
# verity_release
# ---------------------------------------------------------------------------


def test_release_success(tmp_path):
    rp = _build_clean_chain(tmp_path)
    result = verity_release("1.0.0", registry_path=rp)
    assert "rel:1.0.0" in result
    assert "1 claim" in result


def test_release_fails_without_verified_claims(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:x", "X", registry_path=rp)
    verity_add_claim("clm:x.t1", "X works", feature_id="feat:x", status="open", registry_path=rp)
    result = verity_release("1.0.0", registry_path=rp)
    assert "failed" in result.lower()


# ---------------------------------------------------------------------------
# verity_push
# ---------------------------------------------------------------------------


def test_push_error_without_backend(tmp_path):
    rp = _build_clean_chain(tmp_path)
    # no WALRUS_PUBLISHER_URL env var → no backend → error
    result = verity_push(registry_path=rp)
    assert "Error" in result


def test_push_with_mock_backend(tmp_path, monkeypatch):
    rp = _build_clean_chain(tmp_path)
    verity_release("1.0.0", registry_path=rp)

    class _MockBackend:
        def store(self, content: bytes) -> str:
            return "blob-mock-123"

        def fetch(self, key: str) -> bytes:
            return b""

    import verity.mcp_server as srv

    monkeypatch.setattr(srv, "_session", lambda path: __import__("verity").VeritySession(path, backend=_MockBackend()))
    result = verity_push(registry_path=rp)
    assert "blob-mock-123" in result


# ---------------------------------------------------------------------------
# verity_log
# ---------------------------------------------------------------------------


def test_log_empty(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_log(registry_path=rp)
    assert "No pushes" in result


# ---------------------------------------------------------------------------
# verity_status
# ---------------------------------------------------------------------------


def test_status_counts(tmp_path):
    rp = _build_clean_chain(tmp_path)
    result = verity_status(registry_path=rp)
    assert "features:  1" in result
    assert "claims:    1" in result
    assert "tests:     1" in result
    assert "evidence:  1" in result
    assert "valid:     yes" in result


def test_status_missing_file(tmp_path):
    result = verity_status(registry_path=str(tmp_path / "nope.json"))
    assert "Error" in result


# ---------------------------------------------------------------------------
# verity_pull
# ---------------------------------------------------------------------------


def test_pull_error_without_backend(tmp_path):
    result = verity_pull("blob-abc", registry_path=_reg_path(tmp_path))
    assert "Error" in result


def test_pull_with_mock_backend(tmp_path, monkeypatch):
    rp = _build_clean_chain(tmp_path)
    verity_release("1.0.0", registry_path=rp)

    from verity import load_registry
    from verity.registry import canonical_json

    reg = load_registry(Path(rp))
    payload = canonical_json(reg).encode()

    class _MockBackend:
        def store(self, content: bytes) -> str:
            return "blob-pull-test"

        def fetch(self, key: str) -> bytes:
            return payload

    import verity.mcp_server as srv
    import verity

    monkeypatch.setattr(srv, "_session", lambda path: verity.VeritySession(path, backend=_MockBackend()))
    result = verity_pull("blob-pull-test", registry_path=rp)
    assert "blob-pull-test" in result


# ---------------------------------------------------------------------------
# _session with env vars
# ---------------------------------------------------------------------------


def test_session_creates_walrus_backend_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("WALRUS_PUBLISHER_URL", "http://publisher.example")
    monkeypatch.setenv("WALRUS_AGGREGATOR_URL", "http://aggregator.example")
    from verity.mcp_server import _session

    s = _session(str(tmp_path / "v.json"))
    assert s._backend is not None


# ---------------------------------------------------------------------------
# verity_log with entries
# ---------------------------------------------------------------------------


def test_log_with_entries(tmp_path, monkeypatch):
    rp = _build_clean_chain(tmp_path)
    verity_release("1.0.0", registry_path=rp)

    class _MockBackend:
        def store(self, content: bytes) -> str:
            return "blob-log-test"

        def fetch(self, key: str) -> bytes:
            return b""

    import verity.mcp_server as srv
    import verity

    monkeypatch.setattr(srv, "_session", lambda path: verity.VeritySession(path, backend=_MockBackend()))
    verity_push(registry_path=rp)
    result = verity_log(registry_path=rp)
    assert "blob-log-test" in result


# ---------------------------------------------------------------------------
# verity_status with invalid registry
# ---------------------------------------------------------------------------


def test_status_shows_invalid(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:x", "X", registry_path=rp)
    # claim references a non-existent feature
    verity_add_claim("clm:x.t1", "X works", feature_id="feat:x", registry_path=rp)
    # break the registry by removing the feature inline
    data = json.loads(Path(rp).read_text())
    data["features"] = []
    Path(rp).write_text(json.dumps(data))
    result = verity_status(registry_path=rp)
    assert "no" in result or "error" in result.lower()
