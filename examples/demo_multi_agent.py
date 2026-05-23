"""
Multi-agent demo — two agents sharing a proof chain via Walrus.

This script demonstrates verity's core value proposition:
  - Agent A researches and builds a proof chain
  - Agent A pushes it to Walrus (gets a blob ID)
  - Agent B (different session, different machine) pulls by blob ID
  - Agent B adds an audit sign-off and publishes a new release

Run this script against the Walrus testnet:
    export WALRUS_PUBLISHER_URL=https://publisher.walrus-testnet.walrus.space
    export WALRUS_AGGREGATOR_URL=https://aggregator.walrus-testnet.walrus.space
    python examples/demo_multi_agent.py

Or run in dry-run mode (no Walrus calls, simulated blob IDs):
    python examples/demo_multi_agent.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from verity import VeritySession
from verity.walrus import WalrusBackend


def make_mock_backend(blob_id: str) -> MagicMock:
    """Returns a mock StorageBackend for dry-run mode."""
    backend = MagicMock()
    _stored: dict[str, bytes] = {}

    def store(content: bytes) -> str:
        _stored[blob_id] = content
        return blob_id

    def fetch(key: str) -> bytes:
        return _stored.get(key, b"{}")

    backend.store.side_effect = store
    backend.fetch.side_effect = fetch
    return backend


def agent_a(work_dir: Path, backend) -> str:
    """Agent A: researcher — builds proof chain and pushes to Walrus."""
    print("\n=== Agent A (researcher) ===")

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
    print("  validated OK")

    rel = s.release("0.1.0")
    print(f"  released {rel.id}")

    blob_id = s.push()
    print(f"  pushed → blob: {blob_id}")

    registry = s.registry()
    print(f"  registry: {len(registry.features)} features, {len(registry.claims)} claims")
    return blob_id


def agent_b(work_dir: Path, blob_id: str, backend) -> None:
    """Agent B: auditor — pulls Agent A's chain, adds sign-off, publishes."""
    print("\n=== Agent B (auditor, fresh session) ===")

    s = VeritySession(work_dir / "verity_audit.json", backend=backend)
    s.pull(blob_id)
    print(f"  restored registry from {blob_id}")

    errors = s.validate()
    if errors:
        raise RuntimeError(f"Validation failed after pull: {errors}")
    print("  validated OK")

    # Add audit evidence
    s.add_evidence(
        "evd:supplier.audit.signoff",
        test_id="tst:supplier.eval",
        artifact_path="audit/sign-off.json",
        status="passed",
    )

    rel = s.release("1.0.0")
    print(f"  released {rel.id} with {len(rel.claim_ids)} claim(s)")

    new_blob_id = s.push()
    print(f"  pushed → blob: {new_blob_id}")
    print(f"  full audit trail: {blob_id} → {new_blob_id}")

    log = s.log()
    print(f"\n  push log ({len(log)} entries):")
    for entry in log:
        print(f"    [{entry.backend}] {entry.timestamp}  {entry.blob_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="verity multi-agent demo")
    parser.add_argument("--dry-run", action="store_true", help="Use mock backend (no Walrus calls)")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        work_a = Path(tmp) / "agent_a"
        work_b = Path(tmp) / "agent_b"
        work_a.mkdir()
        work_b.mkdir()

        if args.dry_run:
            print("Running in dry-run mode (simulated Walrus)")
            backend_a = make_mock_backend("blob-agent-a-0xabc123")
            backend_b = make_mock_backend("blob-agent-b-0xdef456")
        else:
            publisher = os.environ.get(
                "WALRUS_PUBLISHER_URL", "https://publisher.walrus-testnet.walrus.space"
            )
            aggregator = os.environ.get(
                "WALRUS_AGGREGATOR_URL", "https://aggregator.walrus-testnet.walrus.space"
            )
            backend_a = WalrusBackend(publisher_url=publisher, aggregator_url=aggregator)
            backend_b = WalrusBackend(publisher_url=publisher, aggregator_url=aggregator)

        blob_id = agent_a(work_a, backend_a)

        # Simulate Agent B receiving blob_id out-of-band (e.g. via Slack, issue comment, etc.)
        backend_b.fetch = backend_a.fetch  # share blob store in dry-run
        agent_b(work_b, blob_id, backend_b)

    print("\nDemo complete.")


if __name__ == "__main__":
    main()
