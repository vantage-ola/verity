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

**store()** uploads the registry blob to Walrus directly (unencrypted, content-addressed), then registers a short semantic pointer in MemWal:

```
"verity registry blob_id=<id> repo=<repo_id>"
```

This lets any agent with MemWal access discover your registries via `recall("verity registry for repo:X")`. The MemWal registration is non-fatal — if the relayer is down, the blob is already safely on Walrus.

**fetch()** retrieves the blob directly from the Walrus aggregator — no MemWal round-trip needed. The `blob_id` returned by `push()` is a standard Walrus blob ID, readable by any Walrus client regardless of how it was pushed.

**Why not store encrypted in MemWal?** MemWal encrypts content with SEAL before writing to Walrus, so a direct Walrus fetch returns ciphertext. verity needs deterministic JSON round-trips, so it keeps the registry unencrypted on Walrus and uses MemWal only for the discovery layer.
