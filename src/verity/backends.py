from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """Minimal interface for verity storage backends."""

    def store(self, content: bytes) -> str:
        """Upload bytes, return an opaque key (blob ID) for later retrieval."""
        ...

    def fetch(self, key: str) -> bytes:
        """Download bytes by the key returned from store()."""
        ...
