"""
MemWal storage backend for verity.

Storage strategy (Option A):
  store() — uploads the registry blob to Walrus directly (unencrypted,
            content-addressed, directly retrievable), then registers a
            semantic pointer in MemWal so agents can discover registries
            via recall("verity registry for repo:X").
  fetch() — fetches directly from the Walrus aggregator; no MemWal
            round-trip needed.

This means:
  - blob_id is a standard Walrus blob ID, usable by any Walrus client.
  - MemWal provides semantic discoverability on top, not the storage layer.
  - MemWal registration failure is non-fatal — the blob is already on Walrus.

Required configuration (pass as kwargs or set env vars):
    MEMWAL_KEY          Ed25519 delegate key (hex), issued by the MemWal relayer
    MEMWAL_ACCOUNT_ID   Your MemWal account ID (on-chain address)

Optional configuration:
    MEMWAL_SERVER_URL       Relayer URL (default: prod relayer)
    MEMWAL_NAMESPACE        Logical namespace (default: verity)
    MEMWAL_ENV              Relayer preset: prod | dev | staging | local
    WALRUS_PUBLISHER_URL    Walrus publisher endpoint
    WALRUS_AGGREGATOR_URL   Walrus aggregator endpoint
"""

from __future__ import annotations

import json
import os

from verity.walrus import (
    AGGREGATOR_URL as _WALRUS_AGGREGATOR_URL,
    PUBLISHER_URL as _WALRUS_PUBLISHER_URL,
    WalrusBackend,
    WalrusError,
)

try:
    from memwal import MemWalSync
    from memwal import MemWalError as _SdkError

    _MEMWAL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MEMWAL_AVAILABLE = False
    _SdkError = Exception  # type: ignore[assignment,misc]

PROD_SERVER_URL = "https://relayer.memwal.ai"


class MemWalError(Exception):
    pass


class MemWalBackend:
    """
    StorageBackend that stores blobs on Walrus and registers a semantic
    pointer in MemWal for agent discovery via recall().
    """

    def __init__(
        self,
        *,
        key: str | None = None,
        account_id: str | None = None,
        server_url: str | None = None,
        namespace: str | None = None,
        env: str | None = None,
        publisher_url: str | None = None,
        aggregator_url: str | None = None,
        epochs: int = 5,
    ) -> None:
        if not _MEMWAL_AVAILABLE:
            raise MemWalError(  # pragma: no cover
                "memwal package not installed — run: pip install memwal"
            )

        _key = key or os.environ.get("MEMWAL_KEY", "")
        _account_id = account_id or os.environ.get("MEMWAL_ACCOUNT_ID", "")
        _server_url = server_url or os.environ.get("MEMWAL_SERVER_URL", PROD_SERVER_URL)
        _namespace = namespace or os.environ.get("MEMWAL_NAMESPACE", "verity")
        _env = env or os.environ.get("MEMWAL_ENV")

        if not _key:
            raise MemWalError("MemWal key is required (set MEMWAL_KEY or pass key=)")
        if not _account_id:
            raise MemWalError("MemWal account_id is required (set MEMWAL_ACCOUNT_ID or pass account_id=)")

        self.namespace = _namespace

        create_kwargs: dict[str, str] = dict(
            key=_key,
            account_id=_account_id,
            server_url=_server_url,
            namespace=_namespace,
        )
        if _env:
            create_kwargs["env"] = _env

        self._client: MemWalSync = MemWalSync.create(**create_kwargs)

        # Internal Walrus backend — reuses WALRUS_PUBLISHER/AGGREGATOR_URL env vars
        _publisher = publisher_url or os.environ.get("WALRUS_PUBLISHER_URL", _WALRUS_PUBLISHER_URL)
        _aggregator = aggregator_url or os.environ.get("WALRUS_AGGREGATOR_URL", _WALRUS_AGGREGATOR_URL)
        self._walrus = WalrusBackend(
            publisher_url=_publisher,
            aggregator_url=_aggregator,
            epochs=epochs,
        )

    def store(self, content: bytes) -> str:
        """
        Upload content to Walrus (primary) and register a discovery pointer
        in MemWal (secondary, non-fatal). Returns the Walrus blob ID.
        """
        try:
            blob_id = self._walrus.store(content)
        except WalrusError as exc:
            raise MemWalError(f"MemWal store failed (Walrus upload): {exc}") from exc

        # Register semantic pointer so agents can recall("verity registry for repo:X")
        try:
            repo_id = json.loads(content).get("repo_id", "unknown")
        except Exception:
            repo_id = "unknown"

        try:
            self._client.remember_and_wait(
                f"verity registry blob_id={blob_id} repo={repo_id}",
                namespace=self.namespace,
            )
        except _SdkError:
            pass  # non-fatal — blob is already on Walrus

        return blob_id

    def fetch(self, key: str) -> bytes:
        """
        Fetch a registry blob directly from the Walrus aggregator.
        """
        try:
            return self._walrus.fetch(key)
        except WalrusError as exc:
            raise MemWalError(f"MemWal fetch failed: {exc}") from exc
