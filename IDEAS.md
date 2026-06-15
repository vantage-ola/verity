# Ideas

Potential directions for verity beyond the current implementation.

---

## Shipped

| Feature | Version |
|---|---|
| `verity status` — terminal health summary | 0.1.x |
| `verity track` — quick-track one command | 0.1.x |
| `verity recall` — MemWal natural language query | 0.1.x |
| `verity site` — Walrus HTML proof page | 0.1.x |
| MCP server — proof-chain tools for AI editors | 0.1.x |
| `verity diff` — diff two Walrus blob snapshots | 0.2.0 |
| `verity export` — SARIF / JUnit / SPDX export | 0.2.0 |
| `verity sign` + `verity verify` — Ed25519 agent-to-agent trust | 0.3.0 |
| `verity_set_status_batch` MCP tool — promote full chain atomically | 0.3.1 |
| Deeper validation — passing tests need passed evidence; releases need verified claims | 0.3.2 |
| DRY release — `create_release()` delegates to `validate()` | 0.3.2 |
| Walrus retry — exponential backoff on 5xx and transport errors | 0.3.3 |
| Type-safe memwal — `store()` parses blobs via `Registry.model_validate()` | 0.3.4 |
| Structured diff — `diff_registries()` returns `DiffResult` with typed entries | 0.3.5 |
| Safe pull — `pull()` requires `force=True` to overwrite existing registry; CLI `--force` flag | 0.3.6 |
| MCP structured errors — all catch-all exceptions now raise (proper MCP error), domain errors still return strings | 0.3.7 |
| Status literal validation — `add_feature/claim/test/evidence` validate status strings early with clear ValueError | 0.3.8 |
| Default `.verity/registry.json` path — CLI/session/MCP default to new path; `registry_path()` falls back to legacy `verity.json` with DeprecationWarning | 0.3.9 |
| `verity watch` — daemon mode; polls registry, validates on change, auto-pushes on `--auto-push` | 0.3.10 |
| Evidence artifacts on Walrus — `verity push --upload-artifacts` uploads local artifact files, rewrites `artifact_path` to `walrus://<blob_id>` | 0.3.11 |
| Lazy signing import — `[sign]` extra no longer crashes basic commands for users without `cryptography` installed | 0.3.12 |
| `walrus-verity[all]` — meta-extra installs memwal + mcp + sign in one command | 0.3.13 |
| Explicit CWD `.env` loading — CLI picks up `.env` from current working directory reliably | 0.3.14 |

---

## Meaty Features

### Evidence artifacts on Walrus

Right now `artifact_path` in an evidence entry is just a local file path string. It should be a Walrus blob — the actual test report, log file, or eval result stored permanently. `verity push --upload-artifacts` uploads any evidence files and rewrites their paths to `walrus://<blob_id>`. The proof chain becomes fully self-contained: anyone with the root blob ID can verify the entire chain, including the raw artifacts, without local files.

```json
{
  "id": "evd:auth.ci",
  "test_id": "tst:auth.unit",
  "artifact_path": "walrus://AbCdEfGh...",
  "status": "passed"
}
```

### Policy as code

A `.verity-policy.yaml` in the repo that specifies minimum claim tiers, required test kinds, or evidence freshness windows per feature tag. `verity validate` enforces the policy — turns verity from a *recording* tool into an *enforcement* tool.

```yaml
# .verity-policy.yaml
rules:
  - tag: auth
    min_claim_tier: T2
    required_test_kinds: [unit, integration]
  - tag: billing
    evidence_max_age_days: 3
```

### `verity re-run` — re-execute from chain

Given a blob_id, pull the chain and re-run the actual test commands referenced in the evidence entries. Cryptographic reproduction — prove that the tests still pass today against the exact same claim set that was released. Useful for audits, compliance, and dependency trust.

```bash
verity re-run AbCdEfGh…
# pulling chain… 11 tests found
# running tst:auth.unit → passed ✓
# running tst:auth.integration → passed ✓
# all 11 verified — chain reproducible
```

### AI claim drafting (`verity draft`)

Given a feature description and the relevant code files, an LLM auto-generates suggested claims, test stubs, and evidence entries. Removes the blank-page problem of starting a chain from scratch.

```bash
verity draft feat:auth --from src/auth/
# suggested clm:auth.login "Login succeeds with valid credentials"
# suggested clm:auth.session "Session token expires after timeout"
# suggested tst:auth.unit → tests/test_auth.py
```

---

## Ecosystem

### CI/CD integration

A GitHub Action that runs on every merge: updates `verity.json` automatically (marks tests passing, adds evidence from the CI run), pushes to Walrus, and comments the blob_id on the PR. The proof chain stays in sync with the codebase with zero manual work.

### Agent framework plugins

The MCP server covers AI editors (Claude Code, Cursor, Windsurf). Framework plugins make sense for pipeline/orchestration code: LangChain tool wrapper, CrewAI plugin, OpenAI function-calling schema.

### Autonomous agent monitoring

Agents push proof chains as they work in real time. A supervisor agent polls or recalls via MemWal to get live visibility into what an autonomous agent has verified so far — without sharing a session or process. Each push is a heartbeat with proof.

### Multi-registry federation

A release in one `verity.json` could reference blob_ids from other registries as dependencies — "this release depends on proof chain X from the auth service and proof chain Y from the data pipeline." A DAG of proof chains across a whole system.

### Public proof registry

A MemWal-indexed directory of public verity proof chains. `verity search "walrus-verity"` returns the latest published blob_id for any indexed repo. Third parties can audit their dependencies' proof chains the same way `npm audit` surfaces vulnerability data — but with full claim/test/evidence lineage.

```bash
verity search "walrus-verity"
# walrus-verity  rel:0.3.4  blob: BHXE_i6Y…  24 claims verified
```

### On-chain release anchoring

Walrus already lives on Sui. A verity release could write its blob_id to a Sui smart contract — an immutable on-chain record that version X was certified at timestamp Y with these claims. Third parties can verify without trusting the publisher.

---

## Submission packaging (after features)

- **Demo narrative** — script the end-to-end multi-agent story: Agent A builds, signs, pushes with artifact uploads. Agent B verifies signature, inspects evidence artifacts — all from Walrus blob IDs.
- **Website / README rewrite** — lead with the problem ("how do you trust what an AI agent built?"), move multi-agent trust to the front door.
- **Submission write-up** — problem → solution → demo → tech stack → what's on Walrus.

*Hackathon deadline: June 20, 2026.*
