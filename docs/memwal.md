# MemWal Setup

[MemWal](https://memwal.ai) is a Walrus-backed memory layer for AI agents. It adds delegate-key auth, namespace isolation, and semantic recall on top of Walrus.

## Install

```bash
pip install "walrus-verity[memwal]"
# or separately:
pip install memwal
```

## Configure

```bash
export MEMWAL_KEY="<ed25519-delegate-key-hex>"        # required
export MEMWAL_ACCOUNT_ID="<your-account-id>"          # required
export MEMWAL_SERVER_URL="https://relayer.memwal.ai"  # default: prod relayer
export MEMWAL_NAMESPACE="my-project"                  # default: verity
export MEMWAL_ENV="production"                        # production | dev | staging | local
```

Get a delegate key at [memwal.ai](https://memwal.ai).

## Use

### CLI

```bash
verity push --backend memwal
verity pull <blob-id> --backend memwal
```

### Python

```python
from verity import VeritySession, MemWalBackend

s = VeritySession("verity.json", backend=MemWalBackend())
blob_id = s.push()

# Restore in a different session
s2 = VeritySession("verity_restored.json", backend=MemWalBackend())
s2.pull(blob_id)
```

You can also pass credentials explicitly instead of reading from env:

```python
backend = MemWalBackend(
    key="<delegate-key>",
    account_id="<account-id>",
    server_url="https://relayer.memwal.ai",
    namespace="my-project",
)
```

## How it works

**store()** uploads the registry blob to Walrus directly (unencrypted, content-addressed), then registers five kinds of memories in MemWal:

1. A registry pointer so agents can discover registries by repo:
   ```
   "verity registry blob_id=<id> repo=<repo_id>"
   ```

2. One memory per context entry (see `verity context set`):
   ```
   "verity context key=architecture repo=<repo_id>: 5-layer proof chain…"
   "verity context key=decisions repo=<repo_id>: chose MemWal Option A…"
   ```

3. A features summary listing all feature titles, IDs, and statuses:
   ```
   "verity features repo=<repo_id>: User Auth (feat:auth, active); Data Export (feat:export, deprecated)"
   ```

4. A verified-claims summary listing only claims with `status=verified`:
   ```
   "verity verified-claims repo=<repo_id>: Login works (clm:auth.t1, T1); …"
   ```

5. A latest-release summary with version, timestamp, and claim count:
   ```
   "verity latest-release repo=<repo_id> version=0.1.0 at=2025-01-01T00:00:00Z: 5 claims"
   ```

All MemWal registrations are non-fatal — if the relayer is down, the blob is already safely on Walrus.

**fetch()** retrieves the blob directly from the Walrus aggregator — no MemWal round-trip needed. The `blob_id` returned by `push()` is a standard Walrus blob ID, readable by any Walrus client regardless of how it was pushed.

**Why not store encrypted in MemWal?** MemWal encrypts content with SEAL before writing to Walrus, so a direct Walrus fetch returns ciphertext. verity needs deterministic JSON round-trips, so it keeps the registry unencrypted on Walrus and uses MemWal only for the discovery layer.

## Natural language recall

After pushing with `--backend memwal`, you can query your registry in plain English.

### CLI

```bash
verity recall "what features have we built"
verity recall "what claims are verified"
verity recall "what was the latest release"
verity recall "what is the architecture of this project"

# Override namespace (defaults to MEMWAL_NAMESPACE env var, then "verity")
verity recall "what features have we built" --namespace my-project
verity recall "what features have we built" -n my-project
```

The answer is synthesized by MemWal's semantic memory layer from whatever was registered during the last `verity push --backend memwal`.

### Python API

```python
from verity.memwal import MemWalBackend

backend = MemWalBackend()  # reads MEMWAL_KEY, MEMWAL_ACCOUNT_ID from env
answer = backend.recall("what features have we built")
print(answer)

# With explicit namespace
answer = backend.recall("what claims are verified", namespace="my-project")
```

`recall()` raises `MemWalError` if the relayer is unreachable or credentials are missing. Unlike `store()`, recall errors are always surfaced — there is no silent fallback.

### What gets indexed

Push a registry, then immediately ask questions about it:

```bash
verity push --backend memwal

verity recall "what features have we built"
# Returns: a natural language summary of all features with their IDs and statuses

verity recall "what claims are verified"
# Returns: all claims with status=verified, grouped by tier

verity recall "what was the latest release"
# Returns: the most recent release version, timestamp, and claim count

verity recall "what is the architecture"
# Returns: your context entries (set with `verity context set architecture "..."`)
```

The recall index is updated on every push — run `verity push --backend memwal` after changing features, claims, or releases to keep answers current.
