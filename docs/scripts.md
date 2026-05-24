# Scripts

Helper scripts in `scripts/` that are useful outside the main verity CLI.

---

## `scripts/store_project_context.py`

Syncs `verity.json` context entries to MemWal so any AI agent can `recall("verity")` and arrive with full project knowledge — no context pasting required.

### The workflow

Context entries live in `verity.json` under the `context` field. You manage them with the CLI:

```bash
verity context set architecture "5-layer proof chain: feature → claim → test → evidence → release"
verity context set decisions "chose MemWal Option A — blobs on Walrus, MemWal for discovery only"
verity context set stack "Python 3.11+, pydantic v2, typer, httpx, walrus-verity on PyPI"
```

Then sync them to MemWal in one of two ways:

**Option 1 — automatic (recommended):** push via MemWal backend, context entries are stored alongside the registry pointer:
```bash
verity push --backend memwal
```

**Option 2 — manual:** run the script directly for a standalone sync without a full push:
```bash
python scripts/store_project_context.py
```

### Setup

Requires MemWal credentials (see [MemWal Setup](memwal.md)):

```bash
export MEMWAL_KEY="<ed25519-delegate-key-hex>"
export MEMWAL_ACCOUNT_ID="<your-account-id>"
```

Or add them to a `.env` file — the script loads it automatically.

```bash
pip install "walrus-verity[memwal]"
```

### Run

```bash
python scripts/store_project_context.py
```

Expected output:

```
Connecting to MemWal (https://relayer.memwal.ai) namespace='verity-project' ...
  storing: 'architecture' ... OK
  storing: 'decisions' ... OK
  storing: 'stack' ... OK

Stored 3 context entries for repo='repo:my-project'.
Any agent can now recall('verity') and arrive with full project context.
```

If no context entries are in `verity.json`:

```
No context entries in verity.json.
Add some with: verity context set KEY 'your narrative here'
```

### Recall in any agent

After syncing, any agent with MemWal access can retrieve the context:

```python
from memwal import MemWalSync

client = MemWalSync.create(
    key="<key>",
    account_id="<account_id>",
    server_url="https://relayer.memwal.ai",
    namespace="verity-project",
)

results = client.recall("verity architecture")
for r in results:
    print(r.content)
```

The script is safe to re-run — MemWal deduplicates memories by content proximity.
