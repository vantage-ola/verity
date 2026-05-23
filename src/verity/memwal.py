"""
MemWal storage backend for verity.

MemWal (https://memwal.io) is a Walrus-backed memory layer for AI agents.
It handles encryption, embedding, and Walrus storage server-side; the
client signs requests with an Ed25519 delegate key and receives a Walrus
blob ID in return.

Installation:
    pip install memwal          # or: uv add memwal

Required configuration (pass as kwargs or set env vars):
    MEMWAL_KEY          Ed25519 delegate key (hex), issued by the MemWal relayer
    MEMWAL_ACCOUNT_ID   Your MemWal account ID (on-chain address)

Optional configuration:
    MEMWAL_SERVER_URL   Relayer URL (default: https://relayer.memwal.ai)
    MEMWAL_NAMESPACE    Logical namespace for this project (default: verity)
    MEMWAL_ENV          Preset env: prod | dev | staging | local

Store uses the MemWal relayer; fetch goes to the Walrus aggregator
directly (the blob_id returned by MemWal is a standard Walrus blob ID).
"""

from __future__ import annotations

import os

import httpx

from verity.walrus import AGGREGATOR_URL

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
    StorageBackend that stores via the MemWal relayer and fetches directly
    from the Walrus aggregator.
    """

    def __init__(
        self,
        *,
        key: str | None = None,
        account_id: str | None = None,
        server_url: str | None = None,
        namespace: str | None = None,
        env: str | None = None,
        aggregator_url: str = AGGREGATOR_URL,
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
        self._aggregator_url = aggregator_url

        create_kwargs: dict[str, str] = dict(
            key=_key,
            account_id=_account_id,
            server_url=_server_url,
            namespace=_namespace,
        )
        if _env:
            create_kwargs["env"] = _env

        self._client: MemWalSync = MemWalSync.create(**create_kwargs)

    def store(self, content: bytes) -> str:
        """
        Upload content to MemWal via remember_and_wait().
        Returns the Walrus blob ID assigned by the relayer.
        """
        try:
            result = self._client.remember_and_wait(
                content.decode("utf-8"), namespace=self.namespace
            )
        except _SdkError as exc:
            raise MemWalError(f"MemWal store failed: {exc}") from exc
        return result.blob_id

    def fetch(self, key: str) -> bytes:
        """
        Fetch content by Walrus blob ID directly from the aggregator.
        MemWal stores blobs on Walrus, so no relayer round-trip is needed.
        """
        with httpx.Client(timeout=30) as client:
            response = client.get(f"{self._aggregator_url}/v1/blobs/{key}")
        if response.status_code != 200:
            raise MemWalError(
                f"MemWal fetch failed: HTTP {response.status_code} — {response.text[:200]}"
            )
        return response.content
