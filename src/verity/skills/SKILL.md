# verity

Use this skill when working with the `verity` proof-chain registry — building chains, running the CLI, writing Python sessions, or reasoning about multi-agent handoffs.

**Package**: `walrus-verity` on PyPI  
**Repo**: `~/work/verity/`  
**Version**: 0.3.5

---

## Core concept

Every verity workflow produces one chain:

```
feature → claim → test → evidence → release
                                       │
                              verity push ──► Walrus blob ID (immutable)
```

- **feature** — a capability being shipped
- **claim** — a testable statement about the feature
- **test** — the mechanism that exercises the claim
- **evidence** — the pass/fail signal the test produced
- **release** — a named snapshot; `push()` publishes it to Walrus

---

## CLI reference

```bash
# Init
verity init --repo-id repo:my-project

# Quick-track — one command, full chain (claim+test+evidence)
verity track feat:auth tests/test_auth.py            # --status passed (default)
verity track feat:auth tests/test_auth.py --status failed
verity track feat:auth tests/test_auth.py --title "Login succeeds"

# Build the chain manually (full control over IDs/tiers/statuses)
verity add feature feat:auth "User authentication"
verity add claim   clm:auth.t1 "Login succeeds" --feature feat:auth --status verified
verity add test    tst:auth.unit "Unit test" --claim clm:auth.t1 --path tests/test_auth.py --status passing
verity add evidence evd:auth.ci "CI run" --test tst:auth.unit --artifact reports/ci.json --status passed

# Validate, release, push
verity validate
verity release 1.0.0
verity push                        # Walrus (default)
verity push --backend memwal       # Walrus + MemWal semantic pointer

# Recall from MemWal (natural language query)
verity recall "what features have we built"
verity recall "what claims are verified"
verity recall "what was the latest release"
verity recall "architecture of this project"
verity recall "what features have we built" --namespace my-project

# Sign and verify blobs (requires pip install "walrus-verity[sign]")
verity keygen --key ~/.verity/signing.key       # generate Ed25519 keypair
verity sign --key ~/.verity/signing.key         # sign latest push, embed sig in verity.json
verity push                                      # re-publish with signature
verity verify <blob_id>                         # fetch + validate chain
verity verify <blob_id> --pubkey-b64 <b64>      # + check signature

# Diff two Walrus blob snapshots
verity diff <blob_a> <blob_b>
# + feat:new  "New feature" (active)
# ~ clm:auth.t1  open → verified
# 1 added, 1 changed, 0 removed

# Export to standard DevSecOps formats
verity export --format sarif                         # SARIF 2.1.0 JSON
verity export --format junit                         # JUnit XML
verity export --format spdx                          # SPDX-2.3 JSON
verity export --format sarif --output verity.sarif   # write to file

# Inspect
verity log
verity status
```

---

## Python API

```python
from verity import VeritySession, WalrusBackend, MemWalBackend

v = VeritySession("verity.json", backend=WalrusBackend())
v.init(repo_id="repo:my-project")

v.add_feature("feat:auth", "User authentication")
v.add_claim("clm:auth.t1", "Login succeeds",
            feature_id="feat:auth", status="verified")
v.add_test("tst:auth.unit", claim_id="clm:auth.t1",
           path="tests/test_auth.py", status="passing")
v.add_evidence("evd:auth.ci", test_id="tst:auth.unit",
               artifact_path="reports/ci.json", status="passed")

errors = v.validate()   # returns list; empty = clean
v.release("1.0.0")
blob_id = v.push()      # returns plain str — the Walrus blob ID

for entry in v.log():
    print(entry.blob_id, entry.timestamp, entry.backend)
```

### Key API facts
- `VeritySession` is **not** a context manager — no `with` block
- `push()` returns a **plain `str`** (the blob_id), not an object
- `backend=` is passed to the constructor, not to `push()`
- `add_claim` uses `feature_id=` (keyword), not `feature=`
- `validate()` returns a list of error strings; empty list = valid
- `registry()` returns a `Registry` object with `.features`, `.claims`, `.tests`, `.evidence`, `.releases`

---

## Backends

| Backend | Install | Use |
|---|---|---|
| `WalrusBackend` | `pip install walrus-verity` | Pushes to Walrus testnet/mainnet |
| `MemWalBackend` | `pip install "walrus-verity[memwal]"` | Walrus + MemWal semantic pointer |
| In-memory (test) | built-in | Pass a `_SharedStore` instance |

**MemWal**: `push(backend=MemWalBackend())` stores the blob on Walrus **and** registers semantic memories in MemWal (features summary, verified claims, latest release, context entries). Use `backend.recall(query)` or `verity recall "<query>"` to query them in natural language.

---

## Multi-agent handoff

```python
# Agent A — builds and publishes
a = VeritySession("agent_a/verity.json", backend=WalrusBackend())
a.init(repo_id="repo:quality-check")
# ... add features, claims, tests, evidence ...
a.validate()
a.release("0.1.0")
blob_id = a.push()   # pass this to Agent B

# Agent B — pulls, verifies, extends
b = VeritySession("agent_b/verity.json", backend=WalrusBackend())
b.pull(blob_id)
b.validate()
b.add_evidence("evd:audit", test_id="tst:...", artifact_path="audit/sign-off.json", status="passed")
b.release("1.0.0")
new_blob_id = b.push()
```

Pass `blob_id` via env var, file, task metadata, or message queue — it's a plain string.

### Dry-run (in-memory, no Walrus)

```python
class _SharedStore:
    def __init__(self): self._blobs: dict[str, bytes] = {}
    def store(self, content): key = f"blob-{len(self._blobs)}"; self._blobs[key] = content; return key
    def fetch(self, key): return self._blobs[key]

shared = _SharedStore()
a = VeritySession("agent_a/verity.json", backend=shared)
b = VeritySession("agent_b/verity.json", backend=shared)
```

---

## Environment variables

```bash
WALRUS_PUBLISHER_URL    # Walrus publisher endpoint
WALRUS_AGGREGATOR_URL   # Walrus aggregator endpoint
MEMWAL_API_URL          # MemWal API endpoint
MEMWAL_API_KEY          # MemWal API key
```

Auto-loaded from `.env` via `python-dotenv` when present.

---

## Operating rules

- **Update `verity.json` after every feature, fix, or code change.** If you added a feature, add `feat:` + `clm:` + `tst:` + `evd:`. If you fixed a bug, add or update the relevant evidence. If you wrote tests, link them. The proof chain must reflect what actually exists in the repo.
- Always validate before release: `v.validate()` or `verity validate`
- `blob_id` is immutable — it always resolves to the exact state that was pushed
- Agent B's push creates a **new** blob; it does not overwrite Agent A's
- The chain file (`verity.json`) is local state; the blob on Walrus is the portable artifact
- Tests live at `tests/` — run with `uv run pytest`

## Correct order when building the chain via CLI

verity validates on every write. **Always add entities with neutral statuses first, then promote statuses once the chain is fully linked.**

```bash
# correct — neutral statuses first
verity add feature feat:x "My feature"
verity add claim   clm:x.t1 "My claim"  --feature feat:x        # open (default)
verity add test    tst:x.unit "My test" --claim clm:x.t1         # pending (default)
verity add evidence evd:x.ci "CI run"   --test tst:x.unit        # collected (default)

# then promote
# patch verity.json or re-add with --status, then verity validate
```

**Never set a promoted status before the chain is wired:**
- `--status verified` on a claim requires a linked passing test to already exist
- `--status passing` on a test requires linked passed evidence to already exist

Adding them out of order causes validation to fail and the write is rejected.
