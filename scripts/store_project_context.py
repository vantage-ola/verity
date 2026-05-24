"""
Sync verity.json context entries to MemWal so any agent can recall("verity")
and arrive with full project knowledge — no context pasting required.

Add context entries first:
    verity context set architecture "5-layer proof chain: feature → claim → test → evidence → release"
    verity context set decisions "we chose MemWal Option A because SEAL encryption..."

Then run this script to push them to MemWal:
    python scripts/store_project_context.py

Requires MEMWAL_KEY and MEMWAL_ACCOUNT_ID (reads from .env automatically).
When you push via `verity push --backend memwal`, context is stored automatically.
This script is useful for a one-shot sync without a full push.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    from memwal import MemWalSync
except ImportError:
    print("ERROR: memwal not installed — run: pip install 'walrus-verity[memwal]'")
    raise SystemExit(1)

NAMESPACE = "verity-project"
REGISTRY_PATH = Path("verity.json")


def main() -> None:
    key = os.environ.get("MEMWAL_KEY", "")
    account_id = os.environ.get("MEMWAL_ACCOUNT_ID", "")
    server_url = os.environ.get("MEMWAL_SERVER_URL", "https://relayer.memwal.ai")

    if not key:
        print("ERROR: MEMWAL_KEY not set — add it to .env or export it")
        raise SystemExit(1)
    if not account_id:
        print("ERROR: MEMWAL_ACCOUNT_ID not set — add it to .env or export it")
        raise SystemExit(1)

    if not REGISTRY_PATH.exists():
        print(f"ERROR: {REGISTRY_PATH} not found — run from the repo root")
        raise SystemExit(1)

    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    repo_id = data.get("repo_id", "unknown")
    entries = data.get("context", [])

    if not entries:
        print(f"No context entries in {REGISTRY_PATH}.")
        print("Add some with: verity context set KEY 'your narrative here'")
        raise SystemExit(0)

    print(f"Connecting to MemWal ({server_url}) namespace={NAMESPACE!r} ...")
    client = MemWalSync.create(
        key=key,
        account_id=account_id,
        server_url=server_url,
        namespace=NAMESPACE,
    )

    stored = 0
    for entry in entries:
        key_name = entry.get("key", "")
        value = entry.get("value", "")
        if not key_name or not value:
            continue
        print(f"  storing: {key_name!r} ...", end=" ", flush=True)
        client.remember_and_wait(
            f"verity context key={key_name} repo={repo_id}: {value}",
            namespace=NAMESPACE,
        )
        print("OK")
        stored += 1

    print(f"\nStored {stored} context entries for repo={repo_id!r}.")
    print("Any agent can now recall('verity') and arrive with full project context.")


if __name__ == "__main__":
    main()
