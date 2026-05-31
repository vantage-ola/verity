# verity

**A proof-chain registry for AI agents — backed by Walrus for persistent, portable, verifiable memory.**

[![CI](https://github.com/vantage-ola/verity/actions/workflows/ci.yml/badge.svg)](https://github.com/vantage-ola/verity/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/vantage-ola/verity/branch/main/graph/badge.svg)](https://codecov.io/gh/vantage-ola/verity)
[![PyPI version](https://badge.fury.io/py/walrus-verity.svg)](https://badge.fury.io/py/walrus-verity)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/walrus-verity?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/walrus-verity)

---

## What it does

verity gives AI agents structured, portable memory:

```
feature → claim → test → evidence → release
                                       │
                              verity push ──► Walrus blob ID (immutable)
                              verity pull ◄── restore anywhere, any agent
```

1. **Proof-chain registry** — track what an agent claimed, what it tested, and what it proved, all in a single `verity.json` file.
2. **Agent memory layer** — push the registry to [Walrus](https://docs.walrus.site) (or [MemWal](https://memwal.ai)) and pull it back in any future session, on any machine, by any agent.

Built for the **Sui Overflow hackathon, Walrus track**.

---

## Install

```bash
pip install walrus-verity

# With MemWal support
pip install "walrus-verity[memwal]"
```

### AI coding assistant integration

**Context skill** — teach your AI tool the verity proof chain model, CLI, and API:

```bash
verity install-skill                    # Claude Code (global)
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

Available MCP tools: `verity_init`, `verity_add_feature`, `verity_add_claim`, `verity_add_test`, `verity_add_evidence`, `verity_set_status`, `verity_validate`, `verity_release`, `verity_push`, `verity_pull`, `verity_log`, `verity_status`.

---

## Quick start

The CLI validates on every write, so build the chain with neutral statuses first, then promote them once everything is linked.

```bash
verity init --repo-id repo:my-project

# Phase 1 — build the chain (neutral statuses)
verity add feature feat:auth "User authentication"
verity add claim   clm:auth.t1 "Login succeeds"  --feature feat:auth
verity add test    tst:auth.unit "Unit test"      --claim clm:auth.t1 --kind unit --path tests/test_auth.py
verity add evidence evd:auth.ci "CI run"          --test tst:auth.unit --artifact artifacts/ci.json --status passed

# Phase 2 — promote statuses (edit verity.json: set claim → verified, test → passing)
verity validate      # → OK
verity release 1.0.0
verity push          # → blob: AbCdEfGh…

# Any agent, any machine, any future session:
verity pull AbCdEfGh…
```

> **Why two phases?** verity validates after every `add` command. Setting `--status verified` on a claim before its test exists will fail. Build the full chain first, then mark statuses.
>
> Using the **Python API** instead? Statuses can be set at add time — validation is deferred until you call `validate()` or `push()`. See [Python API](docs/python-api.md).

```
$ verity validate
OK

$ verity release 1.0.0
Released rel:1.0.0 at 2026-05-23T19:08:25Z
  claims: clm:auth.t1

$ verity push
blob: AbCdEfGhIjKlMnOpQrStUvWxYz0123456789

$ verity log
  1.  [walrus]  2026-05-23T19:08:25Z  AbCdEfGhIjKlMnOpQrStUvWxYz0123456789

$ verity status
repo:my-project  schema 0.1.0
features   1   claims     1  (1 verified, 0 open)
tests      1  (1 passing)
evidence   1  (1 passed)
releases   1   latest: rel:1.0.0  blob: AbCdEfGh…
valid      ✓
```

---

## Documentation

| Topic | |
|---|---|
| [CLI Reference](docs/cli.md) | All commands: `init`, `add`, `validate`, `release`, `push`, `pull`, `log`, `site`, `context`, `install-skill` |
| [MCP Server](plugins/verity-agent/README.md) | `verity-mcp` — expose verity tools to any MCP-compatible editor |
| [Python API](docs/python-api.md) | `VeritySession`, low-level functions, custom backends |
| [Schema Reference](docs/schema.md) | `verity.json` fields, ID prefixes, status values, validation rules |
| [Walrus Setup](docs/walrus.md) | Testnet, mainnet, custom endpoints |
| [MemWal Setup](docs/memwal.md) | Env vars, delegate keys, namespace isolation |
| [Multi-Agent Patterns](docs/multi-agent.md) | Handoff pattern, audit trail, dry-run |
| [Scripts](docs/scripts.md) | `store_project_context.py` — seed MemWal with verity project knowledge |

---

## Acknowledgements

The proof-chain model — `feature → claim → test → evidence → release` — is directly inspired by the [ssot-registry](https://github.com/groupsum/ssot-registry) project, licensed under [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0). verity adapts that model for AI agents and Walrus-backed persistence.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run tests with `uv run pytest`.

## License

MIT — see [LICENSE](LICENSE).
