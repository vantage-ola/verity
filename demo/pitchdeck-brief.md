# Pitch Deck Brief — verity

> Hand this file to an AI design tool (Claude, Gamma, etc.) with the prompt:
> "Create a clean, minimal pitch deck from this brief. Dark background, accent color #89b4fa (Catppuccin blue). 8–10 slides. No filler slides."

---

## Project

**Name**: verity  
**Tagline**: Proof chains for AI agents, on Walrus.  
**One-liner**: verity lets AI agents record what they built, what they claimed, and what tests proved it — then publishes the whole chain to Walrus as an immutable blob ID.  
**PyPI package**: `walrus-verity`  
**Install**: `uv tool install "walrus-verity[all]"`  
**Version**: 0.3.14  
**Hackathon**: Sui Overflow 2026 — Walrus track  

---

## The Problem (Slide 1–2)

AI agents write code, run tests, and ship features. But there's no receipt.

- An agent says "tests pass" — you have to trust it
- A multi-agent pipeline hands off work between models — there's no audit trail
- You can't tell what an agent actually verified vs what it just claimed
- If something breaks in production, there's no chain of evidence to trace back

**The core gap**: AI output is cheap to produce and impossible to verify after the fact.

This matters more every month as agents get more autonomy. The smarter the agent, the better it gets at finding shortcuts — and the harder it is to catch.

---

## The Solution (Slide 3)

**verity** is a proof-chain registry. Every agent action produces a chain:

```
Feature → Claim → Test → Evidence → Release
                                        ↓
                               Walrus blob ID  (immutable, permanent)
```

- **Feature** — what capability was built
- **Claim** — a testable statement about that feature
- **Test** — the mechanism that exercises the claim
- **Evidence** — the pass/fail result, with artifact (log file, CI report)
- **Release** — a named snapshot of the full chain
- **Walrus blob ID** — the permanent, content-addressed receipt

Anyone with the blob ID can pull the full chain and verify it independently. No trust required.

---

## How It Works (Slide 4)

**Three commands. Full chain.**

```bash
verity init --repo-id repo:payments-api
verity track feat:payments tests/test_payments.py
verity push --upload-artifacts
# → blob: AbCdEfGh…  (permanent Walrus receipt)
```

`verity track` builds the full chain (feature + claim + test + evidence) from a single command. `verity push` publishes it to Walrus. The blob ID is the handoff token.

---

## The Multi-Agent Story (Slide 5) ← CORE SLIDE

This is the use case that makes verity unique.

**Agent A** builds a payments feature, runs tests, signs the chain with Ed25519, and pushes to Walrus:
```bash
verity push --upload-artifacts   # artifacts live on Walrus
verity sign --key agent-a.key
verity push                      # → BLOB_A
```

**Agent B** receives `BLOB_A`, verifies the signature and full chain, then extends it:
```bash
verity pull BLOB_A
verity verify BLOB_A             # chain valid ✓  signature valid ✓
# ... Agent B adds audit logging feature ...
verity push                      # → BLOB_B  (new blob, new proof)
```

**Agent A** can pull `BLOB_B` and see the full updated chain — both agents' work, one immutable receipt.

**The key insight**: the blob ID is the trust token. No shared state. No blind trust. No central authority. Cryptographically grounded in Walrus immutability.

---

## Key Features (Slide 6)

| Feature | What it does |
|---|---|
| `verity track` | One command builds the full chain |
| `verity push --upload-artifacts` | Uploads test reports and logs to Walrus, rewrites paths to `walrus://` |
| `verity sign` + `verity verify` | Ed25519 agent-to-agent trust — Agent B verifies Agent A's signature before building on top |
| `verity diff` | Diff two Walrus blob snapshots — see what changed between releases |
| `verity export` | Export chains as SARIF, JUnit, or SPDX for DevSecOps tooling |
| `verity watch` | Daemon mode — polls registry, validates on change, auto-pushes |
| MCP server | AI editors (Claude Code, Cursor, Windsurf) can build proof chains natively |
| MemWal backend | Natural language recall — "what features have been verified?" queries Walrus-backed memory |
| `walrus-verity[all]` | One install, everything included |

---

## Walrus Integration (Slide 7)

verity is built on Walrus from the ground up — not bolted on.

- **Every push** stores the registry JSON as a Walrus blob (content-addressed, permanent)
- **Artifact upload** (`--upload-artifacts`) stores test reports, CI logs, and eval results as individual blobs — rewriting `artifact_path` to `walrus://blob_id`
- **Pull** fetches any historical chain state from its blob ID — no local files needed
- **Diff** compares two blob snapshots directly on Walrus
- **MemWal** uses Walrus as the storage layer for semantic memory — natural language queries over proof chains stored on-chain
- **The blob ID is the proof** — immutable, permanent, shareable across agents, teams, and time

Everything that matters about what an agent built lives on Walrus. The blob ID is the receipt.

---

## Who It's For (Slide 8)

**Today** (v0.3.x):
- Developers building with AI coding assistants who want a verifiable record of what was shipped
- AI agent pipeline builders (LangChain, CrewAI, custom agents) who need audit trails between steps
- Security and compliance teams who need evidence chains for AI-generated code

**Near future**:
- CI/CD pipelines — auto-update proof chains on every merge, push to Walrus, comment blob ID on PR
- Multi-model systems where trust must be established cryptographically between agents
- Auditors and third parties who want to verify what an AI agent actually proved, independently

---

## Traction (Slide 9)

- **v0.3.14** shipped — 14 releases in rapid iteration
- Full feature set: chain building, Walrus push/pull, artifact upload, Ed25519 signing, diff, export, MCP server, MemWal recall, watch daemon
- MCP server works with Claude Code, Cursor, Windsurf — AI editors can build proof chains natively
- `walrus-verity[all]` — one install command covers everything
- MIT licensed, published on PyPI

---

## Vision (Slide 10)

Right now verity records what AI agents prove. The next steps:

- **Policy as code** — `.verity-policy.yaml` turns verity from a recording tool into an enforcement tool
- **Public proof registry** — `verity search "my-package"` returns the latest verified blob ID for any published package, like `npm audit` but for AI-generated proof chains
- **On-chain anchoring** — write release blob IDs to Sui smart contracts for immutable, trustless verification
- **CI/CD native** — GitHub Action that keeps proof chains in sync with every merge, zero manual work

The long-term bet: as AI agents get more autonomous, the demand for cryptographic proof of what they actually did goes from "nice to have" to "required by law."

---

## Design Notes for the Deck

**Tone**: technical confidence, not hype. The audience is developers and builders.  
**Style**: dark background (#1e1e2e Catppuccin base), accent #89b4fa (blue), text #cdd6f4  
**Font**: something monospace-adjacent for code blocks, clean sans-serif for body  
**Visuals**:
- Slide 1: big bold problem statement, no images
- Slide 4: the chain diagram (`Feature → Claim → Test → Evidence → blob ID`) as a visual flow
- Slide 5: two terminal panels side by side (Agent A left, Agent B right) with an arrow showing the blob ID handoff
- Slide 7: Walrus logo + the blob ID flow diagram
- Keep code blocks styled — dark terminal aesthetic fits the brand
- No stock photos. No generic "AI brain" imagery.

**Key phrases to use**:
- "One blob ID. Full picture. Any agent, anywhere."
- "No shared state. No blind trust."
- "The blob ID is the receipt."
- "Proof chains for AI agents, on Walrus."
