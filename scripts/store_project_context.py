"""
Store verity project context in MemWal so any agent can recall("verity") and
arrive with full project knowledge — no context pasting required.

Usage:
    python scripts/store_project_context.py

Requires MEMWAL_KEY and MEMWAL_ACCOUNT_ID (reads from .env automatically).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

try:
    from memwal import MemWalSync
except ImportError:
    print("ERROR: memwal not installed — run: pip install 'walrus-verity[memwal]'")
    raise SystemExit(1)

NAMESPACE = "verity-project"

MEMORIES = [
    (
        "verity overview",
        "verity is a proof-chain registry for AI agents backed by Walrus. "
        "It gives agents structured, portable memory: track what was claimed, "
        "what was tested, and what was proved, all in a single verity.json file. "
        "Push to Walrus → get a blob_id; pull by blob_id in any future session, "
        "on any machine, by any agent. PyPI package: walrus-verity.",
    ),
    (
        "verity proof-chain model",
        "verity's data model is a five-layer proof chain: "
        "feature → claim → test → evidence → release. "
        "Features describe capabilities. Claims are assertions a feature makes. "
        "Tests describe how claims are verified. Evidence records test run outcomes. "
        "Releases are fail-closed snapshots: all verified claims need passing tests "
        "with passed evidence, or the release is rejected.",
    ),
    (
        "verity storage design",
        "verity uses two storage layers: Walrus as primary (unencrypted, "
        "content-addressed blobs via HTTP REST), and MemWal as semantic discovery index "
        "(registers a pointer 'verity registry blob_id=<id> repo=<repo_id>' so agents "
        "can recall registries without knowing the blob_id). blob_id is always a plain "
        "Walrus blob_id, usable by any Walrus client. MemWal registration is non-fatal. "
        "Backends: WalrusBackend, MemWalBackend. CLI: verity push --backend walrus|memwal.",
    ),
    (
        "verity tech stack",
        "verity stack: Python 3.11+, pydantic v2 (models with extra=forbid), "
        "typer (CLI), httpx (Walrus HTTP), python-dotenv (.env loading), "
        "memwal SDK (MemWalSync). PyPI: walrus-verity. "
        "Optional: pip install 'walrus-verity[memwal]' for MemWal support. "
        "Build: hatchling, uv for dev. CI: GitHub Actions matrix on Python 3.11/3.12/3.13.",
    ),
    (
        "verity current status",
        "verity 0.1.3 is live on PyPI as walrus-verity. "
        "91 tests, 96% coverage, 85% branch coverage minimum enforced. "
        "Submitted to Sui Overflow hackathon, Walrus track. "
        "Features: core models, registry I/O, validation, fail-closed releases, "
        "Walrus backend, MemWal backend (Option A), VeritySession Python API, full CLI, "
        "LLM-agnostic agent skill (plugins/verity-agent/SKILL.md).",
    ),
    (
        "verity key design decisions",
        "Key verity decisions: (1) MemWal Option A — store blobs on Walrus directly "
        "(unencrypted), use MemWal only for semantic discovery; avoids SEAL encryption "
        "making direct Walrus fetch return ciphertext. "
        "(2) Canonical JSON — sorted keys, compact separators, no trailing newline, "
        "allow_nan=False — ensures deterministic blob IDs. "
        "(3) Fail-closed releases — all verified claims need passing tests with passed "
        "evidence, no partial releases. "
        "(4) load_dotenv() deferred to CLI @app.callback() — avoids polluting test env.",
    ),
    (
        "verity repo layout",
        "verity repository layout: "
        "src/verity/ — core package (models, registry, validate, release, walrus, memwal, session, site, cli/). "
        "tests/ — pytest suite (test_models, test_cli, test_walrus, test_memwal, test_release, test_session, test_validate, test_site). "
        "docs/ — cli.md, python-api.md, schema.md, walrus.md, memwal.md, multi-agent.md. "
        "plugins/verity-agent/ — SKILL.md + AGENT_PROMPT.md (LLM-agnostic agent skill). "
        "examples/ — demo_multi_agent.py (two-agent handoff demo). "
        "scripts/ — store_project_context.py (this file). "
        "verity.json — verity's own proof chain (dogfooding).",
    ),
]


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

    print(f"Connecting to MemWal ({server_url}) namespace={NAMESPACE!r} ...")
    client = MemWalSync.create(
        key=key,
        account_id=account_id,
        server_url=server_url,
        namespace=NAMESPACE,
    )

    for label, content in MEMORIES:
        print(f"  storing: {label!r} ...", end=" ", flush=True)
        client.remember_and_wait(content, namespace=NAMESPACE)
        print("OK")

    print(f"\nStored {len(MEMORIES)} memories in namespace {NAMESPACE!r}.")
    print("Any agent can now recall('verity') and arrive with full project context.")


if __name__ == "__main__":
    main()
