# CLI Reference

## `verity init`

Create `verity.json` in the current directory (or a target directory). Fails if the file already exists.

```bash
verity init
verity init /path/to/project --repo-id repo:my-app
```

| Argument / Option | Default | Description |
|---|---|---|
| `DIRECTORY` | `.` | Where to create `verity.json` |
| `--repo-id` | `repo:default` | Registry identifier |

---

## `verity add`

Add an entity to the registry. All IDs must carry the correct prefix.

> **Status rules:** verity validates after every write. Promoted statuses require the downstream chain to already exist:
> - A claim can only be `verified` if it already has a linked test.
> - A test can only be `passing` if it already has linked passed evidence.
>
> **Correct approach**: build the full chain with neutral statuses first (`open`, `pending`, `collected`), then edit `verity.json` to promote statuses, and run `verity validate`. If you prefer to set statuses at add time, use the [Python API](python-api.md) which defers validation until `validate()` or `push()`.

### `verity add feature`

```bash
verity add feature ID TITLE [--status active|deprecated|retired]
```

```bash
verity add feature feat:auth "User authentication"
```

### `verity add claim`

```bash
verity add claim ID TITLE --feature FEAT_ID [--tier T1|T2|T3] [--status open|verified|rejected]
```

```bash
# add with default status (open) — safe at any point
verity add claim clm:auth.t1 "Login succeeds" --feature feat:auth
verity add claim clm:auth.t2 "Session expires" --feature feat:auth --tier T2

# promoting to verified — only valid after a linked test exists
# do this by editing verity.json, then: verity validate
```

### `verity add test`

```bash
verity add test ID TITLE --claim CLM_ID [--kind unit|integration] [--path PATH] [--status pending|passing|failing]
```

```bash
# add with default status (pending) — safe at any point
verity add test tst:auth.unit "Login unit test" --claim clm:auth.t1 --kind unit --path tests/test_auth.py

# promoting to passing — only valid after linked passed evidence exists
# do this by editing verity.json, then: verity validate
```

### `verity add evidence`

```bash
verity add evidence ID TITLE --test TST_ID [--artifact PATH] [--status passed|failed|collected]
```

```bash
# evidence status can be set at add time — no downstream dependencies
verity add evidence evd:auth.run1 "CI run #1" --test tst:auth.unit --artifact artifacts/run1.json --status passed
```

---

## `verity track`

Auto-create a claim, test, and evidence entry for a feature in one step. The full chain is wired and validated before saving. No two-phase setup required.

```bash
verity track FEATURE_ID TEST_PATH [--status passed|failed|collected] [--title TITLE] [--kind unit|integration]
```

| Argument / Option | Default | Description |
|---|---|---|
| `FEATURE_ID` | — | Feature to track against (must already exist) |
| `TEST_PATH` | — | Path to the test file |
| `--status` | `passed` | Outcome: `passed`, `failed`, or `collected` |
| `--title` | feature title | Claim title (auto-derived from the feature if omitted) |
| `--kind` | `unit` | Test kind: `unit` or `integration` |

IDs are auto-generated from the feature slug (`feat:auth` → `clm:auth.track`, `tst:auth.track`, `evd:auth.track`). Running `track` a second time for the same feature appends `.2`, `.3`, etc.

**Status → chain mapping**

| `--status` | claim | test | evidence |
|---|---|---|---|
| `passed` | `verified` | `passing` | `passed` |
| `failed` | `open` | `failing` | `failed` |
| `collected` | `open` | `pending` | `collected` |

```bash
# record a passing test run (default)
verity track feat:auth tests/test_auth.py
# Tracked feat:auth via tests/test_auth.py
#   clm:auth.track  (verified)
#   tst:auth.track  (passing)
#   evd:auth.track  (passed)

# record a failing test
verity track feat:auth tests/test_auth.py --status failed

# record with a custom claim title
verity track feat:auth tests/test_auth.py --title "Login succeeds with valid credentials"

# record an integration test
verity track feat:auth tests/test_auth_integration.py --kind integration

# second track call for the same feature — IDs auto-increment
verity track feat:auth tests/test_auth2.py
#   clm:auth.track.2  (verified)
#   tst:auth.track.2  (passing)
#   evd:auth.track.2  (passed)
```

**When to use `track` vs `add`**

