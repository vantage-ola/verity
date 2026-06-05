"""Tests for the verity MCP server tools."""

from __future__ import annotations

import json
from pathlib import Path


from verity.mcp_server import (
    verity_add_claim,
    verity_add_evidence,
    verity_add_feature,
    verity_add_test,
    verity_diff,
    verity_export,
    verity_init,
    verity_log,
    verity_pull,
    verity_push,
    verity_recall,
    verity_release,
    verity_set_status,
    verity_set_status_batch,
    verity_sign,
    verity_status,
    verity_validate,
    verity_verify,
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


def test_add_claim_bad_prefix(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:auth", "Auth", registry_path=rp)
    result = verity_add_claim("bad:auth.t1", "Login works", feature_id="feat:auth", registry_path=rp)
    assert "Error" in result


def test_add_test(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:auth", "Auth", registry_path=rp)
    verity_add_claim("clm:auth.t1", "Login works", feature_id="feat:auth", registry_path=rp)
    result = verity_add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", registry_path=rp)
    assert "tst:auth.unit" in result


def test_add_test_bad_prefix(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_add_test("bad:unit", claim_id="clm:auth.t1", registry_path=rp)
    assert "Error" in result


def test_add_evidence(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:auth", "Auth", registry_path=rp)
    verity_add_claim("clm:auth.t1", "Login works", feature_id="feat:auth", registry_path=rp)
    verity_add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="t.py", registry_path=rp)
    result = verity_add_evidence("evd:auth.ci", test_id="tst:auth.unit", artifact_path="a.json", registry_path=rp)
    assert "evd:auth.ci" in result


def test_add_evidence_bad_prefix(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_add_evidence("bad:ci", test_id="tst:auth.unit", artifact_path="a.json", registry_path=rp)
    assert "Error" in result


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
# verity_set_status_batch
# ---------------------------------------------------------------------------


def test_set_status_batch_promotes_full_chain(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:x", "X", registry_path=rp)
    verity_add_claim("clm:x.t1", "X works", feature_id="feat:x", registry_path=rp)
    verity_add_test("tst:x.unit", claim_id="clm:x.t1", path="tests/test_x.py", registry_path=rp)
    verity_add_evidence("evd:x.ci", test_id="tst:x.unit", artifact_path="reports/x.json", registry_path=rp)
    result = verity_set_status_batch(
        [
            {"id": "evd:x.ci", "status": "passed"},
            {"id": "tst:x.unit", "status": "passing"},
            {"id": "clm:x.t1", "status": "verified"},
        ],
        registry_path=rp,
    )
    assert "Updated" in result
    assert "evd:x.ci" in result
    assert "clm:x.t1" in result
    assert verity_validate(registry_path=rp) == "OK"


def test_set_status_batch_rejects_all_on_validation_failure(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:x", "X", registry_path=rp)
    verity_add_claim("clm:x.t1", "X works", feature_id="feat:x", registry_path=rp)
    # No test or evidence — verified should be rejected, nothing saved
    result = verity_set_status_batch(
        [{"id": "clm:x.t1", "status": "verified"}],
        registry_path=rp,
    )
    assert "rejected" in result.lower()


def test_set_status_batch_unknown_id(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_set_status_batch(
        [{"id": "clm:ghost", "status": "verified"}],
        registry_path=rp,
    )
    assert "Error" in result


def test_set_status_batch_missing_keys(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_set_status_batch(
        [{"id": "clm:x.t1"}],  # missing "status"
        registry_path=rp,
    )
    assert "Error" in result


# ---------------------------------------------------------------------------
# verity_validate
# ---------------------------------------------------------------------------


def test_validate_clean(tmp_path):
    rp = _build_clean_chain(tmp_path)
    assert verity_validate(registry_path=rp) == "OK"


def test_validate_missing_file(tmp_path):
    result = verity_validate(registry_path=str(tmp_path / "missing.json"))
    assert "Error" in result


def test_validate_returns_errors(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    verity_add_feature("feat:x", "X", registry_path=rp)
    verity_add_claim("clm:x.t1", "X works", feature_id="feat:x", registry_path=rp)
    # break the registry: remove the feature so claim has dangling reference
    data = json.loads(Path(rp).read_text())
    data["features"] = []
    Path(rp).write_text(json.dumps(data))
    result = verity_validate(registry_path=rp)
    assert "Errors:" in result


# ---------------------------------------------------------------------------
# verity_release
# ---------------------------------------------------------------------------


def test_release_success(tmp_path):
    rp = _build_clean_chain(tmp_path)
    result = verity_release("1.0.0", registry_path=rp)
    assert "rel:1.0.0" in result
    assert "1 claim" in result


def test_release_missing_file(tmp_path):
    result = verity_release("1.0.0", registry_path=str(tmp_path / "missing.json"))
    assert "Error" in result


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


def test_log_missing_file(tmp_path):
    result = verity_log(registry_path=str(tmp_path / "missing.json"))
    assert "Error" in result


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
# verity_diff
# ---------------------------------------------------------------------------


def test_verity_diff_happy_path(tmp_path, monkeypatch):
    from unittest.mock import MagicMock
    from verity.models import Registry
    from verity.registry import canonical_json

    reg_a = Registry(repo_id="repo:test")
    reg_b = Registry(repo_id="repo:test")

    responses = {"blobA": canonical_json(reg_a).encode(), "blobB": canonical_json(reg_b).encode()}
    mock_backend = MagicMock()
    mock_backend.fetch.side_effect = lambda key: responses[key]
    monkeypatch.setattr("verity.mcp_server.WalrusBackend", lambda **kw: mock_backend)

    result = verity_diff(blob_a="blobA", blob_b="blobB")
    assert "No changes." in result


def test_verity_diff_fetch_error(monkeypatch):
    from unittest.mock import MagicMock

    mock_backend = MagicMock()
    mock_backend.fetch.side_effect = RuntimeError("network down")
    monkeypatch.setattr("verity.mcp_server.WalrusBackend", lambda **kw: mock_backend)

    result = verity_diff(blob_a="blobA", blob_b="blobB")
    assert result.startswith("Error:")


# ---------------------------------------------------------------------------
# verity_export
# ---------------------------------------------------------------------------


def test_verity_export_sarif(tmp_path):
    rp = _build_clean_chain(tmp_path)
    result = verity_export(format="sarif", registry_path=rp)
    assert "$schema" in result


def test_verity_export_junit(tmp_path):
    rp = _build_clean_chain(tmp_path)
    result = verity_export(format="junit", registry_path=rp)
    assert "<testsuites" in result


def test_verity_export_spdx(tmp_path):
    rp = _build_clean_chain(tmp_path)
    result = verity_export(format="spdx", registry_path=rp)
    assert "SPDX-2.3" in result


def test_verity_export_invalid_format(tmp_path):
    rp = _build_clean_chain(tmp_path)
    result = verity_export(format="csv", registry_path=rp)
    assert result.startswith("Error:")


def test_verity_export_missing_file(tmp_path):
    result = verity_export(registry_path=str(tmp_path / "nope.json"))
    assert result.startswith("Error:")


# ---------------------------------------------------------------------------
# verity_recall
# ---------------------------------------------------------------------------


def test_verity_recall_happy_path(monkeypatch):
    from unittest.mock import MagicMock

    mock_backend = MagicMock()
    mock_backend.recall.return_value = "3 features built."
    monkeypatch.setattr("verity.mcp_server.MemWalBackend", lambda **kw: mock_backend)
    result = verity_recall(query="what features have we built")
    assert "3 features built." in result


def test_verity_recall_exception_returns_error(monkeypatch):
    monkeypatch.setattr(
        "verity.mcp_server.MemWalBackend",
        lambda **kw: (_ for _ in ()).throw(Exception("config missing")),
    )
    result = verity_recall(query="q")
    assert result.startswith("Error:")
    assert "config missing" in result


def test_verity_recall_custom_namespace(monkeypatch):
    from unittest.mock import MagicMock

    mock_backend = MagicMock()
    mock_backend.recall.return_value = "answer"
    captured: dict = {}

    def _fake_backend(**kw):
        captured.update(kw)
        return mock_backend

    monkeypatch.setattr("verity.mcp_server.MemWalBackend", _fake_backend)
    verity_recall(query="q", namespace="proj")
    assert captured.get("namespace") == "proj"
    mock_backend.recall.assert_called_once_with("q", namespace="proj")


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


# ---------------------------------------------------------------------------
# verity_sign
# ---------------------------------------------------------------------------


def test_verity_sign_mcp(tmp_path):
    from datetime import datetime, timezone
    from verity.models import PushRecord, Registry
    from verity.registry import save_registry
    from verity.signing import generate_keypair, save_private_key

    rp = _reg_path(tmp_path)
    reg = Registry(repo_id="repo:test")
    reg.pushes.append(PushRecord(blob_id="TestBlob42", timestamp=datetime.now(timezone.utc).isoformat()))
    save_registry(reg, Path(rp))

    priv, _ = generate_keypair()
    key_path = tmp_path / "signing.key"
    save_private_key(priv, key_path)

    result = verity_sign(key_path=str(key_path), registry_path=rp)
    assert "Signed blob TestBlob42" in result
    assert "pubkey-b64:" in result

    data = json.loads(Path(rp).read_text())
    assert data["pushes"][-1]["signature"] is not None


def test_verity_sign_no_pushes(tmp_path):
    from verity.signing import generate_keypair, save_private_key

    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    priv, _ = generate_keypair()
    key_path = tmp_path / "signing.key"
    save_private_key(priv, key_path)

    result = verity_sign(key_path=str(key_path), registry_path=rp)
    assert "Error" in result
    assert "no pushes" in result.lower()


# ---------------------------------------------------------------------------
# verity_verify
# ---------------------------------------------------------------------------


def test_verity_verify_valid_chain(tmp_path, monkeypatch):
    from verity.models import Registry
    from verity.registry import canonical_json

    reg = Registry(repo_id="repo:test")
    content = canonical_json(reg).encode("utf-8")

    class _FakeBackend:
        def store(self, data): return "blob-verify-test"
        def fetch(self, key): return content

    import verity.mcp_server as srv
    import verity
    monkeypatch.setattr(srv, "WalrusBackend", lambda **kw: _FakeBackend())
    result = verity_verify("blob-verify-test")
    assert "chain valid ✓" in result
    assert "repo:test" in result


def test_verity_sign_missing_registry(tmp_path):
    from verity.signing import generate_keypair, save_private_key
    priv, _ = generate_keypair()
    key_path = tmp_path / "signing.key"
    save_private_key(priv, key_path)
    result = verity_sign(key_path=str(key_path), registry_path=str(tmp_path / "nope.json"))
    assert "Error" in result


def test_verity_sign_missing_key(tmp_path):
    rp = _reg_path(tmp_path)
    verity_init(registry_path=rp)
    result = verity_sign(key_path=str(tmp_path / "nope.key"), registry_path=rp)
    assert "Error" in result


def test_verity_verify_fetch_error(monkeypatch):
    class _BrokenBackend:
        def fetch(self, k): raise Exception("timeout")
    import verity.mcp_server as srv
    monkeypatch.setattr(srv, "WalrusBackend", lambda **kw: _BrokenBackend())
    result = verity_verify("BadBlob")
    assert "Error fetching blob" in result


def test_verity_verify_invalid_chain(monkeypatch):
    from verity.models import Claim, Registry
    from verity.registry import canonical_json
    reg = Registry(
        repo_id="repo:test",
        claims=[Claim(id="clm:x.t1", title="X", feature_id="feat:missing")],
    )
    content = canonical_json(reg).encode("utf-8")
    class _FakeBackend:
        def fetch(self, k): return content
    import verity.mcp_server as srv
    monkeypatch.setattr(srv, "WalrusBackend", lambda **kw: _FakeBackend())
    result = verity_verify("BrokenBlob")
    assert "chain invalid" in result


def test_verity_verify_invalid_signature(monkeypatch):
    from datetime import datetime, timezone
    from verity.models import PushRecord, Registry
    from verity.registry import canonical_json
    from verity.signing import generate_keypair, pubkey_to_b64, sign_blob
    blob_id = "SigBlob888"
    wrong_priv, _ = generate_keypair()
    _, pub = generate_keypair()
    sig = sign_blob(blob_id, wrong_priv)
    reg = Registry(
        repo_id="repo:test",
        pushes=[PushRecord(
            blob_id=blob_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            signature=sig,
            signer_pubkey=pubkey_to_b64(pub),
        )],
    )
    content = canonical_json(reg).encode("utf-8")
    class _FakeBackend:
        def fetch(self, k): return content
    import verity.mcp_server as srv
    monkeypatch.setattr(srv, "WalrusBackend", lambda **kw: _FakeBackend())
    result = verity_verify(blob_id)
    assert "signature invalid" in result


def test_verity_verify_no_sig_with_pubkey(monkeypatch):
    from verity.models import Registry
    from verity.registry import canonical_json
    from verity.signing import generate_keypair, pubkey_to_b64
    reg = Registry(repo_id="repo:test")
    content = canonical_json(reg).encode("utf-8")
    _, pub = generate_keypair()
    class _FakeBackend:
        def fetch(self, k): return content
    import verity.mcp_server as srv
    monkeypatch.setattr(srv, "WalrusBackend", lambda **kw: _FakeBackend())
    result = verity_verify("UnsignedBlob", pubkey_b64=pubkey_to_b64(pub))
    assert "no signature" in result


def test_verity_verify_with_valid_signature(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from verity.models import PushRecord, Registry
    from verity.registry import canonical_json
    from verity.signing import generate_keypair, pubkey_to_b64, sign_blob

    blob_id = "SignedBlob777"
    priv, pub = generate_keypair()
    pub_b64 = pubkey_to_b64(pub)
    sig = sign_blob(blob_id, priv)

    reg = Registry(
        repo_id="repo:test",
        pushes=[PushRecord(
            blob_id=blob_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            signature=sig,
            signer_pubkey=pub_b64,
        )],
    )
    content = canonical_json(reg).encode("utf-8")

    class _FakeBackend:
        def store(self, data): return blob_id
        def fetch(self, key): return content

    import verity.mcp_server as srv
    monkeypatch.setattr(srv, "WalrusBackend", lambda **kw: _FakeBackend())
    result = verity_verify(blob_id, pubkey_b64=pub_b64)
    assert "chain valid ✓" in result
    assert "signature valid ✓" in result
