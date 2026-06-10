from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from verity.models import Registry
from verity.session import VerityPushError, VeritySession


@pytest.fixture
def tmp_session(tmp_path: Path) -> VeritySession:
    s = VeritySession(tmp_path / "verity.json")
    s.init(repo_id="repo:test")
    return s


def test_init_creates_file(tmp_path: Path) -> None:
    s = VeritySession(tmp_path / "verity.json")
    s.init(repo_id="repo:test")
    assert (tmp_path / "verity.json").exists()


def test_init_raises_if_exists(tmp_session: VeritySession) -> None:
    with pytest.raises(FileExistsError):
        tmp_session.init()


def test_add_feature(tmp_session: VeritySession) -> None:
    f = tmp_session.add_feature("feat:auth", "User auth")
    assert f.id == "feat:auth"
    assert tmp_session.registry().features[0].id == "feat:auth"


def test_add_claim(tmp_session: VeritySession) -> None:
    tmp_session.add_feature("feat:auth", "Auth")
    c = tmp_session.add_claim("clm:auth.t1", "Login works", feature_id="feat:auth")
    assert c.feature_id == "feat:auth"


def test_add_test(tmp_session: VeritySession) -> None:
    tmp_session.add_feature("feat:auth", "Auth")
    tmp_session.add_claim("clm:auth.t1", "Login", feature_id="feat:auth")
    t = tmp_session.add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/t.py")
    assert t.kind == "unit"


def test_add_evidence(tmp_session: VeritySession) -> None:
    tmp_session.add_feature("feat:auth", "Auth")
    tmp_session.add_claim("clm:auth.t1", "Login", feature_id="feat:auth")
    tmp_session.add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit")
    e = tmp_session.add_evidence("evd:run1", test_id="tst:auth.unit", artifact_path="a.json")
    assert e.status == "collected"


def test_validate_clean(tmp_session: VeritySession) -> None:
    tmp_session.add_feature("feat:auth", "Auth")
    assert tmp_session.validate() == []


def test_validate_broken_link(tmp_session: VeritySession) -> None:
    tmp_session.add_claim("clm:auth.t1", "No feature", feature_id="feat:missing")
    errors = tmp_session.validate()
    assert any("feat:missing" in e for e in errors)


def test_release_via_session(tmp_path: Path) -> None:
    s = VeritySession(tmp_path / "verity.json")
    s.init()
    s.add_feature("feat:auth", "Auth")
    s.add_claim("clm:auth.t1", "Login", feature_id="feat:auth", status="verified")
    s.add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="t.py", status="passing")
    s.add_evidence("evd:run1", test_id="tst:auth.unit", artifact_path="a.json", status="passed")
    rel = s.release("0.1.0")
    assert rel.version == "0.1.0"
    assert "clm:auth.t1" in rel.claim_ids


def test_push_no_backend_raises(tmp_session: VeritySession) -> None:
    with pytest.raises(VerityPushError, match="No storage backend"):
        tmp_session.push()


def test_push_with_mock_backend(tmp_session: VeritySession) -> None:
    backend = MagicMock()
    backend.store.return_value = "fake-blob-id-abc123"
    s = VeritySession(tmp_session.path, backend=backend)
    tmp_session.add_feature("feat:auth", "Auth")

    blob_id = s.push()
    assert blob_id == "fake-blob-id-abc123"
    backend.store.assert_called_once()


def test_push_records_push_history(tmp_session: VeritySession) -> None:
    backend = MagicMock()
    backend.store.return_value = "blob-xyz"
    s = VeritySession(tmp_session.path, backend=backend)
    s.push()
    records = s.log()
    assert len(records) == 1
    assert records[0].blob_id == "blob-xyz"


