from __future__ import annotations

import json
from pathlib import Path

from verity.models import Registry

REGISTRY_FILENAME = "verity.json"


def load_registry(path: Path) -> Registry:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Registry.model_validate(data)


def canonical_json(registry: Registry) -> str:
    return json.dumps(registry.model_dump(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def save_registry(registry: Registry, path: Path) -> None:
    path.write_text(canonical_json(registry), encoding="utf-8")


def registry_path(directory: Path = Path(".")) -> Path:
    return directory / REGISTRY_FILENAME
