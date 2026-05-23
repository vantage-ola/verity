# verity

**A proof-chain registry for AI agents — backed by Walrus for persistent, portable, verifiable memory.**

[![CI](https://github.com/vantage-ola/verity/actions/workflows/ci.yml/badge.svg)](https://github.com/vantage-ola/verity/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/verity.svg)](https://badge.fury.io/py/verity)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

verity gives AI agents structured, portable memory:

```
feature → claim → test → evidence → release
                                       │
                              verity push ──► Walrus blob ID (immutable)
                              verity pull ◄── restore anywhere, any agent
```

Two things in one:

1. **Proof-chain registry** — track what an agent claimed, what it tested, and what it proved, all in a single `verity.json` file.
2. **Agent memory layer** — push the registry to [Walrus](https://docs.walrus.site) (or [MemWal](https://memwal.io)) and pull it back in any future session, on any machine, by any agent.

Built for the **Sui Overflow hackathon, Walrus track**.

---

## Install

```bash
pip install walrus-verity
```

With MemWal support:

```bash
pip install "walrus-verity[memwal]"
```

Development install:

```bash
git clone https://github.com/vantage-ola/verity
cd verity
uv venv && uv pip install -e ".[dev]"
```

---

## Quick start (60 seconds)

```bash
# 1. Initialise a registry in your project
verity init --repo-id repo:my-project

# 2. Build a proof chain
verity add feature feat:auth "User authentication"
verity add claim   clm:auth.t1 "Login succeeds" --feature feat:auth
verity add test    tst:auth.unit "Unit login test" --claim clm:auth.t1 --kind unit --path tests/test_auth.py
verity add evidence evd:auth.run1 "CI run #1" --test tst:auth.unit --artifact artifacts/run1.json --status passed

# 3. Validate all links
verity validate   # → OK

# 4. Cut a release (fail-closed — all verified claims need passed evidence)
verity release 0.1.0

# 5. Push to Walrus
verity push
# → blob: AbCdEfGhIjKlMnOpQrStUvWxYz…

# 6. In any future session, on any machine:
verity pull AbCdEfGhIjKlMnOpQrStUvWxYz…
```

---

## CLI reference

### `verity init`

Create `verity.json` in the current directory (or a target directory).

```
verity init [DIRECTORY] [--repo-id REPO_ID]
```

| Argument / Option | Default | Description |
|---|---|---|
| `DIRECTORY` | `.` | Where to create `verity.json` |
| `--repo-id` | `repo:default` | Registry identifier |

```bash
verity init
verity init /path/to/project --repo-id repo:my-app
```

---

### `verity add`

Add an entity to the registry. All IDs must use the correct prefix.

#### `verity add feature`

```
verity add feature ID TITLE
```

| ID prefix | Example |
|---|---|
| `feat:` | `feat:auth`, `feat:supplier.quality` |

```bash
verity add feature feat:auth "User authentication"
```

#### `verity add claim`

```
verity add claim ID TITLE --feature FEAT_ID [--tier T1|T2|T3]
```

```bash
verity add claim clm:auth.t1 "Login succeeds" --feature feat:auth
verity add claim clm:auth.t2 "Session expires" --feature feat:auth --tier T2
```

#### `verity add test`

```
verity add test ID TITLE --claim CLM_ID [--kind unit|integration] [--path PATH]
```

```bash
verity add test tst:auth.unit "Login unit test" --claim clm:auth.t1 --kind unit --path tests/test_auth.py
```

#### `verity add evidence`

```
verity add evidence ID TITLE --test TST_ID [--artifact PATH] [--status passed|failed|collected]
```

```bash
verity add evidence evd:auth.run1 "CI run #42" --test tst:auth.unit --artifact artifacts/run1.json --status passed
```

---

### `verity validate`

Check all links, required fields, and status consistency. Exits non-zero on any error.

```bash
verity validate
# OK
# or:
#   clm:auth.t1 references unknown feature feat:missing
#   1 error(s) found.
```

Checks performed:
- Broken links (claim→feature, test→claim, evidence→test, release→claim)
- Duplicate IDs within each entity type
- Verified claims must have at least one linked test
- Passing tests must have at least one linked evidence

---

### `verity release`

Create a named release snapshot. **Fail-closed**: every verified claim must have at least one passing test with passed evidence, or the command aborts.

```
verity release VERSION
```

```bash
verity release 0.1.0
# Released rel:0.1.0 at 2025-01-15T10:30:00Z
#   claims: clm:auth.t1, clm:auth.t2
```

The release is written to `verity.json` as a `releases` entry with `walrus_blob_id: null` until you run `verity push`.

---

### `verity push`

Serialize the registry to canonical JSON and upload to Walrus (or MemWal). Prints the blob ID and records it in the latest release row and in the push log.

```
verity push [--epochs N] [--backend walrus|memwal]
```

| Option | Default | Description |
|---|---|---|
| `--epochs` | `5` | Walrus storage duration in epochs |
| `--backend` | `walrus` | Storage backend to use |

```bash
verity push
# blob: AbCdEfGhIjKlMnOpQrStUvWxYz…

verity push --epochs 10 --backend walrus
verity push --backend memwal   # requires MEMWAL_KEY and MEMWAL_ACCOUNT_ID
```

---

### `verity pull`

Fetch a registry blob by ID and write it to `verity.json`. Creates the file if it doesn't exist.

```
verity pull BLOB_ID [--dir DIRECTORY] [--backend walrus|memwal]
```

```bash
verity pull AbCdEfGhIjKlMnOpQrStUvWxYz…
# Restored registry from AbCdEfGhIjKlMnOpQrStUvWxYz…
#   3 feature(s), 5 claim(s), 1 release(s)
```

---

### `verity log`

List all push operations recorded in the registry.

```bash
verity log
#   1.  [walrus]  2025-01-15T10:30:00Z  AbCdEfGhIjKlMnOpQrStUvWxYz…
#   2.  [walrus]  2025-01-16T09:15:00Z  XyZaBcDeFgHiJkLmNoPqRsTuVw…
```

---

## Python API

Use verity directly in Python — no subprocess needed. Designed for agents that need to manage their proof chain programmatically.

```python
from verity import VeritySession, WalrusBackend, MemWalBackend

# Open (or create) a session
s = VeritySession("verity.json", backend=WalrusBackend())

# First time: initialise
s.init(repo_id="repo:my-agent")

# Build the proof chain
s.add_feature("feat:summarise", "Summarise documents")
s.add_claim("clm:summarise.t1", "Summary is accurate",
            feature_id="feat:summarise", tier="T1", status="verified")
s.add_test("tst:summarise.eval", claim_id="clm:summarise.t1",
           kind="integration", path="evals/test_summary.py", status="passing")
s.add_evidence("evd:summarise.run1", test_id="tst:summarise.eval",
               artifact_path="evals/results.json", status="passed")

# Validate before releasing
errors = s.validate()
assert errors == [], errors

# Cut a release
release = s.release("1.0.0")
print(release.id, release.timestamp)

# Push to Walrus — returns the blob ID
blob_id = s.push()
print(f"Pushed: {blob_id}")

# Later, in a new session or a different agent:
s2 = VeritySession("verity.json", backend=WalrusBackend())
s2.pull(blob_id)
print(s2.registry().repo_id)   # → "repo:my-agent"

# Show push history
for entry in s2.log():
    print(entry.blob_id, entry.timestamp, entry.backend)
```

### `VeritySession` reference

| Method | Description |
|---|---|
| `init(repo_id)` | Create `verity.json`; raises `FileExistsError` if exists |
| `add_feature(id, title, status?)` | Append a Feature |
| `add_claim(id, title, *, feature_id, tier?, status?)` | Append a Claim |
| `add_test(id, *, claim_id, kind?, path?, status?)` | Append a Test |
| `add_evidence(id, *, test_id, artifact_path, kind?, status?)` | Append Evidence |
| `validate()` | Returns `list[str]` of errors (empty = clean) |
| `release(version)` | Fail-closed release; raises `VerityReleaseError` |
| `push(epochs?)` | Upload via backend; returns blob ID |
| `pull(blob_id)` | Download and overwrite local registry |
| `log()` | Returns `list[PushRecord]` |
| `registry()` | Returns the current `Registry` object |

---

## Walrus setup

verity uses the [Walrus HTTP API](https://docs.walrus.site) directly. No Sui SDK required.

### Testnet (default)

Works out of the box — no configuration needed:

```bash
verity push    # uses testnet publisher and aggregator
```

Default endpoints:
- Publisher: `https://publisher.walrus-testnet.walrus.space`
- Aggregator: `https://aggregator.walrus-testnet.walrus.space`

### Custom / mainnet endpoints

Use `WalrusBackend` in the Python API:

```python
from verity import VeritySession, WalrusBackend

backend = WalrusBackend(
    publisher_url="https://publisher.walrus.space",
    aggregator_url="https://aggregator.walrus.space",
    epochs=10,
)
s = VeritySession("verity.json", backend=backend)
```

---

## MemWal setup

[MemWal](https://memwal.io) is a Walrus-backed memory layer built for AI agents. It adds delegate-key authentication, namespace isolation, and semantic recall on top of Walrus storage.

### Install

```bash
pip install "walrus-verity[memwal]"
# or:
pip install memwal
```

### Configure

Set these environment variables (or create a `.env` file):

```bash
export MEMWAL_KEY="<ed25519-delegate-key-hex>"       # required
export MEMWAL_ACCOUNT_ID="<your-memwal-account-id>" # required
export MEMWAL_SERVER_URL="https://relayer.memwal.ai" # optional (default: prod)
export MEMWAL_NAMESPACE="my-project"                # optional (default: verity)
export MEMWAL_ENV="prod"                            # optional: prod|dev|staging|local
```

Get a delegate key at [memwal.io](https://memwal.io).

### Use

```bash
verity push --backend memwal
verity pull <blob-id> --backend memwal
```

In Python:

```python
from verity import VeritySession, MemWalBackend

s = VeritySession("verity.json", backend=MemWalBackend())
blob_id = s.push()
```

**How it works**: verity stores the registry via the MemWal relayer (`remember_and_wait`), which handles encryption and Walrus upload server-side. The relayer returns a Walrus blob ID. Fetching goes directly to the Walrus aggregator — no relayer round-trip needed.

---

## `verity.json` schema

Everything lives in one file. Keys are always sorted; format is compact canonical JSON (safe to hash).

```json
{
  "schema_version": "0.1.0",
  "repo_id": "repo:my-project",
  "features": [
    { "id": "feat:auth", "title": "User authentication", "status": "active" }
  ],
  "claims": [
    {
      "id": "clm:auth.t1",
      "feature_id": "feat:auth",
      "title": "Login succeeds",
      "tier": "T1",
      "status": "verified"
    }
  ],
  "tests": [
    {
      "id": "tst:auth.unit",
      "claim_id": "clm:auth.t1",
      "kind": "unit",
      "path": "tests/test_auth.py",
      "status": "passing"
    }
  ],
  "evidence": [
    {
      "id": "evd:auth.run1",
      "test_id": "tst:auth.unit",
      "kind": "test_run",
      "artifact_path": "artifacts/run1.json",
      "status": "passed"
    }
  ],
  "releases": [
    {
      "id": "rel:0.1.0",
      "version": "0.1.0",
      "timestamp": "2025-01-15T10:30:00Z",
      "walrus_blob_id": "AbCdEfGhIjKlMnOpQrStUvWxYz…",
      "claim_ids": ["clm:auth.t1"]
    }
  ],
  "pushes": [
    {
      "blob_id": "AbCdEfGhIjKlMnOpQrStUvWxYz…",
      "timestamp": "2025-01-15T10:30:00Z",
      "backend": "walrus"
    }
  ]
}
```

### ID prefixes

| Entity | Prefix | Example |
|---|---|---|
| Feature | `feat:` | `feat:auth` |
| Claim | `clm:` | `clm:auth.t1` |
| Test | `tst:` | `tst:auth.unit` |
| Evidence | `evd:` | `evd:auth.run1` |
| Release | `rel:` | `rel:0.1.0` |

### Status values

| Entity | Valid statuses |
|---|---|
| Feature | `active`, `deprecated`, `retired` |
| Claim | `open`, `verified`, `rejected` |
| Test | `pending`, `passing`, `failing` |
| Evidence | `collected`, `passed`, `failed` |

### Claim tiers

| Tier | Meaning |
|---|---|
| `T1` | Direct verification — unit tests, direct assertions |
| `T2` | Indirect verification — integration tests, logs |
| `T3` | Circumstantial — documentation, review sign-offs |

---

## Running tests

```bash
# All tests
uv run pytest

# With coverage report in the terminal
uv run pytest --cov=src/verity --cov-report=term-missing

# With HTML coverage report (opens htmlcov/index.html)
uv run pytest --cov=src/verity --cov-report=html

# Specific test file
uv run pytest tests/test_session.py -v

# Fail if coverage drops below threshold (85%)
uv run pytest --cov=src/verity --cov-fail-under=85
```

Current coverage by module:

| Module | Coverage |
|---|---|
| `models.py` | ~99% |
| `registry.py` | ~93% |
| `validate.py` | ~97% |
| `release.py` | 100% |
| `walrus.py` | 100% |
| `memwal.py` | ~95% |
| `session.py` | ~96% |
| `cli/main.py` | ~85% |

---

## Publishing to PyPI

### One-time setup

1. **Create a PyPI account** at [pypi.org](https://pypi.org) if you don't have one.

2. **Set up Trusted Publishing** (recommended — no API tokens needed):
   - Go to [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing)
   - Add a new publisher: GitHub Actions, your repo, workflow `publish.yml`, environment `pypi`

3. **Create the `pypi` environment** in your GitHub repo:
   - Repo Settings → Environments → New environment → name it `pypi`
   - Optionally require reviewers before publishing

### Release a new version

```bash
# 1. Update version in pyproject.toml
#    version = "0.2.0"

# 2. Update CHANGELOG.md

# 3. Commit
git add pyproject.toml CHANGELOG.md
git commit -m "Release 0.2.0"

# 4. Tag — this triggers the publish workflow
git tag v0.2.0
git push origin main --tags
```

The `publish.yml` workflow will:
1. Build the wheel and sdist with `uv build`
2. Publish to PyPI using OIDC (no token required)
3. Create a GitHub Release with the built artifacts

### Manual publish (fallback)

```bash
# Build
uv build

# Upload (requires PYPI_API_TOKEN or ~/.pypirc)
uv publish
# or:
pip install twine
twine upload dist/*
```

---

## Project structure

```
verity/
├── pyproject.toml         # packaging, deps, pytest/coverage config
├── LICENSE
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── examples/
│   └── demo_multi_agent.py   # two-agent demo script
├── src/
│   └── verity/
│       ├── __init__.py        # public API exports
│       ├── models.py          # pydantic v2 models (Feature, Claim, …, Registry)
│       ├── registry.py        # load_registry / save_registry / canonical_json
│       ├── validate.py        # validation guards → list[str]
│       ├── release.py         # create_release (fail-closed)
│       ├── backends.py        # StorageBackend protocol
│       ├── walrus.py          # WalrusBackend + module-level push/pull helpers
│       ├── memwal.py          # MemWalBackend (real SDK)
│       ├── session.py         # VeritySession high-level Python API
│       └── cli/
│           └── main.py        # typer CLI entry point
└── tests/
    ├── conftest.py            # minimal_registry fixture
    ├── test_models.py
    ├── test_validate.py
    ├── test_release.py
    ├── test_walrus.py
    ├── test_memwal.py
    ├── test_session.py
    └── test_cli.py
```

---

## Why Walrus

| Walrus property | What it gives verity |
|---|---|
| Immutable blobs | Every `verity push` is a tamper-evident, timestamped snapshot |
| Portable blob IDs | Any agent, any session, any machine can retrieve the same context |
| Verifiable storage | Claims and evidence are auditable, not just self-reported |
| No platform lock-in | `verity.json` is plain JSON; Walrus stores it without transformation |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