def test_push_updates_latest_release(tmp_path: Path) -> None:
    s = VeritySession(tmp_path / "verity.json")
    s.init()
    s.add_feature("feat:a", "A")
    s.add_claim("clm:a.t1", "C", feature_id="feat:a", status="verified")
    s.add_test("tst:a.unit", claim_id="clm:a.t1", kind="unit", path="t.py", status="passing")
    s.add_evidence("evd:a.run1", test_id="tst:a.unit", artifact_path="a.json", status="passed")
    s.release("1.0.0")

    backend = MagicMock()
    backend.store.return_value = "blob-release"
    s2 = VeritySession(tmp_path / "verity.json", backend=backend)
    s2.push()
    assert s2.registry().releases[-1].walrus_blob_id == "blob-release"


def test_pull_with_mock_backend(tmp_session: VeritySession) -> None:

    from verity.registry import canonical_json

    target = Registry(repo_id="repo:remote", features=[])
    backend = MagicMock()
    backend.fetch.return_value = canonical_json(target).encode()
    s = VeritySession(tmp_session.path, backend=backend)
    s.pull("some-blob-id", force=True)
    assert s.registry().repo_id == "repo:remote"


def test_pull_raises_if_file_exists(tmp_session: VeritySession) -> None:
    backend = MagicMock()
    s = VeritySession(tmp_session.path, backend=backend)
    with pytest.raises(FileExistsError, match="force=True"):
        s.pull("some-blob-id")


def test_pull_force_overwrites(tmp_session: VeritySession) -> None:
    from verity.registry import canonical_json

    target = Registry(repo_id="repo:overwritten", features=[])
    backend = MagicMock()
    backend.fetch.return_value = canonical_json(target).encode()
    s = VeritySession(tmp_session.path, backend=backend)
    s.pull("some-blob-id", force=True)
    assert s.registry().repo_id == "repo:overwritten"


def test_pull_no_error_when_file_missing(tmp_path: VeritySession) -> None:
    from verity.registry import canonical_json

    target = Registry(repo_id="repo:fresh", features=[])
    backend = MagicMock()
    backend.fetch.return_value = canonical_json(target).encode()
    path = tmp_path / "new.json"
    s = VeritySession(str(path), backend=backend)
    s.pull("some-blob-id")  # no force needed — file doesn't exist
    assert path.exists()


def test_log_empty(tmp_session: VeritySession) -> None:
    assert tmp_session.log() == []


def test_multiple_pushes_log(tmp_session: VeritySession) -> None:
    backend = MagicMock()
    backend.store.side_effect = ["blob-1", "blob-2"]
    s = VeritySession(tmp_session.path, backend=backend)
    s.push()
    s.push()
    records = s.log()
    assert len(records) == 2
    assert records[0].blob_id == "blob-1"
    assert records[1].blob_id == "blob-2"


# ---------------------------------------------------------------------------
# context
# ---------------------------------------------------------------------------

def test_set_context_persists(tmp_session: VeritySession) -> None:
    tmp_session.set_context("arch", "5-layer proof chain")
    assert tmp_session.get_context("arch") == "5-layer proof chain"


def test_set_context_upserts(tmp_session: VeritySession) -> None:
    tmp_session.set_context("arch", "old")
    tmp_session.set_context("arch", "new")
    assert tmp_session.get_context("arch") == "new"
    assert len(tmp_session.registry().context) == 1


def test_get_context_missing_returns_none(tmp_session: VeritySession) -> None:
    assert tmp_session.get_context("missing") is None


def test_remove_context_returns_true_when_found(tmp_session: VeritySession) -> None:
    tmp_session.set_context("k", "v")
    assert tmp_session.remove_context("k") is True
    assert tmp_session.get_context("k") is None


def test_remove_context_returns_false_when_missing(tmp_session: VeritySession) -> None:
    assert tmp_session.remove_context("nonexistent") is False


def test_context_survives_round_trip(tmp_session: VeritySession) -> None:
    tmp_session.set_context("decisions", "chose Option A for MemWal")
    tmp_session.set_context("stack", "python + walrus + pydantic")
    reg = tmp_session.registry()
    assert len(reg.context) == 2
    assert reg.context[1].key == "stack"


