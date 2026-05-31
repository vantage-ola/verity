# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [semantic versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.1.7] — 2026-05-31

### Added
- **`verity status` CLI command** — compact terminal summary of registry health: entity counts with status breakdowns (verified/open claims, passing/failing tests, passed/failed evidence), latest release and blob ID, validation result; exits non-zero when the registry has errors
- 6 new tests for `verity status` in `tests/test_cli.py` (172 total, 97.83% coverage)

---

## [0.1.6] — 2026-05-26

### Added
- **MCP server** (`src/verity/mcp_server.py`) — exposes all proof-chain operations as MCP tools (`verity_init`, `verity_add_feature`, `verity_add_claim`, `verity_add_test`, `verity_add_evidence`, `verity_set_status`, `verity_validate`, `verity_release`, `verity_push`, `verity_pull`, `verity_log`, `verity_status`); compatible with any MCP-capable editor (Claude Code, Cursor, Windsurf, Codex)
- `verity_set_status` MCP tool — promotes entity statuses after the chain is wired; validates before saving so premature promotions are rejected
- `verity-mcp` entry point — available after `pip install "walrus-verity[mcp]"`
- `walrus-verity[mcp]` optional dependency group (`mcp>=1.0`)
- `plugins/verity-agent/` — standalone `verity-agent` package that re-exports from `verity.mcp_server`; installable independently via `pip install verity-agent` or `uvx verity-agent`
- 24 tests in `tests/test_mcp_server.py` covering all MCP tools, two-phase status promotion, mock backends, env-var Walrus wiring, and error paths
- MCP server section added to `docs/cli.md` and `web/src/components/Docs.tsx`
- MCP server section added to `README.md` with config examples for Claude Code and Cursor

---

## [0.1.5] — 2026-05-25

### Added
- `verity install-skill` command — installs the verity context skill into AI coding assistants; Claude Code gets a global `@path` reference in `~/.claude/CLAUDE.md`; Cursor, Windsurf, Codex, Aider get the skill injected into their project config files; idempotent (safe to run multiple times)
- `src/verity/skills/SKILL.md` — full verity reference skill bundled with the package; covers core concept, CLI, Python API, backends, multi-agent patterns, env vars, and the two-phase CLI status workflow
- `pyproject.toml`: `artifacts = ["src/verity/skills/*.md"]` so hatchling includes the skill file in the wheel
- `codecov.yml` — explicit Codecov config: project target `auto` with 1% threshold, patch target 85% with 5% threshold
- PyPI downloads badge in `README.md`
- `verity install-skill` section in `docs/cli.md` and `web/src/components/Docs.tsx`
- 12 tests in `tests/test_cli.py` covering install-skill for all five tools, idempotency, unknown tool error, missing skill file, and content validation
- `feat:install-skill` proof chain entry in `verity.json`

### Changed
- Two-phase CLI status workflow documented across `README.md`, `docs/cli.md`, `docs/python-api.md`, and `web/src/components/Docs.tsx` — build the full chain with neutral statuses first, then promote (`verified`, `passing`, `passed`) after everything is linked
- `SKILL.md` updated with "Correct order when building the chain via CLI" section explaining why neutral-first is required
- Section 02 ("In code") on the landing page now shows the evidence step (was missing)
- External links (GitHub, PyPI, License) open in a new tab

