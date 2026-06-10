from __future__ import annotations

import json
import warnings
from pathlib import Path

from verity.models import Registry

REGISTRY_FILENAME = "verity.json"
_NEW_REGISTRY_PATH = Path(".verity") / "registry.json"
_OLD_REGISTRY_FILENAME = "verity.json"


def load_registry(path: Path) -> Registry:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Registry.model_validate(data)


def canonical_json(registry: Registry) -> str:
    return json.dumps(registry.model_dump(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def save_registry(registry: Registry, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(registry), encoding="utf-8")


def registry_path(directory: Path = Path(".")) -> Path:
    """Return the registry path, preferring .verity/registry.json.

    Falls back to legacy verity.json with a deprecation warning when the new
    path does not exist but the old one does.
    """
    new = directory / _NEW_REGISTRY_PATH
    old = directory / _OLD_REGISTRY_FILENAME
    if not new.exists() and old.exists():
        warnings.warn(
            f"verity.json found at repo root. Move it to .verity/registry.json — "
            f"run: mkdir -p .verity && mv verity.json .verity/registry.json",
            DeprecationWarning,
            stacklevel=2,
        )
        return old
    return new