Use `track` for the common case: you ran tests, they passed, record it. Use the individual `add` commands when you need explicit IDs, custom tiers, or multi-step chains with separate claim and evidence types.

---

## `verity validate`

Check all links, required fields, and status consistency. Exits non-zero if any error is found.

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

## `verity release`

Create a named release snapshot. **Fail-closed**: every verified claim must have a passing test with passed evidence, or the command aborts.

```bash
verity release VERSION [--dir DIRECTORY]
```

```bash
verity release 1.0.0
# Released rel:1.0.0 — 3 claim(s)
```

---

## `verity push`

Serialize the registry to canonical JSON and upload to Walrus (or MemWal). Records the blob ID in the push log.

```bash
verity push [--epochs N] [--backend walrus|memwal] [--dir DIRECTORY]
```

| Option | Default | Description |
|---|---|---|
| `--epochs` | `5` | Walrus storage duration in epochs |
| `--backend` | `walrus` | Storage backend |

```bash
verity push
# blob: AbCdEfGhIjKlMnOpQrStUvWxYz…

verity push --epochs 10
verity push --backend memwal
```

---

## `verity pull`

Fetch a registry blob by ID and write it to `verity.json`.

```bash
verity pull BLOB_ID [--backend walrus|memwal] [--dir DIRECTORY]
```

```bash
verity pull AbCdEfGhIjKlMnOpQrStUvWxYz…
# Restored registry from AbCdEfGhIjKlMnOpQrStUvWxYz…
#   3 feature(s), 5 claim(s), 1 release(s)
```

---

## `verity status`

Show a compact health summary of the registry: entity counts with status breakdowns, latest release, and validation result. Exits non-zero if the registry has validation errors.

```bash
verity status [DIRECTORY]
```

**Example output**

```
repo:my-project  schema 0.1.0
features   6   claims    11  (10 verified, 1 open)
tests     11  (11 passing)
evidence  11  (11 passed)
releases   2   latest: rel:0.1.5  blob: AbCdEfGh…
valid      ✓
```

When the registry is invalid:

```
valid      ✗  (2 error(s))
```

**Use cases**

- Quick check before committing: run `verity status` to confirm everything is verified and the chain is clean
- Script integration: exits 1 on any validation error, so `verity status && git push` is a lightweight gate
- At-a-glance agent health: see how much of the chain an autonomous agent has built without parsing the full JSON

---

## `verity log`

Print all push operations recorded in the registry.

```bash
verity log [--dir DIRECTORY]
# 1.  [walrus]  2025-01-15T10:30:00Z  AbCdEfGhIjKlMnOpQrStUvWxYz…
# 2.  [walrus]  2025-01-16T09:15:00Z  XyZaBcDeFgHiJkLmNoPqRsTuVw…
```

---

## `verity site`

Generate a human-readable HTML proof page from `verity.json`. Shows every feature, claim, test, evidence entry, release, and push in a clean browseable page.

```bash
verity site [--dir DIRECTORY] [--output PATH] [--push] [--epochs N]
```

| Option | Default | Description |
|---|---|---|
| `--dir` | `.` | Directory containing `verity.json` |
| `--output` | — | Save HTML to a local file |
| `--push` | `false` | Upload HTML to Walrus and print the blob ID and viewer URL |
| `--epochs` | `5` | Walrus storage duration (only used with `--push`) |

**Save locally:**
```bash
verity site --output proof.html
# Saved to proof.html
```

**Push to Walrus and get a public URL:**
```bash
verity site --push
# blob: AbCdEfGhIjKlMnOpQrStUvWxYz…
# url:  https://aggregator.walrus-testnet.walrus.space/v1/blobs/AbCdEfGh…
```

**Save and push:**
```bash
verity site --output proof.html --push
```

**Print HTML to stdout** (no flags):
```bash
verity site
# <!DOCTYPE html>…
```

The URL format depends on whether you're using testnet or mainnet; it reads `WALRUS_AGGREGATOR_URL` from the environment (same env var used by `verity push`).

---

## `verity context`

Manage named narrative context entries stored inside `verity.json`. Context entries are free-form key/value notes (architecture decisions, current focus areas, design rationale) that travel with the proof chain and are automatically stored in MemWal when you push via `verity push --backend memwal`.

