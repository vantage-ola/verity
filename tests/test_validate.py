from verity.models import Claim, Evidence, Feature, Registry, Test
from verity.validate import validate


def test_clean_registry_passes(minimal_registry):
    assert validate(minimal_registry) == []


def test_broken_claim_feature_link():
    registry = Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="Auth")],
        claims=[Claim(id="clm:auth.t1", feature_id="feat:missing", title="Bad link")],
    )
    errors = validate(registry)
    assert any("feat:missing" in e for e in errors)


def test_broken_test_claim_link():
    registry = Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="Auth")],
        claims=[Claim(id="clm:auth.t1", feature_id="feat:auth", title="Good")],
        tests=[Test(id="tst:auth.unit", claim_id="clm:missing", kind="unit", path="tests/t.py")],
    )
    errors = validate(registry)
    assert any("clm:missing" in e for e in errors)


def test_broken_evidence_test_link():
    registry = Registry(
        repo_id="repo:test",
        evidence=[Evidence(id="evd:run1", test_id="tst:missing", artifact_path="a.json")],
    )
    errors = validate(registry)
    assert any("tst:missing" in e for e in errors)


def test_duplicate_feature_ids():
    f = Feature(id="feat:auth", title="Auth")
    registry = Registry(repo_id="repo:test", features=[f, f])
    errors = validate(registry)
    assert any("Duplicate" in e and "feat:auth" in e for e in errors)


def test_verified_claim_without_tests():
    registry = Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="Auth")],
        claims=[Claim(id="clm:auth.t1", feature_id="feat:auth", title="No tests", status="verified")],
    )
    errors = validate(registry)
    assert any("verified" in e and "clm:auth.t1" in e for e in errors)


def test_passing_test_without_evidence():
    registry = Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="Auth")],
        claims=[Claim(id="clm:auth.t1", feature_id="feat:auth", title="C")],
        tests=[Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="t.py", status="passing")],
    )
    errors = validate(registry)
    assert any("passing" in e and "tst:auth.unit" in e for e in errors)
