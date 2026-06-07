from __future__ import annotations

from datetime import datetime, timezone

from verity.models import Registry, Release
from verity.validate import validate


class VerityReleaseError(Exception):
    pass


def create_release(registry: Registry, version: str) -> Release:
    errors = validate(registry)
    if errors:
        raise VerityReleaseError(
            "Registry has validation errors:\n" + "\n".join(f"  {e}" for e in errors)
        )

    verified_claims = [c for c in registry.claims if c.status == "verified"]
    if not verified_claims:
        raise VerityReleaseError("No verified claims found — nothing to release")

    release_id = f"rel:{version}"
    if any(r.id == release_id for r in registry.releases):
        raise VerityReleaseError(f"Release {release_id} already exists")

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
