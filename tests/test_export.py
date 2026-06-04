"""Tests for verity.export — SARIF, JUnit XML, and SPDX exporters."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import pytest

from verity.export import export, export_junit, export_sarif, export_spdx
from verity.models import Claim, Evidence, Feature, Registry, Test


def _registry() -> Registry:
    return Registry(
        repo_id="repo:test",
        features=[Feature(id="feat:auth", title="User authentication")],
        claims=[Claim(id="clm:auth.t1", title="Login succeeds", feature_id="feat:auth", status="verified")],
        tests=[Test(id="tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", status="passing")],
        evidence=[Evidence(id="evd:auth.ci", test_id="tst:auth.unit", artifact_path="ci.json", status="passed")],
    )


# ---------------------------------------------------------------------------
# SARIF
# ---------------------------------------------------------------------------


def test_sarif_schema_field() -> None:
    doc = json.loads(export_sarif(_registry()))
    assert "$schema" in doc
    assert "sarif" in doc["$schema"].lower()


def test_sarif_verified_claim_level_none() -> None:
    doc = json.loads(export_sarif(_registry()))
    result = doc["runs"][0]["results"][0]
    assert result["ruleId"] == "clm:auth.t1"
    assert result["level"] == "none"


def test_sarif_open_claim_level_warning() -> None:
    reg = _registry()
    reg.claims = [Claim(id="clm:auth.t1", title="Login succeeds", feature_id="feat:auth", status="open")]
    doc = json.loads(export_sarif(reg))
    result = doc["runs"][0]["results"][0]
    assert result["level"] == "warning"


# ---------------------------------------------------------------------------
# JUnit XML
# ---------------------------------------------------------------------------


def test_junit_is_valid_xml() -> None:
    output = export_junit(_registry())
    root = ET.fromstring(output.replace('<?xml version="1.0" encoding="utf-8"?>\n', ""))
    assert root.tag == "testsuites"


def test_junit_passed_evidence_no_failure_element() -> None:
    output = export_junit(_registry())
    root = ET.fromstring(output.replace('<?xml version="1.0" encoding="utf-8"?>\n', ""))
    testcase = root.find(".//testcase")
    assert testcase is not None
    assert testcase.find("failure") is None
    assert testcase.find("skipped") is None


def test_junit_failed_evidence_has_failure_element() -> None:
    reg = _registry()
    reg.evidence = [Evidence(id="evd:auth.ci", test_id="tst:auth.unit", artifact_path="ci.json", status="failed")]
    output = export_junit(reg)
    root = ET.fromstring(output.replace('<?xml version="1.0" encoding="utf-8"?>\n', ""))
    failure = root.find(".//failure")
    assert failure is not None


def test_junit_no_evidence_is_skipped() -> None:
    reg = _registry()
    reg.evidence = []
    output = export_junit(reg)
    root = ET.fromstring(output.replace('<?xml version="1.0" encoding="utf-8"?>\n', ""))
    skipped = root.find(".//skipped")
    assert skipped is not None


# ---------------------------------------------------------------------------
# SPDX
# ---------------------------------------------------------------------------


def test_spdx_version_field() -> None:
    doc = json.loads(export_spdx(_registry()))
    assert doc["spdxVersion"] == "SPDX-2.3"


def test_spdx_packages_contains_feature() -> None:
    doc = json.loads(export_spdx(_registry()))
    names = [p["name"] for p in doc["packages"]]
    assert "feat:auth" in names


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------


def test_export_invalid_format_raises() -> None:
    with pytest.raises(ValueError, match="Unknown format"):
        export(_registry(), "csv")
