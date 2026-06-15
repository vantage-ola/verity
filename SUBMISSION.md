# Sui Overflow 2026: Submission Package
**Track**: Walrus | **Deadline**: June 21, 2026 | **Repo**: https://github.com/vantage-ola/verity

---

## 1. What We Built

**verity** is a proof-chain registry for AI agents, backed by Walrus.

When an AI agent builds something, it records what was built (features), what was claimed about it (claims), what tests ran (tests), and what they proved (evidence). Every chain is published to Walrus as an immutable blob. Any other agent, anywhere, any time, can pull it back and verify it.

```
feature → claim → test → evidence → release
                                       │
                              verity push ──► Walrus blob ID (immutable)
```

---

## 2. Why It Matters

The AI coding era has a trust problem nobody is talking about:

- An AI agent writes code and says "tests pass", but you can't verify that claim independently
- Multi-agent pipelines hand off work between models, but there's no receipt, no audit trail
- Open source packages are increasingly AI-generated, with no proof of what was actually tested

**verity solves this.** Every claim is linked to the test that exercised it and the evidence that test produced. The whole chain is published to Walrus: permanent, content-addressed, verifiable by anyone with the blob ID.

Walrus is the only storage layer that makes this possible at scale. A `verity.json` on your laptop is local state. A Walrus blob ID is a portable, permanent certificate.

---

## 3. How It Uses the Sui / Walrus Stack

| Layer | How verity uses it |
|---|---|
| **Walrus blob store** | Every proof chain is serialized to canonical JSON and stored as a Walrus blob. The blob ID is the immutable fingerprint of that chain state. |
| **Walrus artifact upload** | `verity push --upload-artifacts` uploads individual test report files (JUnit XML, SARIF, logs) as separate Walrus blobs and rewrites `artifact_path` to `walrus://<blob_id>`. The entire chain, registry and raw test artifacts, lives on Walrus. |
| **MemWal (Walrus-backed memory)** | `verity push --backend memwal` registers semantic pointers on top of Walrus so agents can query in natural language: *"what features have we verified?"* Walrus provides the storage; MemWal provides the index. |
| **Ed25519 agent-to-agent signing** | Agent A signs its blob with `verity sign`. Agent B calls `verity verify blob_id --pubkey-b64 <key>` before building on top of it. Trust between agents is cryptographically grounded in Walrus immutability. |

---

## 4. Feature Highlight Reel

| Feature | Version |
|---|---|
| Proof chain CLI (`init`, `add`, `validate`, `release`, `push`, `pull`) | 0.1.x |
| `verity track`: one command records the full chain | 0.1.x |
| `verity recall`: MemWal natural language query | 0.1.x |
| MCP server: AI editors (Claude Code, Cursor, Windsurf) get native verity tools | 0.1.x |
| `verity diff`: diff two Walrus blob snapshots | 0.2.0 |
| `verity export`: SARIF / JUnit / SPDX export | 0.2.0 |
| `verity sign` + `verity verify`: Ed25519 agent-to-agent trust | 0.3.0 |
| `verity_set_status_batch`: atomic multi-entity status promotion via MCP | 0.3.1 |
| `verity watch`: daemon mode, auto-push on valid change | 0.3.10 |
| `verity push --upload-artifacts`: full chain on Walrus, artifacts and all | 0.3.11 |
| CWD `.env` loading: CLI picks up `.env` from current directory reliably | 0.3.14 |

---

## 5. Demo Video

**Animated teaser** (35s, 4K): `demo/verity-demo.mp4`, recorded and ready.

**Full walkthrough** (~3.5 min): screen recording showing the complete multi-agent flow below.

**Format**: two terminals side by side, text cards, no commentary needed

### Pre-recording setup (not on camera)

```bash
mkdir -p demo/agent-a/tests demo/agent-a/reports demo/agent-b/tests
echo "def test_charge(): assert True" > demo/agent-a/tests/test_payments.py
echo '{"tests": 5, "passed": 5}' > demo/agent-a/reports/ci.json
echo "def test_audit(): assert True" > demo/agent-b/tests/test_audit.py
verity keygen --key ~/.verity/signing.key
```

### Recording sequence

---

**TEXT CARD**: "AI agents build code. But how do you know what they actually proved?"

---

**LEFT TERMINAL: Agent A**
```bash
cd demo/agent-a
verity init --repo-id repo:payments-api
verity add feature feat:payments "Payment processing"
verity track feat:payments tests/test_payments.py
verity status
```

**TEXT CARD**: "Feature → Claim → Test → Evidence."

```bash
verity release 1.0.0
verity push --upload-artifacts
```
*(note the blob ID)*

**TEXT CARD**: "Test artifacts and proof chain, all on Walrus. Permanently."

```bash
verity sign --key ~/.verity/signing.key
verity push
```
*(note this blob ID: BLOB_A)*

---

**TEXT CARD**: "Agent A signed it. Agent B needs to verify before building on top."

---

**SPLIT SCREEN: both terminals**

**RIGHT TERMINAL: Agent B**
```bash
cd demo/agent-b
verity pull BLOB_A --force
verity verify BLOB_A
```
*(shows: chain valid ✓  signature valid ✓)*

