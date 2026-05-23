"""
Multi-agent demo — two agents sharing a proof chain via Walrus.

This script demonstrates verity's core value proposition:
  - Agent A researches and builds a proof chain
  - Agent A pushes it to Walrus (gets a blob ID)
  - Agent B (different session, different machine) pulls by blob ID
  - Agent B adds an audit sign-off and publishes a new release

Modes
-----
--dry-run   Use an in-memory shared store (no Walrus calls). Default.
--live      Use the Walrus testnet (set WALRUS_PUBLISHER_URL / WALRUS_AGGREGATOR_URL).

Examples
--------
    python examples/demo_multi_agent.py --dry-run
    python examples/demo_multi_agent.py --live
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from verity import VeritySession
from verity.walrus import WalrusBackend


class _SharedStore:
    """In-memory blob store for dry-run mode — both agents share one instance."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    def store(self, content: bytes) -> str:
        key = f"blob-{len(self._blobs)}"
        self._blobs[key] = content
        return key

    def fetch(self, key: str) -> bytes:
        return self._blobs[key]


def _hr(label: str = "") -> None:
    if label:
        print(f"\n{'─' * 20} {label} {'─' * 20}")
    else:
        print("─" * 60)


def agent_a(work_dir: Path, backend) -> str:
    """Agent A: researcher — builds proof chain and pushes."""
    _hr("Agent A  (researcher)")

    s = VeritySession(work_dir / "verity.json", backend=backend)
    s.init(repo_id="repo:supplier-quality")

    s.add_feature("feat:supplier.quality", "Evaluate supplier quality")
    s.add_claim(
        "clm:supplier.threshold",
        "Supplier X meets quality threshold",
        feature_id="feat:supplier.quality",
        tier="T1",
        status="verified",
    )
    s.add_test(
        "tst:supplier.eval",
        claim_id="clm:supplier.threshold",
        kind="integration",
        path="tests/test_supplier_eval.py",
        status="passing",
    )
    s.add_evidence(
        "evd:supplier.eval.run1",
        test_id="tst:supplier.eval",
        artifact_path="reports/eval.json",
        status="passed",
    )

    errors = s.validate()
    if errors:
        raise RuntimeError(f"Validation failed: {errors}")
    print("  validate  → OK")

    rel = s.release("0.1.0")
    print(f"  release   → {rel.id}")

    blob_id = s.push()
    print(f"  push      → blob: {blob_id}")

    registry = s.registry()
    print(f"  registry  → {len(registry.features)} feature(s), {len(registry.claims)} claim(s)")
    return blob_id


def agent_b(work_dir: Path, blob_id: str, backend) -> None:
    """Agent B: auditor — pulls Agent A's chain, adds sign-off, publishes."""
    _hr("Agent B  (auditor, fresh session)")

    s = VeritySession(work_dir / "verity_audit.json", backend=backend)
    s.pull(blob_id)

    registry = s.registry()
    print(f"  pull      → restored from {blob_id}")
    print(f"  registry  → {len(registry.features)} feature(s), {len(registry.claims)} claim(s)")

    errors = s.validate()
    if errors:
        raise RuntimeError(f"Validation failed after pull: {errors}")
    print("  validate  → OK")

    s.add_evidence(
        "evd:supplier.audit.signoff",
        test_id="tst:supplier.eval",
        artifact_path="audit/sign-off.json",
        status="passed",
    )

    rel = s.release("1.0.0")
    print(f"  release   → {rel.id}  ({len(rel.claim_ids)} claim(s))")

    new_blob_id = s.push()
    print(f"  push      → blob: {new_blob_id}")

    _hr("Audit trail")
    print(f"  {blob_id}  (Agent A)")
    print(f"    └─► {new_blob_id}  (Agent B audit)")

    log = s.log()
    _hr("Push log")
    for entry in log:
        print(f"  [{entry.backend}] {entry.timestamp}  {entry.blob_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="verity multi-agent demo")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True, help="In-memory shared store (default)")
    mode.add_argument("--live", action="store_true", help="Use Walrus testnet")
    args = parser.parse_args()

    use_live = args.live

    with tempfile.TemporaryDirectory() as tmp:
        work_a = Path(tmp) / "agent_a"
        work_b = Path(tmp) / "agent_b"
        work_a.mkdir()
        work_b.mkdir()

        if use_live:
            print("Mode: live (Walrus testnet)")
            publisher = os.environ.get(
                "WALRUS_PUBLISHER_URL", "https://publisher.walrus-testnet.walrus.space"
            )
            aggregator = os.environ.get(
                "WALRUS_AGGREGATOR_URL", "https://aggregator.walrus-testnet.walrus.space"
            )
            backend_a = WalrusBackend(publisher_url=publisher, aggregator_url=aggregator)
            backend_b = WalrusBackend(publisher_url=publisher, aggregator_url=aggregator)
        else:
            print("Mode: dry-run (in-memory shared store)")
            shared = _SharedStore()
            backend_a = shared
            backend_b = shared

        blob_id = agent_a(work_a, backend_a)
        agent_b(work_b, blob_id, backend_b)

    _hr()
    print("Demo complete.")


if __name__ == "__main__":
    main()
