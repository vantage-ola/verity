# verity Agent Skill

Use this skill when an AI agent needs to build, maintain, or share a **proof chain** — a structured, verifiable record of what a system claims, what tests exercise those claims, and what evidence backs them up. The chain is persisted to [Walrus](https://docs.walrus.site) or [MemWal](https://memwal.ai) so any other agent can pull it and continue the work.

## What verity is

verity is a lightweight proof-chain registry. It models five entity types:

| Entity   | ID prefix | What it represents |
|----------|-----------|-------------------|
| Feature  | `feat:`   | A unit of capability being verified |
| Claim    | `clm:`    | An assertion that a feature meets a quality bar |
| Test     | `tst:`    | A test that exercises a claim |
| Evidence | `evd:`    | A concrete artifact (run result, audit log) that proves a test passed |
| Release  | `rel:`    | A versioned snapshot of verified claims |

A proof chain is valid when every `verified` claim has a linked `passing` test, and every passing test has a linked `passed` evidence artifact. Releases are fail-closed — no partial certification.

Proof chains are persisted to **Walrus** (content-addressed blob storage on Sui) and identified by a `blob_id`. Any agent that receives a `blob_id` can pull the full chain and continue from there.

---

## Install

```bash
pip install verity
# or with MemWal support
pip install "verity[memwal]"
```

---

## CLI quick reference

### Initialise a registry

```bash
verity init                                 # creates verity.json in cwd
verity init --repo-id repo:my-project       # explicit repo ID
```

### Add entities

```bash
verity add feature feat:auth "User authentication"
verity add claim   clm:auth.login "Login succeeds" --feature feat:auth --tier T1
verity add test    tst:auth.unit  "Login unit test" --claim clm:auth.login --kind unit --path tests/test_auth.py
verity add evidence evd:auth.ci   "CI run"          --test  tst:auth.unit  --artifact reports/auth.json --status passed
```

### Inspect and validate

```bash
verity validate          # prints errors or "OK"
```

### Cut a release

```bash
verity release 1.0.0     # fail-closed; all verified claims must have passed evidence
```

### Push to Walrus / pull from Walrus

```bash
# push (Walrus testnet by default)
verity push                         # returns blob_id
verity push --backend memwal        # push via MemWal SDK

# pull (restore a registry from a blob_id)
verity pull <blob_id>
verity pull <blob_id> --backend memwal

# push history
verity log
```

---

## Python API quick reference

```python
from verity import VeritySession, WalrusBackend

# Agent A — build a proof chain
s = VeritySession("verity.json", backend=WalrusBackend())
s.init(repo_id="repo:my-project")

s.add_feature("feat:auth", "User authentication")
s.add_claim("clm:auth.login", "Login succeeds", feature_id="feat:auth", tier="T1", status="verified")
s.add_test("tst:auth.unit", claim_id="clm:auth.login", kind="unit", path="tests/test_auth.py", status="passing")
s.add_evidence("evd:auth.ci", test_id="tst:auth.unit", artifact_path="reports/auth.json", status="passed")

errors = s.validate()               # [] means clean
rel = s.release("1.0.0")            # raises VerityReleaseError if guards fail
blob_id = s.push()                  # returns Walrus blob ID

# Agent B — pull and audit
s2 = VeritySession("verity_audit.json", backend=WalrusBackend())
s2.pull(blob_id)                    # restores full chain from Walrus
s2.add_evidence("evd:auth.audit", test_id="tst:auth.unit", artifact_path="audit/sign-off.json", status="passed")
new_blob_id = s2.push()             # publishes audited chain

log = s2.log()                      # list[PushRecord] — timestamp, backend, blob_id
```

---

## Entity rules

### ID prefixes (enforced at model level)
- `feat:` — Feature
- `clm:`  — Claim
- `tst:`  — Test
- `evd:`  — Evidence
- `rel:`  — Release

### Status values

| Entity   | Allowed statuses |
|----------|-----------------|
| Feature  | `active`, `deprecated`, `retired` |
| Claim    | `open`, `verified`, `rejected` |
| Test     | `pending`, `passing`, `failing` |
| Evidence | `collected`, `passed`, `failed` |

### Tiers
Claims carry a tier (`T1`, `T2`, `T3`) indicating assurance strength. Use `T1` for direct verification (tests + evidence). `T2`/`T3` for layered assurance.

### Validation guards

`validate()` returns a list of error strings. It checks:
- Duplicate IDs within each entity family
- Broken foreign-key links (claim → feature, test → claim, evidence → test, release → claim)
- Status consistency: every `verified` claim must have a linked test; every `passing` test must have linked evidence

### Release guards

`release(version)` raises `VerityReleaseError` (never creates a partial release) if:
- There are no claims with `status="verified"`
- Any verified claim has no linked test with `status="passing"`
- Any passing test has no linked evidence with `status="passed"`

---

## Storage backends

### Walrus (default)

```python
from verity import WalrusBackend
backend = WalrusBackend(
    publisher_url="https://publisher.walrus-testnet.walrus.space",
    aggregator_url="https://aggregator.walrus-testnet.walrus.space",
)
```

Environment variables for the CLI:
```
WALRUS_PUBLISHER_URL=https://publisher.walrus-testnet.walrus.space
WALRUS_AGGREGATOR_URL=https://aggregator.walrus-testnet.walrus.space
```

### MemWal

```python
from verity import MemWalBackend
backend = MemWalBackend()   # reads from environment
```

Environment variables:
```
MEMWAL_KEY=<api-key>
MEMWAL_ACCOUNT_ID=<account-id>
MEMWAL_SERVER_URL=https://relayer.memwal.ai
MEMWAL_NAMESPACE=<optional-namespace>
MEMWAL_ENV=production
```

### Custom backend (Protocol)

```python
from verity.backends import StorageBackend

class MyBackend:
    def store(self, content: bytes) -> str:
        # persist content, return a key/ID
        ...
    def fetch(self, key: str) -> bytes:
        # retrieve content by key
        ...
```

Any object that implements `store(bytes) -> str` and `fetch(str) -> bytes` is accepted.

---

## Multi-agent workflow pattern

```
Agent A                           Agent B
  │                                  │
  ├─ init / build proof chain        │
  ├─ validate()                      │
  ├─ release("0.1.0")                │
  ├─ push() ──── blob_id ──────────► │
  │                                  ├─ pull(blob_id)
  │                                  ├─ add_evidence(...)   # audit / extend
  │                                  ├─ release("1.0.0")
  │                                  ├─ push() ──► new_blob_id
  │                                  └─ log()  # full push trail
```

The `blob_id` is the handoff token. Pass it via any channel (env var, Slack, issue comment, task metadata).

---

## verity.json schema

```json
{
  "schema_version": "0.1.0",
  "repo_id": "repo:<name>",
  "features":  [{ "id": "feat:...", "title": "...", "status": "active" }],
  "claims":    [{ "id": "clm:...", "title": "...", "feature_id": "feat:...", "tier": "T1", "status": "open" }],
  "tests":     [{ "id": "tst:...", "claim_id": "clm:...", "kind": "unit|integration", "path": "...", "status": "pending" }],
  "evidence":  [{ "id": "evd:...", "test_id": "tst:...", "kind": "test_run", "artifact_path": "...", "status": "collected" }],
  "releases":  [{ "id": "rel:...", "version": "...", "timestamp": "...", "claim_ids": [...], "walrus_blob_id": "..." }],
  "pushes":    [{ "blob_id": "...", "timestamp": "...", "backend": "walrus|memwal" }]
}
```

---

## Common agent patterns

### Pattern 1 — Track feature proof before shipping

1. `add_feature` → `add_claim` → `add_test` → `add_evidence`
2. `validate()` — fix any errors
3. `release(version)` — cut a release
4. `push()` — publish to Walrus, record `blob_id`

### Pattern 2 — Extend another agent's chain

1. `pull(blob_id)` — restore chain from Walrus
2. `validate()` — confirm it's clean before adding to it
3. `add_evidence(...)` or `add_claim(...)` — add your contribution
4. `release(version)` — new release
5. `push()` — publish updated chain

### Pattern 3 — Audit trail only

1. `pull(blob_id)` — restore chain
2. `validate()` — report findings without mutating
3. `log()` — inspect push history

### Pattern 4 — Dry run / in-memory (no Walrus)

```python
from unittest.mock import MagicMock
backend = MagicMock()
backend.store.return_value = "blob-mock-123"
backend.fetch.return_value = b'{...}'
s = VeritySession("verity.json", backend=backend)
```

---

## Error types

| Exception | When it's raised |
|-----------|-----------------|
| `VerityReleaseError` | `release()` called when proof-chain guards fail |
| `VerityPushError`    | `push()` called with no backend configured |
| `WalrusError`        | Walrus HTTP call fails |
| `MemWalError`        | MemWal SDK call fails |

All errors are subclasses of `VerityError` from `verity.errors`.

---

## Operating rules for agents

1. Always call `validate()` before `release()` — report errors to the user if found.
2. Never construct a `Release` directly; always use `s.release(version)` or `verity release <version>`.
3. Pass `blob_id` as the handoff token between agents — it identifies a specific immutable state of the chain on Walrus.
4. After a `pull()`, validate before adding new entities to confirm the restored chain is clean.
5. IDs must be unique within their family. Prefer `<namespace>.<entity>.<qualifier>` patterns (`clm:auth.login.t1`).
6. Never re-use a `rel:` ID for a different version — releases are immutable records.