### Fixed
- Removed unused `const display` variable in `web/src/components/Chain.tsx` (TypeScript build error)
- Removed invalid `server.historyApiFallback` from `web/vite.config.ts` (webpack-only option; Vite's default `appType: 'spa'` handles SPA routing)
- Removed unused `button.tsx` and `utils.ts` shadcn scaffold files (were never committed or used; CSS bundle shrank from 31.8 kB to 21.3 kB)

---

## [0.1.4] — 2026-05-23

### Added
- `verity site` command — generates a human-readable HTML proof page from `verity.json`; `--output` saves locally, `--push` uploads to Walrus and prints a public viewer URL
- `generate_html(registry)` exported from `verity` public API
- `scripts/store_project_context.py` — one-shot script to seed MemWal with verity project knowledge so any agent can `recall("verity")` and arrive with full context
- `docs/scripts.md` — documents the store_project_context script
- `docs/cli.md` updated with full `verity site` reference
- Coverage badge added to README

### Changed
- `examples/demo_multi_agent.py` — replaced `backend_b.fetch = backend_a.fetch` hack with a clean `_SharedStore` class; added `--live` flag for Walrus testnet mode (dry-run is now the default)
- `docs/multi-agent.md` dry-run example updated to use the `_SharedStore` pattern

---

## [0.1.3] — 2026-05-23

### Added
- `.env` file support via `python-dotenv` — CLI now auto-loads `.env` on startup so `MEMWAL_KEY`, `MEMWAL_ACCOUNT_ID`, `WALRUS_PUBLISHER_URL`, etc. work without manual `export`

### Fixed
- `test_raises_without_key` and `test_raises_without_account_id` now explicitly clear env vars so a local `.env` file doesn't pollute the test session

---

## [0.1.2] — 2026-05-23

### Fixed
- `verity pull --dir <path>` now creates the target directory (and any parents) if it does not exist — previously raised `FileNotFoundError`
- Same fix applied to `VeritySession.pull()` for programmatic use

### Added
- `--status` option on `verity add claim` (default: `open`)
- `--status` option on `verity add test` (default: `pending`)

---

## [0.1.1] — 2026-05-23

### Changed
- Renamed PyPI distribution from `verity` → `verity-sdk` → `walrus-verity`
- Moved detailed documentation out of `README.md` into `docs/` folder
- `README.md` is now a concise overview with links to docs pages
- Added acknowledgement of [ssot-registry](https://github.com/vantage-ola/ssot-registry) (Apache 2.0) as the conceptual origin of the proof-chain model

### Added
- `docs/cli.md` — full CLI reference
- `docs/python-api.md` — Python API and custom backend guide
- `docs/schema.md` — `verity.json` schema, ID prefixes, status values, validation and release rules
- `docs/walrus.md` — Walrus testnet, mainnet, and epoch setup
- `docs/memwal.md` — MemWal env vars, delegate keys, how store/fetch works
- `docs/multi-agent.md` — handoff pattern, audit trail, dry-run examples
- `plugins/verity-agent/SKILL.md` — LLM-agnostic agent skill for using verity in any project
- `plugins/verity-agent/AGENT_PROMPT.md` — compact system-prompt-friendly version
- `PUBLISHING.md` — semantic versioning guide, PyPI trusted publishing setup, full release process

---

## [0.1.0] — 2025-05-23

Initial release. Full Phase 1–3 implementation.

### Added

**Core models** (`src/verity/models.py`)
- `Feature`, `Claim`, `Test`, `Evidence`, `Release` pydantic v2 models with `extra="forbid"`
- ID prefix enforcement at the model layer (`feat:`, `clm:`, `tst:`, `evd:`, `rel:`)
- `Registry` wrapper model with `schema_version`, `repo_id`, and all five entity lists
- `PushRecord` model for tracking push history (blob ID, timestamp, backend label)
- `pushes` list on `Registry` for a durable push log

**Registry I/O** (`src/verity/registry.py`)
- `load_registry(path)` — parse `verity.json` via pydantic
- `save_registry(registry, path)` — write canonical JSON
- `canonical_json(registry) -> str` — deterministic serialization (sorted keys, compact separators, no trailing newline, `allow_nan=False`)
- `registry_path(directory)` — resolve `verity.json` path from a directory

**Validation** (`src/verity/validate.py`)
- `validate(registry) -> list[str]` — returns a list of human-readable error strings
- Guards: duplicate IDs, broken foreign-key links (claim→feature, test→claim, evidence→test, release→claim), status consistency (verified claims need linked tests; passing tests need linked evidence)

**Release** (`src/verity/release.py`)
- `create_release(registry, version) -> Release` — fail-closed
- Raises `VerityReleaseError` when no verified claims exist, or when any verified claim has no linked passing test with passed evidence
- No partial releases — either all verified claims pass the gate or none do

**Storage backends** (`src/verity/backends.py`, `src/verity/walrus.py`, `src/verity/memwal.py`)
- `StorageBackend` runtime-checkable protocol with `store(bytes) -> str` and `fetch(str) -> bytes`
- `WalrusBackend` — HTTP backend over the Walrus REST API (`PUT /v1/blobs`, `GET /v1/blobs/{id}`); handles both `newlyCreated` and `alreadyCertified` response shapes; configurable publisher and aggregator URLs; optional `delegate_key` header
- `MemWalBackend` — wraps the `memwal` SDK (`MemWalSync`) for store; fetches directly from the Walrus aggregator because MemWal blob IDs are Walrus blob IDs; reads credentials from `MEMWAL_KEY`, `MEMWAL_ACCOUNT_ID`, `MEMWAL_SERVER_URL`, `MEMWAL_NAMESPACE`, `MEMWAL_ENV`
- Module-level `push()` and `pull()` helpers in `walrus.py` for backward compatibility

**Python API** (`src/verity/session.py`)
- `VeritySession` — high-level API for programmatic agent use
- `init(repo_id)`, `add_feature`, `add_claim`, `add_test`, `add_evidence` — create entities and write through to disk
- `validate() -> list[str]`, `release(version) -> Release`
- `push(*, epochs=5) -> str` — serialise registry, push to backend, record `PushRecord`
- `pull(blob_id) -> None` — fetch from backend, deserialise, overwrite local registry
- `log() -> list[PushRecord]` — return push history
- `registry() -> Registry` — return current in-memory registry

**CLI** (`src/verity/cli/main.py`)
- `verity init` — create `verity.json` in the current directory
- `verity add feature <id> <title> [--status]`
- `verity add claim <id> <title> --feature <feat-id> [--tier] [--status]`
- `verity add test <id> <title> --claim <clm-id> [--kind] [--path] [--status]`
- `verity add evidence <id> <title> --test <tst-id> [--kind] [--artifact] [--status]`
- `verity validate` — run guards; print errors or `All checks passed.`; exits non-zero on errors
- `verity release <version>` — create a fail-closed release; print release ID
- `verity push [--backend walrus|memwal] [--epochs N] [--dir PATH]`
- `verity pull <blob-id> [--backend walrus|memwal] [--dir PATH]`
- `verity log [--dir PATH]` — print push history (timestamp, backend, blob ID)

**Public exports** (`src/verity/__init__.py`)
- `Registry`, `Feature`, `Claim`, `Test`, `Evidence`, `Release`, `PushRecord`
- `StorageBackend`, `WalrusBackend`, `MemWalBackend`
- `VeritySession`
- `load_registry`, `save_registry`, `validate`, `push`, `pull`

**Packaging and CI**
- `pyproject.toml` with hatchling build backend, full PyPI classifiers and keywords
- `uv.lock` for reproducible installs
- GitHub Actions CI matrix: Python 3.11, 3.12, 3.13 with `uv`; coverage to Codecov
- GitHub Actions publish workflow: OIDC trusted publishing to PyPI + GitHub Release on `v*` tags
- 85% branch coverage minimum enforced in CI

**Examples and docs**
- `examples/demo_multi_agent.py` — two-agent demo (researcher + auditor) with `--dry-run` flag
- `README.md` — installation, quickstart, full CLI + Python API reference, Walrus/MemWal setup, `verity.json` schema, testing guide, PyPI publishing guide
- `CONTRIBUTING.md` — dev setup, test commands, backend/model extension guide, release process
- `LICENSE` — MIT

---

[Unreleased]: https://github.com/vantage-ola/verity/compare/v0.1.7...HEAD
[0.1.7]: https://github.com/vantage-ola/verity/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/vantage-ola/verity/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/vantage-ola/verity/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/vantage-ola/verity/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/vantage-ola/verity/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/vantage-ola/verity/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/vantage-ola/verity/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/vantage-ola/verity/releases/tag/v0.1.0
