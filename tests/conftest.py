import pytest

from verity.models import Claim, Evidence, Feature, Registry, Test


@pytest.fixture
def minimal_registry() -> Registry:
    feature = Feature(id="feat:auth", title="User authentication")
    claim = Claim(id="clm:auth.t1", feature_id="feat:auth", title="Login works", status="verified")
    test = Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", status="passing")
    evidence = Evidence(
        id="evd:auth.run1",
        test_id="tst:auth.unit",
        artifact_path="artifacts/auth_run1.json",
        status="passed",
    )
    return Registry(
        repo_id="repo:example",
        features=[feature],
        claims=[claim],
        tests=[test],
        evidence=[evidence],
    )
