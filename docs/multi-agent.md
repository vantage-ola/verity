# Multi-Agent Patterns

## The handoff pattern

The core idea: Agent A builds a proof chain and pushes it to Walrus. Agent B receives the `blob_id` out-of-band (env var, task metadata, Slack, issue comment — any channel), pulls the chain, and continues.

```
Agent A                            Agent B
  │                                   │
  ├─ init / build proof chain         │
  ├─ validate()                       │
  ├─ release("0.1.0")                 │
  ├─ push() ──── blob_id ───────────► │
  │                                   ├─ pull(blob_id)
  │                                   ├─ validate()
  │                                   ├─ add_evidence(...)   ← audit / extend
  │                                   ├─ release("1.0.0")
  │                                   └─ push() ──► new_blob_id
```

The `blob_id` is immutable — it always resolves to the exact state Agent A published. Agent B's new push creates a separate blob that extends the chain.

---

## Code example

```python
from verity import VeritySession, WalrusBackend

# Agent A — researcher
a = VeritySession("agent_a/verity.json", backend=WalrusBackend())
a.init(repo_id="repo:quality-check")

a.add_feature("feat:supplier.quality", "Evaluate supplier quality")
a.add_claim("clm:supplier.threshold", "Supplier X meets threshold",
            feature_id="feat:supplier.quality", tier="T1", status="verified")
a.add_test("tst:supplier.eval", claim_id="clm:supplier.threshold",
           kind="integration", path="tests/test_supplier.py", status="passing")
a.add_evidence("evd:supplier.run1", test_id="tst:supplier.eval",
               artifact_path="reports/eval.json", status="passed")

a.validate()
a.release("0.1.0")
blob_id = a.push()
print(f"Agent A published: {blob_id}")

# --- blob_id is passed to Agent B via any channel ---

# Agent B — auditor (different machine, different session)
b = VeritySession("agent_b/verity.json", backend=WalrusBackend())
b.pull(blob_id)
b.validate()   # confirm the restored chain is clean

b.add_evidence("evd:supplier.audit", test_id="tst:supplier.eval",
               artifact_path="audit/sign-off.json", status="passed")
b.release("1.0.0")
new_blob_id = b.push()
print(f"Agent B published: {blob_id} → {new_blob_id}")

# Full push trail
for entry in b.log():
    print(f"  [{entry.backend}] {entry.timestamp}  {entry.blob_id}")
```

---

## Dry-run / in-memory (no Walrus)

Useful for testing agent logic without real Walrus calls. Both agents share one `_SharedStore` instance so pushes from Agent A are immediately readable by Agent B:

```python
class _SharedStore:
    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    def store(self, content: bytes) -> str:
        key = f"blob-{len(self._blobs)}"
        self._blobs[key] = content
        return key

    def fetch(self, key: str) -> bytes:
        return self._blobs[key]

shared = _SharedStore()

a = VeritySession("agent_a/verity.json", backend=shared)
b = VeritySession("agent_b/verity.json", backend=shared)
```

See `examples/demo_multi_agent.py` for a full working demo. Run it with:

```bash
python examples/demo_multi_agent.py           # dry-run (default, in-memory)
python examples/demo_multi_agent.py --live    # Walrus testnet
```

---

## Audit trail only

Pull and inspect without mutating:

```python
s = VeritySession("audit.json", backend=WalrusBackend())
s.pull(blob_id)

errors = s.validate()
if errors:
    print("Chain has issues:", errors)
else:
    print("Chain is clean")
    registry = s.registry()
    print(f"  {len(registry.claims)} claims, {len(registry.releases)} releases")
    for entry in s.log():
        print(f"  pushed {entry.blob_id} at {entry.timestamp}")
```

---

## Passing the blob ID

Common patterns for handing off a `blob_id` between agents:

- **Environment variable**: `os.environ["VERITY_BLOB_ID"] = blob_id`
- **File**: write to a shared artifact path the next agent reads
- **Task/issue metadata**: comment the blob_id on a GitHub issue or task
- **Message queue**: publish to a Slack channel, Redis queue, etc.

The blob_id is just a string — pass it however makes sense for your pipeline.
