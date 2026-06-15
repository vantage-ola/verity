# verity — Design Prototypes

Prototypes for the verity marketing website and documentation site.
Use this document as the brief for Claude Design.

---

## Brand

**Name:** verity

**Tagline:** Proof-chain registry for AI agents.

**One-liner:** Track what your agent claimed, what it tested, and what it proved — backed by Walrus for permanent, portable, verifiable memory.

**Icon:** `verity_icon.png` — four connected chain nodes (light gray) with a teal eye at the center, on a dark charcoal background. Use this as the logo mark throughout.

### Colour palette

| Role | Hex |
|---|---|
| Background (dark) | `#1e2128` |
| Surface | `#262b35` |
| Border / subtle | `#2e3440` |
| Text primary | `#e2e8f0` |
| Text muted | `#64748b` |
| Accent (teal) | `#38bdf8` |
| Accent hover | `#0ea5e9` |
| Success green | `#22c55e` |
| Warning amber | `#f59e0b` |
| Error red | `#ef4444` |

### Typography

- Headings: `Inter` or `Geist` — medium/semibold weight
- Body: `Inter` — regular
- Code: `JetBrains Mono` or `Fira Code`

### Tone

Technical but approachable. Not academic, not startup-marketing. Think: good dev tool docs (Stripe, Linear, Fly.io). Dark mode first.

---

## Page 1 — Marketing / Landing Page

**URL:** `verity.site` (or similar)

**Goal:** Communicate what verity is in 10 seconds, get developers to install it or read the docs.

### Sections

#### Hero

- Logo mark + wordmark: `verity`
- Tagline: *Proof-chain registry for AI agents*
- Subtext: *Track what was claimed, what was tested, and what was proved. Push to Walrus. Pull anywhere, any agent, any session.*
- Two CTAs side by side:
  - Primary: `pip install walrus-verity` (copyable code chip)
  - Secondary: `Read the docs →`
- Background: dark charcoal with a subtle grid or chain-node pattern echoing the icon

#### How it works

Five steps shown as a horizontal chain (mirrors the icon):

```
feature → claim → test → evidence → release
```

Each node has a short label and 1-sentence description. The connecting lines are teal. This is the centrepiece visual.

#### Code example

Split panel — left: annotated CLI commands, right: the resulting `verity.json` snippet. Syntax-highlighted dark theme.

```bash
verity add feature feat:auth "User authentication"
verity add claim clm:auth.t1 "Login succeeds" --feature feat:auth
verity add test tst:auth.unit "Unit test" --claim clm:auth.t1 --path tests/test_auth.py
verity release 1.0.0
verity push --backend memwal
# blob: AbCdEfGh…
```

#### Use cases

Three cards in a row:

1. **Multi-agent handoff** — Agent A proves its work, Agent B verifies before building on it
2. **Autonomous monitoring** — Each push is a heartbeat with proof; supervisors recall live state via MemWal
3. **CI/CD audit trail** — Every merge updates the proof chain and publishes a new blob_id

#### Walrus + MemWal integration

Short section explaining the storage layer: Walrus for immutable blobs, MemWal for semantic recall. Show the two logos side by side with a one-line description each. Positions verity within the Sui/Walrus ecosystem.

#### Install strip

```bash
pip install walrus-verity
pip install "walrus-verity[memwal]"
```

Minimal dark strip with copy buttons.

#### Footer

Links: GitHub · PyPI · Docs · License (MIT)

---

## Page 2 — Documentation Site

**Goal:** Fast, searchable reference. Developers land here from the README or marketing site and find what they need without friction.

### Layout

Standard docs layout:
- Fixed left sidebar with navigation tree
- Main content area (readable width, ~720px)
- Right mini-TOC (page headings, sticky)
- Top bar: logo + search + GitHub link + version badge (`v0.1.5`)

### Sidebar navigation

```
Getting Started
  Installation
  Quick start
  verity.json

CLI Reference
  init
  add
  validate
  release
  push / pull
  log
  site
  context

Python API
  VeritySession
  Low-level functions
  Models
  Custom backends
  Error types

Schema
  verity.json structure
  Entity fields
  ID prefixes
  Validation rules

Backends
  Walrus
  MemWal

Guides
  Multi-agent patterns
  CI/CD integration

Scripts
  store_project_context.py
```

### Getting Started page

1. Install block (pip, with memwal variant)
2. Five-command quick start — same sequence as the marketing page but with inline explanation of each command
3. "What you just did" — a short explanation of the proof chain model for someone seeing it for the first time
4. Link to full CLI reference

### CLI Reference pages

One page per command group. Each page follows the same pattern:

- Command signature
- Flag table (option, default, description)
- One or two usage examples with expected output
- Notes / edge cases

### API Reference pages

`VeritySession` page:
- Constructor
- Methods table (name, returns, description)
- Full working code example (init → add → validate → release → push)
- Context methods (`set_context`, `get_context`, `remove_context`) with example

### Design details

- Code blocks: dark background, line numbers optional, copy button top-right
- Callout boxes for notes, warnings, tips — use teal border for notes, amber for warnings
- Command output shown in a terminal-style block (slightly lighter background than code, monospace, muted text)
- Status badges inline (green `verified`, amber `pending`, red `failed`) matching the site colours
- The proof chain `feature → claim → test → evidence → release` shown as a small inline diagram at the top of relevant pages

---

## Assets

| File | Use |
|---|---|
| `media/verity_icon.png` | Logo mark — use at 32px (nav), 48px (footer), 96px+ (hero) |

---

## Notes for Claude Design

- Dark mode only — don't design a light mode variant
- The chain-node motif from the icon should appear as a decorative element in the hero and section dividers
- Keep the teal accent reserved for interactive elements and the proof chain nodes — don't overuse it
- The five-step chain (`feature → claim → test → evidence → release`) is the core visual metaphor; it should feel intentional wherever it appears, not like a generic flowchart
- Prioritise readability and information density on the docs site — this is a developer tool, not a marketing brochure
