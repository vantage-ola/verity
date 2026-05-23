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

`store()` calls `MemWalSync.remember_and_wait()`, which sends the registry JSON to the MemWal relayer. The relayer handles encryption and uploads to Walrus server-side. It returns a Walrus blob ID.

`fetch()` goes **directly to the Walrus aggregator** — no relayer round-trip needed. MemWal blob IDs are Walrus blob IDs, so the aggregator can serve them directly.
