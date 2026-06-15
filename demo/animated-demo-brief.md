# Animated Demo Brief — verity

## What this is

A looping animated explainer showing how verity works end-to-end. Not a slideshow. Not a video. A live HTML animation that plays through the full story — Agent A builds a proof chain, pushes to Walrus, hands off a blob ID, Agent B pulls and verifies, both agents end up with the same immutable receipt.

---

## Visual style

- **Background**: `#1e1e2e` (Catppuccin Mocha base)
- **Primary accent**: `#89b4fa` (blue)
- **Green / success**: `#a6e3a1`
- **Text strong**: `#cdd6f4`
- **Muted text**: `#585b70`
- **Surface panels**: `#181825`
- **Font**: system monospace stack — `'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace`
- **Feel**: minimal, dark, developer tool. No gradients, no glassmorphism. Crisp edges, clean type, purposeful motion.
- **Easing**: ease-in-out on all transitions. Nothing bouncy.

---

## Layout

Three zones, horizontal:

```
┌─────────────────┐      ┌──────────┐      ┌─────────────────┐
│                 │      │          │      │                 │
│    AGENT A      │ ───► │  WALRUS  │ ◄─── │    AGENT B      │
│                 │      │          │      │                 │
└─────────────────┘      └──────────┘      └─────────────────┘
```

- Left panel: Agent A terminal (dark surface, monospace text)
- Center: Walrus node — circular or hexagonal, glowing `#89b4fa` when active
- Right panel: Agent B terminal

The two terminals look like real terminal windows — title bar with three dots (red/yellow/green), a blinking cursor, monospace font, command output appearing line by line.

---

## Animation sequence

### Scene 1 — Agent A builds the chain (0s – 6s)

Agent A terminal fades in. Commands type themselves one by one, each output line fading in after a short delay:

```
$ verity init --repo-id repo:payments-api
  ✓ Created .verity/registry.json

$ verity add feature feat:payments "Payment processing"
  ✓ feat:payments

$ verity track feat:payments tests/test_payments.py
  ✓ clm:payments.1  tst:payments.2  evd:payments.3

$ verity release 1.0.0
  ✓ rel:1.0.0 — 1 claim verified
```

Alongside the terminal, a vertical chain diagram builds up on the left side of Agent A's panel — nodes appearing one at a time in sequence:

```
● feat:payments  (blue)
  ↓
● clm:payments.1  (blue)
  ↓
● tst:payments.2  (blue)
  ↓
● evd:payments.3  (green — passed)
  ↓
● rel:1.0.0  (white)
```

Each node pulses briefly as it appears.

---

### Scene 2 — Push to Walrus (6s – 9s)

```
$ verity sign --key agent-a.key
  ✓ signed

$ verity push --upload-artifacts
```

A particle stream animates from the Agent A panel toward the Walrus center node. The stream looks like small dots flowing left-to-right. The Walrus node pulses and brightens as it receives.

Output appears:

```
  evd:payments.3  → walrus://AbCd…
  blob: XyZabc123MainBlobId…
```

The blob ID appears in `#89b4fa` and holds on screen for 1.5s — it's the key moment.

A tag appears below the Walrus node: `XyZabc…` in small monospace text.

---

### Scene 3 — Blob ID handoff (9s – 10.5s)

A thin glowing line draws from Agent A's panel to Agent B's panel, passing through the Walrus node. The blob ID `XyZabc…` slides along the line as a chip/badge.

Agent B terminal fades in.

---

### Scene 4 — Agent B verifies (10.5s – 15s)

```
$ verity pull XyZabc123MainBlobId…
  ✓ Fetched .verity/registry.json

$ verity verify XyZabc123MainBlobId…
  blob: XyZabc123MainBlobId…
  features 1  claims 1 (1 verified)
  chain valid ✓
  signature valid ✓
```

The `chain valid ✓` and `signature valid ✓` lines appear in green and hold for a beat.

The chain diagram from Agent A reappears inside Agent B's panel — same nodes, same structure — showing that Agent B has the exact same chain.

---

### Scene 5 — Agent B extends (15s – 20s)

```
$ verity add feature feat:audit "Audit logging"
$ verity track feat:audit tests/test_audit.py
$ verity release 1.1.0
$ verity push
  blob: NewBlobId456…
```

A new node appears below the chain in Agent B's panel — `feat:audit` in blue. The chain now has two features.

Another particle stream flows from Agent B to Walrus. Walrus pulses again. New blob tag: `NewBlobId456…`.

---

### Scene 6 — Final state (20s – 24s)

Both terminals visible. Both show a clean `verity status` output:

```
  features 2  claims 2 (2 verified)
  tests    2 (2 passing)
  evidence 2 (2 passed)  valid ✓
  blob: NewBlobId456…
```

The Walrus node shows two stacked tags — both blob IDs — with a subtle link between them showing lineage.

Hold for 2s.

---

### Scene 7 — Title card (24s – 26s)

Everything fades to near-black. Text fades in centered:

```
verity
Proof chains for AI agents, on Walrus.

uv tool install "walrus-verity[all]"
```

`verity` in large white text, tagline in muted, install command in `#89b4fa` monospace.

Loop back to Scene 1.

---

## Key animation details

- **Typing effect**: characters appear one at a time, ~30ms per character for commands, instant for output lines (output shouldn't feel typed, just revealed)
- **Node pulse**: scale 1 → 1.08 → 1 over 300ms when a chain node appears
- **Particle stream**: 8–12 small circles, staggered 80ms apart, travelling a bezier curve from source to Walrus
- **Walrus pulse**: border glow expands from 0 to 12px and fades over 600ms when receiving data
- **Blob ID chip on the handoff line**: slides along the path over 1.2s, eases in and out
- **Scene transitions**: 300ms opacity fade between major scenes, no hard cuts
- **Loop**: Scene 7 fades back to black, then Scene 1 fades in — seamless

---

## Terminal window anatomy

Each terminal panel:
- Dark surface (`#181825`) with 1px border (`#313244`)
- Title bar: `#11111b`, three dots left (red `#f38ba8`, yellow `#f9e2af`, green `#a6e3a1`), centered label `AGENT A` or `AGENT B` in small muted caps
- Content area: padding 20px, monospace 13px
- Prompt: `$ ` in `#89b4fa`
- Commands: `#cdd6f4`
- Output / success lines: `#a6e3a1` for ✓, `#cdd6f4` for info
- Blob IDs: `#89b4fa`
- Cursor: blinking `|` in `#89b4fa`

---

## Walrus center node

- Circle, ~80px diameter
- Border: 2px solid `#89b4fa`
- Background: `#181825`
- Label: `WALRUS` in small caps above the circle, muted
- Blob ID tags: small rounded rectangles below the circle, `#313244` background, `#89b4fa` text, monospace 10px
- Glow effect on receive: `box-shadow: 0 0 0 12px rgba(137, 180, 250, 0.15)` fading out

---

## What NOT to do

- No slide transitions or carousels
- No spinning logos or 3D effects
- No stock illustrations or abstract shapes
- No confetti, particles that drift randomly, or "AI brain" imagery
- No sound indicators or play/pause controls — it should autoplay and loop silently
- Don't show fake "loading" states or progress bars unrelated to the demo
- Don't use Comic Sans, rounded fonts, or anything that doesn't fit the terminal aesthetic