```bash
verity context set KEY VALUE [--dir DIRECTORY]
verity context list           [--dir DIRECTORY]
verity context remove KEY     [--dir DIRECTORY]
```

### `verity context set`

Upsert a context entry. If `KEY` already exists it is overwritten; otherwise a new entry is appended.

```bash
verity context set architecture "5-layer proof chain: feature → claim → test → evidence → release"
verity context set decisions "chose MemWal Option A — blobs on Walrus directly, MemWal for discovery only"
verity context set focus "current sprint: proof-chain diffing and CI/CD integration"
# Set: architecture
```

### `verity context list`

Print all context entries for the registry.

```bash
verity context list
# architecture: 5-layer proof chain: feature → claim → test → evidence → release
# decisions: chose MemWal Option A — blobs on Walrus directly, MemWal for discovery only
# focus: current sprint: proof-chain diffing and CI/CD integration
```

### `verity context remove`

Delete a context entry by key. Exits non-zero if the key is not found.

```bash
verity context remove focus
# Removed: focus
```

### How context flows into MemWal

When you run `verity push --backend memwal`, each context entry is stored as a separate MemWal memory alongside the registry pointer. Any agent with MemWal access can then retrieve it:

```
verity context key=architecture repo=repo:my-project: 5-layer proof chain…
verity context key=decisions repo=repo:my-project: chose MemWal Option A…
```

This means agents can `recall("verity architecture")` or `recall("verity decisions")` and arrive with the relevant context without any manual briefing.

---

## `verity install-skill`

Install the verity context skill into your AI coding assistant. The skill is bundled with the package and teaches the tool verity's proof chain model, CLI, Python API, and multi-agent patterns.

```bash
verity install-skill [--tool claude|cursor|windsurf|aider|codex]
```

| Option | Default | Description |
|---|---|---|
| `--tool` | `claude` | Target assistant |

### Claude Code (global)

Appends an `@` reference to `~/.claude/CLAUDE.md`. Applies to every Claude Code session automatically.

```bash
verity install-skill
# Installed for Claude Code → ~/.claude/CLAUDE.md
#   @/path/to/site-packages/verity/skills/SKILL.md
```

### Cursor, Windsurf, Codex, Aider (project-level)

Injects the skill content into the tool's config file in the current directory.

```bash
verity install-skill --tool cursor    # → .cursorrules
verity install-skill --tool windsurf  # → .windsurfrules
verity install-skill --tool codex     # → AGENTS.md
verity install-skill --tool aider     # → CONVENTIONS.md
```

Running the command a second time is safe. It detects the existing skill block and exits without duplicating it.


---

## MCP server (`verity-mcp`)

Instead of the context skill, you can expose all verity tools natively via the Model Context Protocol. Any MCP-compatible editor (Claude Code, Cursor, Windsurf, Codex) can call these tools directly without running CLI subprocesses.

### Install

```bash
pip install "walrus-verity[mcp]"
```

### Configure

Add to `claude_mcp_config.json` (Claude Code), `.cursor/mcp.json` (Cursor), or equivalent:

```json
{
  "mcpServers": {
    "verity": {
      "command": "verity-mcp",
      "env": {
        "WALRUS_PUBLISHER_URL": "https://publisher.walrus-testnet.walrus.space",
        "WALRUS_AGGREGATOR_URL": "https://aggregator.walrus-testnet.walrus.space"
      }
    }
  }
}
```

Or with `uvx` (no install needed):

```json
{
  "mcpServers": {
    "verity": {
      "command": "uvx",
      "args": ["verity-agent"]
    }
  }
}
```

### Available tools

| Tool | Description |
|------|-------------|
| `verity_init` | Create `verity.json` |
| `verity_add_feature` | Add a Feature (`feat:`) |
| `verity_add_claim` | Add a Claim (`clm:`) |
| `verity_add_test` | Add a Test (`tst:`) |
| `verity_add_evidence` | Add Evidence (`evd:`) |
| `verity_set_status` | Promote status after chain is wired |
| `verity_validate` | Validate the full chain |
| `verity_release` | Create a fail-closed release |
| `verity_push` | Push to Walrus, returns `blob_id` |
| `verity_pull` | Pull from Walrus by `blob_id` |
| `verity_log` | Show push history |
| `verity_status` | Entity counts + validation summary |