# ---------------------------------------------------------------------------
# status literal validation
# ---------------------------------------------------------------------------

def test_add_feature_bad_status(tmp_session: VeritySession) -> None:
    with pytest.raises(ValueError, match="feature status"):
        tmp_session.add_feature("feat:x", "X", status="verifed")


def test_add_claim_bad_status(tmp_session: VeritySession) -> None:
    tmp_session.add_feature("feat:x", "X")
    with pytest.raises(ValueError, match="claim status"):
        tmp_session.add_claim("clm:x.t1", "X", feature_id="feat:x", status="verifed")


def test_add_test_bad_status(tmp_session: VeritySession) -> None:
    tmp_session.add_feature("feat:x", "X")
    tmp_session.add_claim("clm:x.t1", "X", feature_id="feat:x")
    with pytest.raises(ValueError, match="test status"):
        tmp_session.add_test("tst:x.unit", claim_id="clm:x.t1", status="passin")


def test_add_evidence_bad_status(tmp_session: VeritySession) -> None:
    tmp_session.add_feature("feat:x", "X")
    tmp_session.add_claim("clm:x.t1", "X", feature_id="feat:x")
    tmp_session.add_test("tst:x.unit", claim_id="clm:x.t1")
    with pytest.raises(ValueError, match="evidence status"):
        tmp_session.add_evidence("evd:x.ci", test_id="tst:x.unit", artifact_path="a.json", status="passd")


# ---------------------------------------------------------------------------
# upload_artifacts
# ---------------------------------------------------------------------------

def test_upload_artifacts_rewrites_paths(tmp_path: Path) -> None:
    s = VeritySession(tmp_path / "verity.json")
    s.init(repo_id="repo:test")
    s.add_feature("feat:x", "X")
    s.add_claim("clm:x.t1", "X", feature_id="feat:x")
    s.add_test("tst:x.unit", claim_id="clm:x.t1")
    artifact = tmp_path / "ci.json"
    artifact.write_text('{"result": "passed"}')
    s.add_evidence("evd:x.ci", test_id="tst:x.unit", artifact_path=str(artifact))

    backend = MagicMock()
    backend.store.return_value = "artifact-blob-id"
    s._backend = backend

    uploaded = s.upload_artifacts()

    assert uploaded == {"evd:x.ci": "artifact-blob-id"}
    reg = s.registry()
    assert reg.evidence[0].artifact_path == "walrus://artifact-blob-id"
    backend.store.assert_called_once_with(b'{"result": "passed"}')


def test_upload_artifacts_skips_walrus_paths(tmp_path: Path) -> None:
    s = VeritySession(tmp_path / "verity.json")
    s.init(repo_id="repo:test")
    s.add_feature("feat:x", "X")
    s.add_claim("clm:x.t1", "X", feature_id="feat:x")
    s.add_test("tst:x.unit", claim_id="clm:x.t1")
    s.add_evidence("evd:x.ci", test_id="tst:x.unit", artifact_path="walrus://existing-blob")

    backend = MagicMock()
    s._backend = backend

    uploaded = s.upload_artifacts()

    assert uploaded == {}
    backend.store.assert_not_called()
    assert s.registry().evidence[0].artifact_path == "walrus://existing-blob"


def test_upload_artifacts_skips_missing_files(tmp_path: Path) -> None:
    s = VeritySession(tmp_path / "verity.json")
    s.init(repo_id="repo:test")
    s.add_feature("feat:x", "X")
    s.add_claim("clm:x.t1", "X", feature_id="feat:x")
    s.add_test("tst:x.unit", claim_id="clm:x.t1")
    s.add_evidence("evd:x.ci", test_id="tst:x.unit", artifact_path="nonexistent.json")

    backend = MagicMock()
    s._backend = backend

    uploaded = s.upload_artifacts()

    assert uploaded == {}
    backend.store.assert_not_called()
    assert s.registry().evidence[0].artifact_path == "nonexistent.json"
