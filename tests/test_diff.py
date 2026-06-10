"""Tests for verity.diff — diff_registries() and format_diff()."""

from __future__ import annotations

from verity.diff import DiffResult, diff_registries, format_diff
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


# --- DiffResult structure ---

def test_diff_returns_diff_result() -> None:
    reg = _base_registry()
    result = diff_registries(reg, reg)
    assert isinstance(result, DiffResult)


def test_diff_result_stores_blob_ids() -> None:
    reg = _base_registry()
    result = diff_registries(reg, reg, blob_a="blobAAA", blob_b="blobBBB")
    assert result.blob_a == "blobAAA"
    assert result.blob_b == "blobBBB"


def test_diff_result_stores_repo_ids() -> None:
    reg = _base_registry()
    result = diff_registries(reg, reg)
    assert result.repo_a == "repo:test"
    assert result.repo_b == "repo:test"


def test_diff_no_changes_empty_entries() -> None:
    reg = _base_registry()
    result = diff_registries(reg, reg)
    assert result.entries == []
    assert result.added == []
    assert result.removed == []
    assert result.changed == []


def test_diff_added_feature_entry() -> None:
    a = _base_registry()
    b = _base_registry()
    b.features = list(a.features) + [Feature(id="feat:new", title="New feature")]
    result = diff_registries(a, b)
    added = result.added
    assert len(added) == 1
    assert added[0].id == "feat:new"
    assert added[0].kind == "added"
    assert added[0].family == "features"


def test_diff_removed_claim_entry() -> None:
    a = _base_registry()
    b = _base_registry()
    b.claims = []
    result = diff_registries(a, b)
    removed = result.removed
    assert len(removed) == 1
    assert removed[0].id == "clm:auth.t1"
    assert removed[0].kind == "removed"
    assert removed[0].family == "claims"


def test_diff_status_change_entry() -> None:
    a = _base_registry()
    b = _base_registry()
    b.tests = [
        Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", status="passing")
    ]
    result = diff_registries(a, b)
    changed = result.changed
    assert len(changed) == 1
    assert changed[0].id == "tst:auth.unit"
    assert changed[0].kind == "changed"
    assert "pending → passing" in changed[0].change


def test_diff_summary_counts() -> None:
    a = _base_registry()
    b = _base_registry()
    b.features = list(a.features) + [
        Feature(id="feat:x", title="X"),
        Feature(id="feat:y", title="Y"),
    ]
    b.claims = []  # 1 removed
    result = diff_registries(a, b)
    assert len(result.added) == 2
    assert len(result.removed) == 1
    assert len(result.changed) == 0


def test_diff_multiple_families() -> None:
    a = _base_registry()
    b = _base_registry()
    b.features = list(a.features) + [Feature(id="feat:extra", title="Extra")]
    b.claims = [Claim(id="clm:auth.t1", title="Login succeeds", feature_id="feat:auth", status="verified")]
    b.evidence = [Evidence(id="evd:auth.ci", test_id="tst:auth.unit", artifact_path="ci.json", status="passed")]
    result = diff_registries(a, b)
    ids = [e.id for e in result.entries]
    assert "feat:extra" in ids
    assert "clm:auth.t1" in ids
    assert "evd:auth.ci" in ids
    claim_entry = next(e for e in result.entries if e.id == "clm:auth.t1")
    assert "open → verified" in claim_entry.change


# --- format_diff output ---

def test_format_diff_no_changes() -> None:
    reg = _base_registry()
    result = format_diff(diff_registries(reg, reg))
    assert "No changes." in result


def test_format_diff_added_feature() -> None:
    a = _base_registry()
    b = _base_registry()
    b.features = list(a.features) + [Feature(id="feat:new", title="New feature")]
    result = format_diff(diff_registries(a, b))
    assert "+ feat:new" in result


def test_format_diff_removed_claim() -> None:
    a = _base_registry()
    b = _base_registry()
    b.claims = []
    result = format_diff(diff_registries(a, b))
    assert "- clm:auth.t1" in result


def test_format_diff_status_change() -> None:
    a = _base_registry()
    b = _base_registry()
    b.tests = [
        Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", status="passing")
    ]
    result = format_diff(diff_registries(a, b))
    assert "~ tst:auth.unit" in result
    assert "pending → passing" in result


def test_format_diff_header_shows_blobs() -> None:
    reg = _base_registry()
    result = format_diff(diff_registries(reg, reg, blob_a="blobAAA", blob_b="blobBBB"))
    assert "blobAAA" in result
    assert "blobBBB" in result


def test_format_diff_summary_line() -> None:
    a = _base_registry()
    b = _base_registry()
    b.features = list(a.features) + [
        Feature(id="feat:x", title="X"),
        Feature(id="feat:y", title="Y"),
    ]
    b.claims = []
    result = format_diff(diff_registries(a, b))
    assert "2 added" in result
    assert "1 removed" in result
