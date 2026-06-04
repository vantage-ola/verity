"""Export a verity Registry to standard DevSecOps interchange formats."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from verity.models import Registry


def export_sarif(registry: Registry) -> str:
    """Export proof chain claims as a SARIF 2.1.0 document."""
    rules = [
        {
            "id": c.id,
            "name": c.title,
            "shortDescription": {"text": c.title},
            "properties": {"feature_id": c.feature_id, "tier": c.tier},
        }
        for c in registry.claims
    ]

    level_map = {"verified": "none", "open": "warning", "rejected": "error"}

    results = [
        {
            "ruleId": c.id,
            "message": {"text": f"{c.title} [{c.feature_id}, {c.tier}]"},
            "level": level_map.get(c.status, "warning"),
            "properties": {"status": c.status, "tier": c.tier, "feature_id": c.feature_id},
        }
        for c in registry.claims
    ]

    doc = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "verity", "rules": rules}},
                "results": results,
            }
        ],
    }
    return json.dumps(doc, indent=2)


def export_junit(registry: Registry) -> str:
    """Export proof chain tests as JUnit XML."""
    claim_map = {c.id: c for c in registry.claims}
    # map test_id → evidence (take the latest by list order)
    evidence_map: dict[str, object] = {}
    for evd in registry.evidence:
        evidence_map[evd.test_id] = evd

    # group tests by feature (via claim)
    feat_tests: dict[str, list] = {f.id: [] for f in registry.features}
    ungrouped: list = []
    for t in registry.tests:
        claim = claim_map.get(t.claim_id)
        if claim and claim.feature_id in feat_tests:
            feat_tests[claim.feature_id].append(t)
        else:
            ungrouped.append(t)

    root = ET.Element("testsuites", name=f"verity {registry.repo_id}")

    def _add_suite(suite_name: str, tests: list) -> None:
        failures = sum(
            1 for t in tests
            if getattr(evidence_map.get(t.id), "status", None) == "failed"
        )
        skipped = sum(
            1 for t in tests
            if t.id not in evidence_map or getattr(evidence_map[t.id], "status", None) == "collected"
        )
        suite = ET.SubElement(
            root, "testsuite",
            name=suite_name,
            tests=str(len(tests)),
            failures=str(failures),
            errors="0",
            skipped=str(skipped),
        )
        for t in tests:
            claim = claim_map.get(t.claim_id)
            classname = f"{t.claim_id} {claim.title}" if claim else t.claim_id
            tc = ET.SubElement(suite, "testcase", name=t.id, classname=classname, time="0")
            evd = evidence_map.get(t.id)
            if evd is None or getattr(evd, "status", None) == "collected":
                ET.SubElement(tc, "skipped", message="No evidence collected")
            elif getattr(evd, "status", None) == "failed":
                ET.SubElement(tc, "failure", message=f"Evidence failed: {evd.id}", type="VerityEvidence")  # type: ignore[attr-defined]

    for feat_id, tests in feat_tests.items():
        if tests:
            _add_suite(feat_id, tests)
    if ungrouped:
        _add_suite("ungrouped", ungrouped)

    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode")


def export_spdx(registry: Registry) -> str:
    """Export proof chain features as a minimal SPDX-2.3 document."""
    verified_counts: dict[str, int] = {f.id: 0 for f in registry.features}
    for c in registry.claims:
        if c.status == "verified" and c.feature_id in verified_counts:
            verified_counts[c.feature_id] += 1

    def _spdx_id(feat_id: str) -> str:
        return "SPDXRef-" + feat_id.replace(":", "-").replace(".", "-")

    packages = [
        {
            "SPDXID": _spdx_id(f.id),
            "name": f.id,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "versionInfo": f.status,
            "comment": f"{f.title} — {verified_counts[f.id]} verified claim(s)",
        }
        for f in registry.features
    ]

    doc = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": registry.repo_id,
        "documentNamespace": f"https://verity/{registry.repo_id}",
        "packages": packages,
    }
    return json.dumps(doc, indent=2)


def export(registry: Registry, format: str) -> str:
    """Dispatch to the correct exporter. Raises ValueError for unknown formats."""
    if format == "sarif":
        return export_sarif(registry)
    if format == "junit":
        return export_junit(registry)
    if format == "spdx":
        return export_spdx(registry)
    raise ValueError(f"Unknown format: {format!r}. Choose sarif, junit, or spdx.")