**TEXT CARD**: "No shared state. No blind trust."

```bash
verity add feature feat:audit "Audit logging"
verity track feat:audit tests/test_audit.py
verity release 1.1.0
verity push
```

---

**TEXT CARD**: "Agent B extended the chain. New blob. New proof."

---

**BACK TO LEFT TERMINAL: Agent A**
```bash
verity pull BLOB_B --force
verity status
```
*(shows the full updated chain from both agents)*

**TEXT CARD**: "One blob ID. Full picture. Any agent, anywhere."

---

**FINAL SCREEN**: both terminals side by side, both showing clean status

**TEXT CARD**: `uv tool install "walrus-verity[all]"` | "verity. Proof chains for AI agents, on Walrus."

---

## 6. Pitch Deck Outline

**Slide 1: Title**
> verity: Proof Chains for AI Agents, on Walrus

**Slide 2: The Problem**
> AI agents write code. Nobody knows what they actually proved.
> (show: AI PR merged, no test evidence, no audit trail)

**Slide 3: The Model**
> feature → claim → test → evidence → release → Walrus blob ID
> (clean diagram, one line)

**Slide 4: Demo Screenshot**
> Terminal: `verity push` → `blob: AbCdEfGh…`
> "That blob is permanent. Anyone can verify it."

**Slide 5: Multi-Agent Trust**
> Agent A signs and pushes. Agent B verifies before extending.
> (two-agent diagram with blob ID as the handoff token)

**Slide 6: Walrus Stack**
> Walrus blobs, artifact upload, MemWal semantic memory, Ed25519 signing
> "Walrus is the only layer that makes this permanent and verifiable at scale."

**Slide 7: Shipped**
> `uv tool install "walrus-verity[all]"`, v0.3.14 on PyPI
> MCP server, CLI, Python API, tests passing

**Slide 8: What's Next**
> Policy as code, CI/CD GitHub Action, on-chain Sui anchoring

---

## 7. Submission Checklist

- [ ] Demo video uploaded (YouTube / Loom)
- [ ] GitHub repo public: https://github.com/vantage-ola/verity
- [ ] PyPI: https://pypi.org/project/walrus-verity/
- [ ] Submission form filled out (title, description, track: Walrus)
- [ ] Demo video link added to submission
- [ ] Team members listed

---

## 8. Submission Description (for the form)

**One-liner**: verity is a proof-chain registry for AI agents. It records what was built, what was claimed, and what tests proved it, then publishes the whole chain to Walrus as an immutable blob.

**Full description**:

verity solves the trust problem in AI-generated code. When an AI agent builds a feature, verity records the full evidence chain: feature, claim, test, evidence. Then it publishes that chain to Walrus. The blob ID is a permanent, content-addressed receipt. Any agent, on any machine, can pull it back and verify it.

The multi-agent use case is the core story. Agent A builds, signs with Ed25519, and pushes to Walrus. Agent B receives the blob ID, verifies the signature and chain, then extends it and pushes a new blob. Trust between agents is cryptographically grounded in Walrus immutability. No shared state, no trust in the sender.

`verity push --upload-artifacts` goes further: individual test report files (JUnit XML, SARIF, logs) are uploaded as separate Walrus blobs, with `artifact_path` rewritten to `walrus://<blob_id>`. The entire proof chain, registry and raw artifacts, lives on Walrus.

verity also ships an MCP server so AI coding editors (Claude Code, Cursor, Windsurf) get native proof-chain tools. The AI that writes the code also maintains the proof chain.

**Tech stack**: Walrus (blob storage + artifact upload), MemWal (Walrus-backed semantic memory for natural language recall), Ed25519 cryptographic signing

---

## 9. Message to the Nigerian Sui Community

---

Hey Naija Sui fam 👋

My name is Ola. I just shipped something I'm really proud of: **verity**, a proof-chain registry for AI agents built on top of Walrus.

The idea is simple: when an AI agent builds something (code, a report, a feature), how do you actually know it did what it said? Right now you just trust it. verity changes that. It records what was built, what was claimed, what tests ran, and what they proved, then publishes the whole thing to Walrus as an immutable blob. Any agent, any team, any auditor can pull it back and verify it independently.

I built this for the **Sui Overflow 2026 hackathon** (Walrus track) but I want it to outlive the hackathon and actually be useful.

**I'd love your help:**

1. **Try it out**: `uv tool install "walrus-verity[all]"` and run `verity --help`. Takes 2 minutes to get a chain going.
2. **Break it**: if something is confusing, missing, or wrong, tell me. That feedback is gold.
3. **Show it to your agents**: if you're building AI pipelines, LangChain workflows, CrewAI setups, verity can add a verifiable audit trail to any of that.
4. **Star the repo**: https://github.com/vantage-ola/verity. It helps with visibility.

This is built by a Nigerian dev, published on PyPI, running on Walrus testnet right now. I want to see more of us building at the protocol level on Sui. Not just using the tools, but shipping them.

Hit me up with feedback, questions, or just to vibe. Let's build 🇳🇬

Ola

---
