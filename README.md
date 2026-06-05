# verity

**How do you trust what an AI agent built?**

verity is a proof-chain registry for AI agents — record what was built, what was claimed, what tests ran, and what they proved. Every chain is published to [Walrus](https://docs.walrus.site) as an immutable blob. Any agent, on any machine, can pull it back and verify it.

[![CI](https://github.com/vantage-ola/verity/actions/workflows/ci.yml/badge.svg)](https://github.com/vantage-ola/verity/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/vantage-ola/verity/branch/main/graph/badge.svg)](https://codecov.io/gh/vantage-ola/verity)
[![PyPI version](https://badge.fury.io/py/walrus-verity.svg)](https://badge.fury.io/py/walrus-verity)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/walrus-verity?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/walrus-verity)

---

## The model

```
feature → claim → test → evidence → release
                                       │
                              verity push ──► Walrus blob ID (immutable)
                              verity pull ◄── restore anywhere, any agent
```

- **feature** — a capability being shipped
- **claim** — a testable statement about the feature
- **test** — the mechanism that exercises the claim
- **evidence** — the pass/fail signal the test produced
- **release** — a named snapshot; `push()` publishes it to Walrus

Built for the **Sui Overflow hackathon, Walrus track**.

---

## Install

```bash
pip install walrus-verity

# With MemWal semantic recall
pip install "walrus-verity[memwal]"

# With Ed25519 signing support
pip install "walrus-verity[sign]"
```

---

## Quick start

The fastest path — one command records the full claim/test/evidence chain:

```bash
verity init --repo-id repo:my-project
verity track feat:auth tests/test_auth.py --title "Login succeeds"
verity validate
verity release 1.0.0
verity push          # → blob: AbCdEfGh…
```

Or build the chain manually for full control:

```bash
# Phase 1 — add entities with neutral statuses
verity add feature  feat:auth "User authentication"
verity add claim    clm:auth.t1 "Login succeeds"  --feature feat:auth
verity add test     tst:auth.unit "Unit test"      --claim clm:auth.t1 --path tests/test_auth.py
verity add evidence evd:auth.ci "CI run"           --test tst:auth.unit --artifact artifacts/ci.json

# Phase 2 — promote statuses once the chain is fully linked
verity add evidence evd:auth.ci "CI run" --test tst:auth.unit --artifact artifacts/ci.json --status passed
verity validate      # → OK
verity release 1.0.0
verity push          # → blob: AbCdEfGh…

# Any agent, any machine, any future session:
verity pull AbCdEfGh…
```

> **Why neutral statuses first?** verity validates after every `add`. Setting `--status verified` on a claim before its test exists will fail. Build the full chain first, then promote statuses.

---

## Multi-agent trust

Agent A builds and signs. Agent B verifies before building on top.

```bash
# Agent A
verity push                                          # → blob_a
verity keygen --key ~/.verity/signing.key            # generate keypair once
verity sign --key ~/.verity/signing.key              # attest blob_a
verity push                                          # → blob_b (carries the attestation)

# Agent B — receives blob_b + pubkey
verity verify blob_b --pubkey-b64 <pubkey>
# blob: blob_b   repo: repo:my-project
# features 4  claims 5 (5 verified)
# chain valid ✓
# signature valid ✓   attests: blob_a…  signer: <pubkey>…
```

---

## AI coding assistant integration

**Skill installer** — teaches your AI assistant the verity model, CLI, and API:

```bash
verity install-skill                    # Claude Code (global CLAUDE.md)
verity install-skill --tool cursor      # Cursor → .cursorrules
verity install-skill --tool windsurf    # Windsurf → .windsurfrules
verity install-skill --tool codex       # OpenAI Codex → AGENTS.md
verity install-skill --tool aider       # Aider → CONVENTIONS.md
```

**MCP server** — expose all verity tools natively to any MCP-compatible editor:

```bash
pip install "walrus-verity[mcp]"
```

Add to your `claude_mcp_config.json` (or equivalent):

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

| MCP tool | Description |
|---|---|
| `verity_init` | Create `verity.json` |
| `verity_add_feature / claim / test / evidence` | Add chain entities |
| `verity_set_status` | Promote status after chain is wired |
| `verity_set_status_batch` | Promote multiple entities atomically in one call |
| `verity_validate` | Validate the full chain |
| `verity_release` | Fail-closed release |
| `verity_push / pull` | Walrus push and pull |
| `verity_log` | Push history |
| `verity_status` | Entity counts + validation summary |
| `verity_diff` | Diff two Walrus blob snapshots |
| `verity_export` | Export to SARIF, JUnit, or SPDX |
| `verity_sign` | Sign the latest push with an Ed25519 key |
| `verity_verify` | Fetch blob, validate chain, check signature |
| `verity_recall` | Natural language query against MemWal |

---

## Export and interop

```bash
verity export --format sarif    # SARIF 2.1.0 — security findings dashboards
verity export --format junit    # JUnit XML  — CI test result viewers
verity export --format spdx     # SPDX 2.3   — software bill of materials
```

---

## Recall

Push with MemWal to register semantic memories alongside the Walrus blob:

```bash
verity push --backend memwal

verity recall "what features have we built"
verity recall "what claims are verified"
verity recall "what was the latest release"
```

---

## Documentation

| Topic | |
|---|---|
| [CLI Reference](docs/cli.md) | All commands with flags and examples |
| [MCP Server](plugins/verity-agent/README.md) | `verity-mcp`: expose verity tools to any MCP-compatible editor |
| [Python API](docs/python-api.md) | `VeritySession`, low-level functions, custom backends |
| [Schema Reference](docs/schema.md) | `verity.json` fields, ID prefixes, status values, validation rules |
| [Walrus Setup](docs/walrus.md) | Testnet, mainnet, custom endpoints |
| [MemWal Setup](docs/memwal.md) | Env vars, delegate keys, namespace isolation |
| [Multi-Agent Patterns](docs/multi-agent.md) | Handoff pattern, audit trail, dry-run |

---

## Acknowledgements

The proof-chain model (`feature → claim → test → evidence → release`) is directly inspired by the [ssot-registry](https://github.com/groupsum/ssot-registry) project, licensed under [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0). verity adapts that model for AI agents and Walrus-backed persistence.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
