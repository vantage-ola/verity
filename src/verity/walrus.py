from __future__ import annotations

import json

import httpx

from verity.models import Registry
from verity.registry import canonical_json

AGGREGATOR_URL = "https://aggregator.walrus-testnet.walrus.space"
PUBLISHER_URL = "https://publisher.walrus-testnet.walrus.space"
DEFAULT_EPOCHS = 5


class WalrusError(Exception):
    pass


class WalrusBackend:
    """StorageBackend implementation using the Walrus HTTP API directly."""

    def __init__(
        self,
        *,
        publisher_url: str = PUBLISHER_URL,
        aggregator_url: str = AGGREGATOR_URL,
        epochs: int = DEFAULT_EPOCHS,
    ) -> None:
        self.publisher_url = publisher_url
        self.aggregator_url = aggregator_url
        self.epochs = epochs

    def store(self, content: bytes) -> str:
        with httpx.Client(timeout=30) as client:
            response = client.put(
                f"{self.publisher_url}/v1/blobs",
                content=content,
                params={"epochs": self.epochs},
                headers={"Content-Type": "application/octet-stream"},
            )
        if response.status_code not in (200, 201):
            raise WalrusError(f"Upload failed: HTTP {response.status_code} — {response.text[:200]}")
        data = response.json()
        if "newlyCreated" in data:
            return data["newlyCreated"]["blobObject"]["blobId"]
        if "alreadyCertified" in data:
            return data["alreadyCertified"]["blobId"]
        raise WalrusError(f"Unexpected response shape: {list(data.keys())}")

    def fetch(self, key: str) -> bytes:
        with httpx.Client(timeout=30) as client:
            response = client.get(f"{self.aggregator_url}/v1/blobs/{key}")
        if response.status_code != 200:
            raise WalrusError(f"Download failed: HTTP {response.status_code} — {response.text[:200]}")
        return response.content


def push(
    registry: Registry,
    *,
    epochs: int = DEFAULT_EPOCHS,
    publisher_url: str = PUBLISHER_URL,
) -> str:
    """Serialize registry to canonical JSON, upload to Walrus, return blob ID."""
    return WalrusBackend(publisher_url=publisher_url, epochs=epochs).store(
        canonical_json(registry).encode("utf-8")
    )


def pull(blob_id: str, *, aggregator_url: str = AGGREGATOR_URL) -> Registry:
    """Fetch a registry blob from Walrus by blob ID, return parsed Registry."""
    content = WalrusBackend(aggregator_url=aggregator_url).fetch(blob_id)
    return Registry.model_validate(json.loads(content))
