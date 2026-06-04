"""Tests for verity.diff — diff_registries()."""

from __future__ import annotations

from verity.diff import diff_registries
from verity.models import Claim, Evidence, Feature, Registry, Test


def _base_registry() -> Registry:
    return Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="Auth")],
        claims=[Claim(id="clm:auth.t1", title="Login succeeds", feature_id="feat:auth", status="open")],
        tests=[Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", status="pending")],
        evidence=[],
        releases=[],
    )


def test_diff_no_changes() -> None:
    reg = _base_registry()
    result = diff_registries(reg, reg)
    assert "No changes." in result


def test_diff_added_feature() -> None:
    a = _base_registry()
    b = _base_registry()
    b.features = list(a.features) + [Feature(id="feat:new", title="New feature")]
    result = diff_registries(a, b)
    assert "+ feat:new" in result


def test_diff_removed_claim() -> None:
    a = _base_registry()
    b = _base_registry()
    b.claims = []
    result = diff_registries(a, b)
    assert "- clm:auth.t1" in result


def test_diff_status_change() -> None:
    a = _base_registry()
    b = _base_registry()
    b.tests = [
        Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", status="passing")
    ]
    result = diff_registries(a, b)
    assert "~ tst:auth.unit" in result
    assert "pending → passing" in result


def test_diff_header_shows_blobs() -> None:
    reg = _base_registry()
    result = diff_registries(reg, reg, blob_a="blobAAA", blob_b="blobBBB")
    assert "blobAAA" in result
    assert "blobBBB" in result


def test_diff_summary_counts() -> None:
    a = _base_registry()
    b = _base_registry()
    b.features = list(a.features) + [
        Feature(id="feat:x", title="X"),
        Feature(id="feat:y", title="Y"),
    ]
    b.claims = []  # 1 removed
    result = diff_registries(a, b)
    assert "2 added" in result
    assert "1 removed" in result


def test_diff_multiple_families() -> None:
    a = _base_registry()
    b = _base_registry()
    b.features = list(a.features) + [Feature(id="feat:extra", title="Extra")]
    b.claims = [Claim(id="clm:auth.t1", title="Login succeeds", feature_id="feat:auth", status="verified")]
    b.evidence = [Evidence(id="evd:auth.ci", test_id="tst:auth.unit", artifact_path="ci.json", status="passed")]
    result = diff_registries(a, b)
    assert "+ feat:extra" in result
    assert "~ clm:auth.t1" in result
    assert "open → verified" in result
    assert "+ evd:auth.ci" in result
