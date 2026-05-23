from __future__ import annotations

from datetime import datetime, timezone

from verity.models import Registry, Release


class VerityReleaseError(Exception):
    pass


def create_release(registry: Registry, version: str) -> Release:
    verified_claims = [c for c in registry.claims if c.status == "verified"]
    if not verified_claims:
        raise VerityReleaseError("No verified claims found — nothing to release")

    test_ids_by_claim: dict[str, list[str]] = {}
    for test in registry.tests:
        test_ids_by_claim.setdefault(test.claim_id, []).append(test.id)

    passed_evidence_by_test: dict[str, bool] = {}
    for evd in registry.evidence:
        if evd.status == "passed":
            passed_evidence_by_test[evd.test_id] = True

    for claim in verified_claims:
        linked_tests = test_ids_by_claim.get(claim.id, [])
        if not linked_tests:
            raise VerityReleaseError(
                f"Claim {claim.id} is verified but has no linked tests"
            )
        if not any(passed_evidence_by_test.get(tid) for tid in linked_tests):
            raise VerityReleaseError(
                f"Claim {claim.id} has no test with passed evidence"
            )

    release_id = f"rel:{version}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    release = Release(
        id=release_id,
        version=version,
        timestamp=timestamp,
        walrus_blob_id=None,
        claim_ids=[c.id for c in verified_claims],
    )
    registry.releases.append(release)
    return release
