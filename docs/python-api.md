# Python API

## `VeritySession`

The primary interface for agents and scripts. All mutating methods write through to `verity.json` immediately.

```python
from verity import VeritySession, WalrusBackend

s = VeritySession("verity.json", backend=WalrusBackend())
s.init(repo_id="repo:my-agent")
```

### Constructor

```python
VeritySession(path="verity.json", *, backend: StorageBackend | None = None)
```

`backend` is optional. If not provided, `push()` will raise `VerityPushError`.

---

### Methods

| Method | Returns | Description |
|---|---|---|
| `init(repo_id)` | `Registry` | Create `verity.json`; raises `FileExistsError` if it exists |
| `add_feature(id, title, status?)` | `Feature` | Append a Feature |
| `add_claim(id, title, *, feature_id, tier?, status?)` | `Claim` | Append a Claim |
| `add_test(id, *, claim_id, kind?, path?, status?)` | `Test` | Append a Test |
| `add_evidence(id, *, test_id, artifact_path, kind?, status?)` | `Evidence` | Append Evidence |
| `validate()` | `list[str]` | Return errors (empty = clean) |
| `release(version)` | `Release` | Fail-closed release; raises `VerityReleaseError` |
| `push(*, epochs?)` | `str` | Upload to backend; returns blob ID |
| `pull(blob_id)` | `None` | Fetch from backend, overwrite local registry |
| `log()` | `list[PushRecord]` | Push history |
| `registry()` | `Registry` | Current in-memory registry |
| `set_context(key, value)` | `None` | Upsert a named context entry |
| `get_context(key)` | `str \| None` | Return value for key, or `None` |
| `remove_context(key)` | `bool` | Remove entry; returns `True` if it existed |

---

### Full example

```python
from verity import VeritySession, WalrusBackend

s = VeritySession("verity.json", backend=WalrusBackend())
s.init(repo_id="repo:my-agent")

s.add_feature("feat:summarise", "Summarise documents")
s.add_claim(
    "clm:summarise.t1",
    "Summary is accurate",
    feature_id="feat:summarise",
    tier="T1",
    status="verified",
)
s.add_test(
    "tst:summarise.eval",
    claim_id="clm:summarise.t1",
    kind="integration",
    path="evals/test_summary.py",
    status="passing",
)
s.add_evidence(
    "evd:summarise.run1",
    test_id="tst:summarise.eval",
    artifact_path="evals/results.json",
    status="passed",
)

errors = s.validate()
assert errors == [], errors

release = s.release("1.0.0")
blob_id = s.push()
print(f"Published: {blob_id}")
```

---

## Low-level functions

These are available for cases where you want direct access without `VeritySession`.

```python
from verity import load_registry, save_registry, validate, push, pull
from pathlib import Path

registry = load_registry(Path("verity.json"))
errors = validate(registry)

blob_id = push(registry, publisher_url="...", aggregator_url="...")
restored = pull(blob_id, aggregator_url="...")
```

---

### Context example

```python
s = VeritySession("verity.json")

s.set_context("architecture", "5-layer proof chain: feature → claim → test → evidence → release")
s.set_context("decisions", "chose MemWal Option A — store blobs on Walrus, use MemWal for discovery")

print(s.get_context("architecture"))
# 5-layer proof chain: feature → claim → test → evidence → release

s.remove_context("decisions")
print(s.registry().context)  # [ContextEntry(key='architecture', value='...')]
```

Context entries are automatically stored as MemWal memories when you call `push()` with a `MemWalBackend`.

---

## Models

All models are pydantic v2 with `extra="forbid"`. ID prefixes are enforced at the model level.

```python
from verity import Feature, Claim, Test, Evidence, Release, Registry, PushRecord, ContextEntry
```

See [schema.md](schema.md) for field definitions and allowed values.

---

## Custom backend

Any object implementing `store(bytes) -> str` and `fetch(str) -> bytes` works:

```python
from verity.backends import StorageBackend

class S3Backend:
    def store(self, content: bytes) -> str:
        key = upload_to_s3(content)
        return key

    def fetch(self, key: str) -> bytes:
        return download_from_s3(key)

s = VeritySession("verity.json", backend=S3Backend())
```

---

## Error types

| Exception | When |
|---|---|
| `VerityReleaseError` | `release()` fails proof-chain guards |
| `VerityPushError` | `push()` called with no backend |
| `WalrusError` | Walrus HTTP call fails |
| `MemWalError` | MemWal SDK call fails |

All inherit from `VerityError` (`verity.errors`).
