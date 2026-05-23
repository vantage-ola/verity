# verity

**A proof-chain registry for AI agents — backed by Walrus for persistent, portable, verifiable memory.**

[![CI](https://github.com/vantage-ola/verity/actions/workflows/ci.yml/badge.svg)](https://github.com/vantage-ola/verity/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/walrus-verity.svg)](https://badge.fury.io/py/walrus-verity)
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

---

## Quick start

```bash
verity init --repo-id repo:my-project

verity add feature feat:auth "User authentication"
verity add claim   clm:auth.t1 "Login succeeds" --feature feat:auth
verity add test    tst:auth.unit "Unit test" --claim clm:auth.t1 --kind unit --path tests/test_auth.py
verity add evidence evd:auth.run1 "CI run" --test tst:auth.unit --artifact artifacts/run1.json --status passed

verity validate          # → OK
verity release 1.0.0     # fail-closed — all verified claims need passed evidence
verity push              # → blob: AbCdEfGh…

# Any agent, any machine, any future session:
verity pull AbCdEfGh…
```

---

## Documentation

| Topic | |
|---|---|
| [CLI Reference](docs/cli.md) | All commands: `init`, `add`, `validate`, `release`, `push`, `pull`, `log` |
| [Python API](docs/python-api.md) | `VeritySession`, low-level functions, custom backends |
| [Schema Reference](docs/schema.md) | `verity.json` fields, ID prefixes, status values, validation rules |
| [Walrus Setup](docs/walrus.md) | Testnet, mainnet, custom endpoints |
| [MemWal Setup](docs/memwal.md) | Env vars, delegate keys, namespace isolation |
| [Multi-Agent Patterns](docs/multi-agent.md) | Handoff pattern, audit trail, dry-run |

---

## Acknowledgements

The proof-chain model — `feature → claim → test → evidence → release` — is directly inspired by the [ssot-registry](https://github.com/groupsum/ssot-registry) project, licensed under [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0). verity adapts that model for AI agents and Walrus-backed persistence.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run tests with `uv run pytest`.

## License

MIT — see [LICENSE](LICENSE).
