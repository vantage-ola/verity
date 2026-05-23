"""
VeritySession — high-level Python API for AI agents.

Agents can use verity without spawning a subprocess:

    from verity import VeritySession

    s = VeritySession("verity.json")
    s.add_feature("feat:auth", "User authentication")
    s.add_claim("clm:auth.t1", "Login works", feature_id="feat:auth")
    s.validate()
    s.push()
    print(s.log())
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from verity.backends import StorageBackend
from verity.models import Claim, Evidence, Feature, PushRecord, Registry, Release, Test
from verity.registry import canonical_json, load_registry, registry_path, save_registry
from verity.release import VerityReleaseError, create_release
from verity.validate import validate


class VeritySession:
    """
    Wraps a verity.json file and exposes the full verity API as Python methods.

    All mutating methods write-through to disk immediately (same semantics as
    the CLI). Call validate() before push() to catch errors early.
    """

    def __init__(
        self,
        path: str | Path = "verity.json",
        *,
        backend: StorageBackend | None = None,
    ) -> None:
        self.path = Path(path)
        self._backend = backend

    # --- registry I/O ---

    def _load(self) -> Registry:
        if not self.path.exists():
            raise FileNotFoundError(f"No registry at {self.path} — call init() first")
        return load_registry(self.path)

    def _save(self, registry: Registry) -> None:
        save_registry(registry, self.path)

    def init(self, repo_id: str = "repo:default") -> Registry:
        """Create a new verity.json. Raises if one already exists."""
        if self.path.exists():
            raise FileExistsError(f"{self.path} already exists")
        registry = Registry(repo_id=repo_id)
        self._save(registry)
        return registry

    # --- entity mutations ---

    def add_feature(self, id: str, title: str, status: str = "active") -> Feature:
        registry = self._load()
        feature = Feature(id=id, title=title, status=status)  # type: ignore[arg-type]
        registry.features.append(feature)
        self._save(registry)
        return feature

    def add_claim(
        self,
        id: str,
        title: str,
        *,
        feature_id: str,
        tier: str = "T1",
        status: str = "open",
    ) -> Claim:
        registry = self._load()
        claim = Claim(id=id, feature_id=feature_id, title=title, tier=tier, status=status)  # type: ignore[arg-type]
        registry.claims.append(claim)
        self._save(registry)
        return claim

    def add_test(
        self,
        id: str,
        *,
        claim_id: str,
        kind: str = "unit",
        path: str = "",
        status: str = "pending",
    ) -> Test:
        registry = self._load()
        test = Test(id=id, claim_id=claim_id, kind=kind, path=path, status=status)  # type: ignore[arg-type]
        registry.tests.append(test)
        self._save(registry)
        return test

    def add_evidence(
        self,
        id: str,
        *,
        test_id: str,
        artifact_path: str,
        kind: str = "test_run",
        status: str = "collected",
    ) -> Evidence:
        registry = self._load()
        evd = Evidence(id=id, test_id=test_id, kind=kind, artifact_path=artifact_path, status=status)  # type: ignore[arg-type]
        registry.evidence.append(evd)
        self._save(registry)
        return evd

    # --- operations ---

    def validate(self) -> list[str]:
        """Return a list of validation error strings (empty = clean)."""
        return validate(self._load())

    def release(self, version: str) -> Release:
        """Create a fail-closed release snapshot and persist it."""
        registry = self._load()
        rel = create_release(registry, version)
        self._save(registry)
        return rel

    def push(self, *, epochs: int = 5) -> str:
        """
        Serialize and upload the registry via the configured backend.
        Appends a PushRecord to the registry and stores the blob ID in the
        latest release row (if any). Returns the blob ID.

        Raises VerityPushError if no backend is configured.
        """
        if self._backend is None:
            raise VerityPushError(
                "No storage backend configured. Pass backend= to VeritySession, "
                "or use the CLI (verity push) which defaults to Walrus."
            )
        registry = self._load()
        errors = validate(registry)
        if errors:
            raise VerityPushError(f"Registry has {len(errors)} validation error(s): {errors[0]}")

        content = canonical_json(registry).encode("utf-8")
        blob_id: str = self._backend.store(content)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        backend_name = type(self._backend).__name__.lower().replace("backend", "")
        backend_label = "memwal" if "memwal" in backend_name else "walrus"

        registry.pushes.append(PushRecord(blob_id=blob_id, timestamp=timestamp, backend=backend_label))  # type: ignore[arg-type]
        if registry.releases:
            registry.releases[-1].walrus_blob_id = blob_id
        self._save(registry)
        return blob_id

    def pull(self, blob_id: str) -> None:
        """
        Download a registry by blob ID and overwrite the local verity.json.

        Raises VerityPushError if no backend is configured.
        """
        if self._backend is None:
            raise VerityPushError(
                "No storage backend configured. Pass backend= to VeritySession, "
                "or use the CLI (verity pull <blob-id>) which defaults to Walrus."
            )
        content = self._backend.fetch(blob_id)
        registry = Registry.model_validate(json.loads(content))
        self._save(registry)

    def log(self) -> list[PushRecord]:
        """Return all push records for this registry."""
        return self._load().pushes

    # --- read helpers ---

    def registry(self) -> Registry:
        """Return the current Registry object."""
        return self._load()


class VerityPushError(Exception):
    pass
