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
    s.pull("some-blob-id")
    assert s.registry().repo_id == "repo:remote"


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
