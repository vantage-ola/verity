import pytest

from verity.models import Claim, Evidence, Feature, Registry, Test
from verity.release import VerityReleaseError, create_release


def test_release_succeeds(minimal_registry):
    release = create_release(minimal_registry, "0.1.0")
    assert release.id == "rel:0.1.0"
    assert release.version == "0.1.0"
    assert "clm:auth.t1" in release.claim_ids
    assert release.walrus_blob_id is None
    assert release in minimal_registry.releases


def test_release_appends_to_registry(minimal_registry):
    assert len(minimal_registry.releases) == 0
    create_release(minimal_registry, "0.1.0")
    assert len(minimal_registry.releases) == 1


def test_release_fails_no_verified_claims():
    registry = Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="Auth")],
        claims=[Claim(id="clm:auth.t1", feature_id="feat:auth", title="Open claim", status="open")],
    )
    with pytest.raises(VerityReleaseError, match="No verified claims"):
        create_release(registry, "0.1.0")


def test_release_fails_verified_claim_no_tests():
    registry = Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="Auth")],
        claims=[Claim(id="clm:auth.t1", feature_id="feat:auth", title="Verified but no test", status="verified")],
    )
    with pytest.raises(VerityReleaseError, match="no linked tests"):
        create_release(registry, "0.1.0")


def test_release_fails_no_passed_evidence():
    registry = Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="Auth")],
        claims=[Claim(id="clm:auth.t1", feature_id="feat:auth", title="Verified", status="verified")],
        tests=[Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="t.py")],
        evidence=[
            Evidence(id="evd:run1", test_id="tst:auth.unit", artifact_path="a.json", status="failed")
        ],
    )
    with pytest.raises(VerityReleaseError, match="no test with passed evidence"):
        create_release(registry, "0.1.0")


def test_release_timestamp_format(minimal_registry):
    release = create_release(minimal_registry, "1.0.0")
    assert release.timestamp.endswith("Z")
    assert "T" in release.timestamp
