import pytest
from pydantic import ValidationError

from verity.models import Claim, ContextEntry, Evidence, Feature, Registry, Release, Test


def test_feature_valid():
    f = Feature(id="feat:auth", title="Auth")
    assert f.status == "active"


def test_feature_bad_prefix():
    with pytest.raises(ValidationError, match="feat:"):
        Feature(id="auth:foo", title="Bad")


def test_feature_extra_field_rejected():
    with pytest.raises(ValidationError):
        Feature(id="feat:auth", title="Auth", extra_field="oops")


def test_claim_valid():
    c = Claim(id="clm:auth.t1", feature_id="feat:auth", title="Login works")
    assert c.tier == "T1"
    assert c.status == "open"


def test_claim_bad_prefix():
    with pytest.raises(ValidationError, match="clm:"):
        Claim(id="claim:auth", feature_id="feat:auth", title="Bad")


def test_test_valid():
    t = Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py")
    assert t.status == "pending"


def test_test_bad_kind():
    with pytest.raises(ValidationError):
        Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="smoke", path="tests/test_auth.py")


def test_evidence_valid():
    e = Evidence(id="evd:auth.run1", test_id="tst:auth.unit", artifact_path="artifacts/run1.json")
    assert e.kind == "test_run"
    assert e.status == "collected"


def test_evidence_bad_prefix():
    with pytest.raises(ValidationError, match="evd:"):
        Evidence(id="evidence:foo", test_id="tst:auth.unit", artifact_path="artifacts/run1.json")


def test_release_valid():
    r = Release(id="rel:0.1.0", version="0.1.0", timestamp="2024-01-01T00:00:00Z")
    assert r.walrus_blob_id is None


def test_release_bad_prefix():
    with pytest.raises(ValidationError, match="rel:"):
        Release(id="release:0.1.0", version="0.1.0", timestamp="2024-01-01T00:00:00Z")


def test_registry_defaults():
    r = Registry(repo_id="repo:test")
    assert r.schema_version == "0.1.0"
    assert r.features == []
    assert r.releases == []
    assert r.context == []


def test_context_entry_valid():
    e = ContextEntry(key="arch", value="5-layer proof chain")
    assert e.key == "arch"
    assert e.value == "5-layer proof chain"


def test_context_entry_extra_field_rejected():
    with pytest.raises(ValidationError):
        ContextEntry(key="arch", value="v", extra="nope")  # type: ignore[call-arg]


def test_registry_with_context():
    r = Registry(repo_id="repo:test", context=[ContextEntry(key="k", value="v")])
    assert r.context[0].key == "k"
    assert r.context[0].value == "v"
