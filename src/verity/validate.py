from __future__ import annotations

from verity.models import Registry


def validate(registry: Registry) -> list[str]:
    errors: list[str] = []

    feature_ids = {f.id for f in registry.features}
    claim_ids = {c.id for c in registry.claims}
    test_ids = {t.id for t in registry.tests}

    # duplicate IDs within each collection
    for label, items in [
        ("feature", registry.features),
        ("claim", registry.claims),
        ("test", registry.tests),
        ("evidence", registry.evidence),
        ("release", registry.releases),
    ]:
        seen: set[str] = set()
        for item in items:
            if item.id in seen:
                errors.append(f"Duplicate {label} id: {item.id}")
            seen.add(item.id)

    # broken links
    for claim in registry.claims:
        if claim.feature_id not in feature_ids:
            errors.append(f"Claim {claim.id} references unknown feature {claim.feature_id}")

    for test in registry.tests:
        if test.claim_id not in claim_ids:
            errors.append(f"Test {test.id} references unknown claim {test.claim_id}")

    for evd in registry.evidence:
        if evd.test_id not in test_ids:
            errors.append(f"Evidence {evd.id} references unknown test {evd.test_id}")

    for release in registry.releases:
        for cid in release.claim_ids:
            if cid not in claim_ids:
                errors.append(f"Release {release.id} references unknown claim {cid}")

    # build lookup maps for status consistency checks
    tests_by_claim: dict[str, list[str]] = {}
    for test in registry.tests:
        tests_by_claim.setdefault(test.claim_id, []).append(test.id)

    evidence_statuses_by_test: dict[str, list[str]] = {}
    for evd in registry.evidence:
        evidence_statuses_by_test.setdefault(evd.test_id, []).append(evd.status)

    # verified claim must have at least one linked test
    for claim in registry.claims:
        if claim.status == "verified" and not tests_by_claim.get(claim.id):
            errors.append(f"Claim {claim.id} is 'verified' but has no linked tests")

    # passing test must have at least one "passed" evidence (not just collected/failed)
    for test in registry.tests:
        if test.status == "passing":
            statuses = evidence_statuses_by_test.get(test.id, [])
            if not statuses:
                errors.append(f"Test {test.id} is 'passing' but has no linked evidence")
            elif not any(s == "passed" for s in statuses):
                errors.append(f"Test {test.id} is 'passing' but has no 'passed' evidence")

    # T1 verified claim must have at least one test backed by passed evidence
    for claim in registry.claims:
        if claim.tier == "T1" and claim.status == "verified":
            linked_tests = tests_by_claim.get(claim.id, [])
            has_passed = any(
                any(s == "passed" for s in evidence_statuses_by_test.get(tid, []))
                for tid in linked_tests
            )
            if not has_passed:
                errors.append(
                    f"T1 claim {claim.id} is 'verified' but has no test with 'passed' evidence"
                )

    # release claim_ids must reference verified claims (not just existing ones)
    claim_status = {c.id: c.status for c in registry.claims}
    for release in registry.releases:
        for cid in release.claim_ids:
            if cid in claim_status and claim_status[cid] != "verified":
                errors.append(
                    f"Release {release.id} includes claim {cid} which is not 'verified'"
                )

    return errors
