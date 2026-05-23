# Scripts

Helper scripts in `scripts/` that are useful outside the main verity CLI.

---

## `scripts/store_project_context.py`

Stores verity's own project context in MemWal so any AI agent can recall full project knowledge without needing context pasting.

### What it stores

Seven memories under the `verity-project` namespace:

| Memory | Contents |
|---|---|
| verity overview | What verity is, the blob_id handoff model, PyPI package name |
| proof-chain model | feature → claim → test → evidence → release, fail-closed semantics |
| storage design | Walrus primary (unencrypted blobs), MemWal semantic discovery index |
| tech stack | Python 3.11+, pydantic v2, typer, httpx, python-dotenv, memwal SDK |
| current status | Version, test count, coverage, hackathon context |
| key decisions | MemWal Option A rationale, canonical JSON, fail-closed releases, dotenv placement |
| repo layout | All top-level directories and what lives in each |

### Setup

Requires MemWal credentials (see [MemWal Setup](memwal.md)):

```bash
export MEMWAL_KEY="<ed25519-delegate-key-hex>"
export MEMWAL_ACCOUNT_ID="<your-account-id>"
```

Or add them to a `.env` file — the script loads it automatically.

### Run

```bash
pip install "walrus-verity[memwal]"
python scripts/store_project_context.py
```

Expected output:

```
Connecting to MemWal (https://relayer.memwal.ai) namespace='verity-project' ...
  storing: 'verity overview' ... OK
  storing: 'verity proof-chain model' ... OK
  storing: 'verity storage design' ... OK
  storing: 'verity tech stack' ... OK
  storing: 'verity current status' ... OK
  storing: 'verity key decisions' ... OK
  storing: 'verity repo layout' ... OK

Stored 7 memories in namespace 'verity-project'.
Any agent can now recall('verity') and arrive with full project context.
```

### Recall in any agent

After running the script, any agent with MemWal access can retrieve the context:

```python
from memwal import MemWalSync

client = MemWalSync.create(
    key="<key>",
    account_id="<account_id>",
    server_url="https://relayer.memwal.ai",
    namespace="verity-project",
)

results = client.recall("verity proof chain model")
for r in results:
    print(r.content)
```

The script is safe to re-run — MemWal deduplicates memories by content proximity.
