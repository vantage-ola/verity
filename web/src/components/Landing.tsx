import { useState } from 'react'
import { VerityChain, VerityMark } from './Chain'

function SectionHeader({ index, label }: { index: string; label: string }) {
  return (
    <div className="v-container" style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span className="v-mono" style={{ fontSize: 11, color: 'var(--muted)', letterSpacing: 'var(--tracking-wide)' }}>
          {index}
        </span>
        <span className="v-hr" style={{ flex: '0 0 32px' }} />
        <span className="v-overline">{label}</span>
      </div>
    </div>
  )
}

function CopyChip({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const onCopy = () => {
    try {
      navigator.clipboard?.writeText(text)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 1400)
  }
  return (
    <div className="v-codechip">
      <div className="v-codechip-text">{text}</div>
      <button className={'v-codechip-copy' + (copied ? ' copied' : '')} onClick={onCopy}>
        {copied ? 'Copied' : 'Copy'}
      </button>
    </div>
  )
}

function UseCase({ num, title, body, footer }: { num: string; title: string; body: string; footer: string }) {
  return (
    <div style={{ background: 'var(--bg)', padding: '32px 28px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="v-mono" style={{ fontSize: 11, color: 'var(--accent)', letterSpacing: 'var(--tracking-wide)' }}>
          CASE / {num}
        </span>
        <span className="v-badge v-badge-muted">live</span>
      </div>
      <h3 className="v-h3" style={{ margin: 0 }}>{title}</h3>
      <p className="v-body" style={{ color: 'var(--muted-2)', margin: 0, flex: 1 }}>{body}</p>
      <div className="v-hr" style={{ margin: '8px 0' }} />
      <div className="v-mono" style={{ fontSize: 11, color: 'var(--muted)', letterSpacing: 'var(--tracking-wide)' }}>
        {footer}
      </div>
    </div>
  )
}

function BackendCard({ name, eyebrow, desc, tags }: { name: string; eyebrow: string; desc: string; tags: string[] }) {
  return (
    <div style={{ background: 'var(--bg)', padding: '36px 32px' }}>
      <div className="v-overline" style={{ marginBottom: 12 }}>{eyebrow}</div>
      <h3 className="v-h2" style={{ margin: '0 0 16px', display: 'flex', alignItems: 'baseline', gap: 12 }}>
        {name}
        <span className="v-mono" style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 400 }}>backend</span>
      </h3>
      <p className="v-body" style={{ color: 'var(--muted-2)', margin: '0 0 24px' }}>{desc}</p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {tags.map(t => (
          <span key={t} className="v-mono" style={{
            padding: '4px 10px', fontSize: 11, color: 'var(--muted-2)', border: '1px solid var(--border)',
          }}>{t}</span>
        ))}
      </div>
    </div>
  )
}

function ResultRow({ label, value, status, mono }: { label: string; value: string; status?: string; mono?: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 13 }}>
      <span className="v-mono" style={{ color: 'var(--muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)' }}>
        {label}
      </span>
      <span
        className={mono ? 'v-mono' : ''}
        style={{ color: status === 'ok' ? 'var(--ok)' : 'var(--text-strong)', fontWeight: 600, fontSize: mono ? 12 : 14 }}
      >
        {value}
      </span>
    </div>
  )
}

function CodeSplit() {
  const [tab, setTab] = useState<'cli' | 'track' | 'json' | 'py'>('cli')
  return (
    <div style={{ border: '1px solid var(--border)' }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: '1px solid var(--border)', background: 'var(--surface)', padding: '0 16px',
        overflowX: 'auto',
      }}>
        <div style={{ display: 'flex' }}>
          <button className={'v-tab' + (tab === 'cli' ? ' active' : '')} onClick={() => setTab('cli')}>CLI</button>
          <button className={'v-tab' + (tab === 'track' ? ' active' : '')} onClick={() => setTab('track')}>Track</button>
          <button className={'v-tab' + (tab === 'json' ? ' active' : '')} onClick={() => setTab('json')}>JSON</button>
          <button className={'v-tab' + (tab === 'py' ? ' active' : '')} onClick={() => setTab('py')}>Python</button>
        </div>
        <div className="v-mono" style={{ fontSize: 11, color: 'var(--muted)', letterSpacing: 'var(--tracking-wide)', whiteSpace: 'nowrap', paddingLeft: 12 }}>
          {tab === 'track' && '~/proj $'}{tab === 'cli' && '~/proj $'}{tab === 'json' && 'verity.json'}{tab === 'py' && 'session.py'}
        </div>
      </div>
      <div className="v-code-split-cols">
        <div className="v-code" style={{ border: 0, padding: '20px 24px' }}>
          {tab === 'track' && (
            <>
              <span className="c-comm"># one command — claim + test + evidence in one step</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity track</span> <span className="c-id">feat:auth</span> <span className="c-str">tests/test_auth.py</span> <span className="c-flag">--status</span> passed{'\n'}
              <span className="c-out">  Added clm:auth.2  tst:auth.3  evd:auth.4</span>{'\n'}
              {'\n'}
              <span className="c-comm"># inspect what you've built</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity status</span>{'\n'}
              <span className="c-out">  features 1  claims 1 (1 verified)</span>{'\n'}
              <span className="c-out">  tests    1 (1 passing)</span>{'\n'}
              <span className="c-out">  evidence 1 (1 passed)  valid ✓</span>{'\n'}
              {'\n'}
              <span className="c-comm"># release and push to Walrus</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity release</span> <span className="c-num">1.0.0</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity push</span> <span className="c-flag">--backend</span> memwal{'\n'}
              <span className="c-out">  → blob: </span><span className="c-id">AbCdEfGh…</span>
            </>
          )}
          {tab === 'cli' && (
            <>
              <span className="c-comm"># 1. declare a feature you're about to ship</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity add feature</span> <span className="c-id">feat:auth</span> <span className="c-str">"User authentication"</span>{'\n'}
              {'\n'}
              <span className="c-comm"># 2. make a testable claim about it</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity add claim</span> <span className="c-id">clm:auth.t1</span> <span className="c-str">"Login succeeds"</span> <span className="c-flag">--feature</span> <span className="c-id">feat:auth</span>{'\n'}
              {'\n'}
              <span className="c-comm"># 3. attach the test that proves the claim</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity add test</span> <span className="c-id">tst:auth.unit</span> <span className="c-str">"Unit test"</span> <span className="c-flag">--claim</span> <span className="c-id">clm:auth.t1</span> <span className="c-flag">--path</span> <span className="c-str">tests/test_auth.py</span>{'\n'}
              {'\n'}
              <span className="c-comm"># 4. record the evidence from a real run</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity add evidence</span> <span className="c-id">evd:auth.ci</span> <span className="c-str">"CI run"</span> <span className="c-flag">--test</span> <span className="c-id">tst:auth.unit</span> <span className="c-flag">--artifact</span> <span className="c-str">reports/ci.json</span> <span className="c-flag">--status</span> passed{'\n'}
              {'\n'}
              <span className="c-comm"># 5. cut a release, push the chain to Walrus</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity release</span> <span className="c-num">1.0.0</span>{'\n'}
              <span className="c-prompt">$ </span><span className="c-cmd">verity push</span> <span className="c-flag">--backend</span> memwal{'\n'}
              <span className="c-out">  → blob: </span><span className="c-id">AbCdEfGh…</span>
            </>
          )}
          {tab === 'json' && (
            <>
              {'{'}{'\n'}
              {'  '}<span className="c-key">"version"</span>: <span className="c-str">"1.0.0"</span>,{'\n'}
              {'  '}<span className="c-key">"features"</span>: {'['}{'\n'}
              {'    {'} <span className="c-key">"id"</span>: <span className="c-id">"feat:auth"</span>,{'\n'}
              {'      '}<span className="c-key">"title"</span>: <span className="c-str">"User authentication"</span>,{'\n'}
              {'      '}<span className="c-key">"status"</span>: <span className="c-str">"verified"</span> {'}'}{'\n'}
              {'  ],\n'}
              {'  '}<span className="c-key">"claims"</span>: {'[\n'}
              {'    {'} <span className="c-key">"id"</span>: <span className="c-id">"clm:auth.t1"</span>,{'\n'}
              {'      '}<span className="c-key">"feature"</span>: <span className="c-id">"feat:auth"</span>,{'\n'}
              {'      '}<span className="c-key">"text"</span>: <span className="c-str">"Login succeeds"</span> {'}'}{'\n'}
              {'  ],\n'}
              {'  '}<span className="c-key">"evidence"</span>: {'[\n'}
              {'    {'} <span className="c-key">"id"</span>: <span className="c-id">"evd:auth.ci"</span>,{'\n'}
              {'      '}<span className="c-key">"test_id"</span>: <span className="c-id">"tst:auth.unit"</span>,{'\n'}
              {'      '}<span className="c-key">"artifact_path"</span>: <span className="c-str">"reports/ci.json"</span>,{'\n'}
              {'      '}<span className="c-key">"status"</span>: <span className="c-str">"passed"</span> {'}'}{'\n'}
              {'  ],\n'}
              {'  '}<span className="c-key">"blob_id"</span>: <span className="c-id">"AbCdEfGh…"</span>{'\n'}
              {'}'}
            </>
          )}
          {tab === 'py' && (
            <>
              <span className="c-flag">from</span> verity <span className="c-flag">import</span> VeritySession, WalrusBackend{'\n'}
              {'\n'}
              v = VeritySession(<span className="c-str">"verity.json"</span>, backend=WalrusBackend()){'\n'}
              v.add_feature(<span className="c-str">"feat:auth"</span>, <span className="c-str">"User authentication"</span>){'\n'}
              v.add_claim(<span className="c-str">"clm:auth.t1"</span>, <span className="c-str">"Login succeeds"</span>,{'\n'}
              {'           '}feature_id=<span className="c-str">"feat:auth"</span>, status=<span className="c-str">"verified"</span>){'\n'}
              v.add_test(<span className="c-str">"tst:auth.unit"</span>, claim_id=<span className="c-str">"clm:auth.t1"</span>,{'\n'}
              {'          '}path=<span className="c-str">"tests/test_auth.py"</span>, status=<span className="c-str">"passing"</span>){'\n'}
              v.add_evidence(<span className="c-str">"evd:auth.ci"</span>, test_id=<span className="c-str">"tst:auth.unit"</span>,{'\n'}
              {'              '}artifact_path=<span className="c-str">"reports/ci.json"</span>, status=<span className="c-str">"passed"</span>){'\n'}
              v.release(<span className="c-str">"1.0.0"</span>){'\n'}
              blob_id = v.push(){'\n'}
              {'\n'}
              <span className="c-comm"># blob_id → "AbCdEfGh…"  (plain string)</span>
            </>
          )}
        </div>
        <div style={{ background: 'var(--surface)', padding: '20px 24px' }}>
          <div className="v-overline" style={{ marginBottom: 16 }}>What you get</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <ResultRow label="features" value="1" />
            <ResultRow label="claims" value="1" />
            <ResultRow label="tests" value="1" />
            <ResultRow label="evidence" value="1" status="ok" />
            <ResultRow label="release" value="1.0.0" />
            <div className="v-hr" />
            <ResultRow label="blob_id" value="AbCdEfGh…" mono />
            <ResultRow label="backend" value="walrus" />
            <ResultRow label="log" value="1 push" />
          </div>
        </div>
      </div>
    </div>
  )
}

export function Landing({ onDocs }: { onDocs: () => void }) {
  return (
    <div className="v-app" style={{ overflow: 'hidden' }}>

      {/* Nav */}
      <header className="v-nav-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <VerityMark size={28} />
          <span className="v-wordmark" style={{ fontSize: 20 }}>verity</span>
          <span className="v-mono" style={{
            fontSize: 11, color: 'var(--muted)', padding: '3px 7px',
            border: '1px solid var(--border)', marginLeft: 6,
          }}>v0.3.7</span>
        </div>
        <nav style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div className="v-nav-text">
            <button onClick={onDocs} className="v-overline" style={{ background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'none', padding: 0 }}>Docs</button>
            <a href="https://github.com/vantage-ola/verity" className="v-overline" style={{ textDecoration: 'none' }} target="_blank" rel="noopener noreferrer">GitHub</a>
            <a href="https://pypi.org/project/walrus-verity/" className="v-overline" style={{ textDecoration: 'none' }} target="_blank" rel="noopener noreferrer">PyPI</a>
          </div>
          <a href="#install" className="v-btn v-btn-primary">Install →</a>
        </nav>
      </header>

      {/* Hero */}
      <section className="v-hero">
        <div style={{ maxWidth: 880, margin: '0 auto' }}>
          <div className="v-overline-accent" style={{ marginBottom: 24 }}>
            Proof-chain registry · for AI agents
          </div>
          <h1 className="v-display" style={{ margin: '0 0 28px', maxWidth: 760 }}>
            Track what your agent{' '}
            <em style={{ fontStyle: 'normal', color: 'var(--accent)' }}>claimed</em>, what it{' '}
            <em style={{ fontStyle: 'normal', color: 'var(--accent)' }}>tested</em>, and what it{' '}
            <em style={{ fontStyle: 'normal', color: 'var(--accent)' }}>proved</em>.
          </h1>
          <p className="v-body-lg" style={{ margin: '0 0 40px', maxWidth: 640 }}>
            Backed by Walrus for permanent, portable, verifiable memory. Push from one agent.
            Pull by blob ID from any agent, any session.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <CopyChip text="pip install walrus-verity" />
            <button onClick={onDocs} className="v-btn v-btn-ghost" style={{ color: 'var(--text)' }}>
              Read the docs →
            </button>
          </div>
        </div>
      </section>

      {/* Chain centerpiece */}
      <section className="v-section" style={{
        borderTop: '1px solid var(--border)',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg)',
      }}>
        <SectionHeader index="01" label="How it works" />
        <div className="v-container">
          <div className="v-section-row">
            <h2 className="v-h1" style={{ margin: 0, maxWidth: 580 }}>
              Five steps. One chain. Every action is anchored to the last.
            </h2>
            <span className="v-small v-section-row-hint">Hover any node →</span>
          </div>
          <div className="v-chain-scroll">
            <VerityChain />
          </div>
        </div>
      </section>

      {/* Code example */}
      <section className="v-section">
        <SectionHeader index="02" label="In code" />
        <div className="v-container">
          <h2 className="v-h1" style={{ margin: '0 0 32px', maxWidth: 640 }}>
            One CLI. The proof chain writes itself.
          </h2>
          <CodeSplit />
        </div>
      </section>

      {/* Use cases */}
      <section className="v-section" style={{ borderTop: '1px solid var(--border)' }}>
        <SectionHeader index="03" label="What you build with it" />
        <div className="v-container">
          <h2 className="v-h1" style={{ margin: '0 0 48px', maxWidth: 640 }}>
            Built for the gaps in agent workflows.
          </h2>
          <div className="v-grid-2">
            <UseCase
              num="A"
              title="Multi-agent handoff"
              body="Agent A proves its work. Agent B verifies before building on it. No re-running the same tests."
              footer="agent → blob → agent"
            />
            <UseCase
              num="B"
              title="Autonomous monitoring"
              body="Every push is a timestamped, immutable snapshot. Supervisors fetch by blob ID or query via the MemWal SDK — no polling, no scraping."
              footer="immutable · timestamped"
            />
            <UseCase
              num="C"
              title="CI/CD audit trail"
              body="Add verity push to your pipeline and every merge publishes a new blob_id. The push log is the audit trail."
              footer="merge → blob → ledger"
            />
            <UseCase
              num="D"
              title="DevSecOps export"
              body="Export your proof chain to SARIF, JUnit XML, or SPDX in one command. Feed CI dashboards, audit tools, and compliance pipelines without knowing verity's schema."
              footer="verity export --format sarif|junit|spdx"
            />
          </div>
        </div>
      </section>

      {/* Walrus + MemWal */}
      <section className="v-section" style={{ borderTop: '1px solid var(--border)' }}>
        <SectionHeader index="04" label="The storage layer" />
        <div className="v-container">
          <h2 className="v-h1" style={{ margin: '0 0 12px', maxWidth: 640 }}>
            Walrus for blobs. MemWal for recall.
          </h2>
          <p className="v-body-lg" style={{ margin: '0 0 48px', maxWidth: 640 }}>
            verity is the registry. The data lives on Sui's decentralised storage —
            immutable, addressable, and yours.
          </p>
          <div className="v-grid-2">
            <BackendCard
              name="Walrus"
              eyebrow="Immutable blob storage"
              desc="Push your proof chain. Get back a blob_id. The blob is content-addressed, replicated across the Sui network, and impossible to silently alter."
              tags={['immutable', 'content-addressed', 'sui-native']}
            />
            <BackendCard
              name="MemWal"
              eyebrow="Semantic discovery layer"
              desc="verity push --backend memwal registers a semantic pointer in MemWal alongside the blob. Agents can then use the MemWal SDK to recall registries by repo without knowing the blob ID upfront."
              tags={['semantic', 'discoverable', 'walrus-native']}
            />
          </div>
        </div>
      </section>

      {/* Install strip */}
      <section id="install" className="v-section" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="v-container">
          <div className="v-install-flex">
            <div>
              <div className="v-overline-accent" style={{ marginBottom: 16 }}>Get started</div>
              <h2 className="v-h1" style={{ margin: '0 0 8px', maxWidth: 520 }}>
                Two commands. Five minutes.
              </h2>
              <p className="v-body" style={{ color: 'var(--muted-2)', margin: 0 }}>
                MIT licensed. Python 3.11+. No account, no key, no telemetry.
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <CopyChip text="pip install walrus-verity" />
              <CopyChip text='pip install "walrus-verity[memwal]"' />
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="v-footer">
        <div className="v-footer-row">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <VerityMark size={24} />
            <span className="v-wordmark" style={{ fontSize: 16 }}>verity</span>
            <span className="v-small" style={{ color: 'var(--muted)', marginLeft: 8 }}>
              Proof-chain registry for AI agents.
            </span>
          </div>
          <div className="v-footer-links">
            <a href="https://github.com/vantage-ola/verity" className="v-overline" style={{ textDecoration: 'none' }} target="_blank" rel="noopener noreferrer">GitHub</a>
            <a href="https://pypi.org/project/walrus-verity/" className="v-overline" style={{ textDecoration: 'none' }} target="_blank" rel="noopener noreferrer">PyPI</a>
            <button onClick={onDocs} className="v-overline" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>Docs</button>
            <a href="https://github.com/vantage-ola/verity/blob/main/LICENSE" className="v-overline" style={{ textDecoration: 'none' }} target="_blank" rel="noopener noreferrer">License · MIT</a>
          </div>
        </div>
      </footer>

    </div>
  )
}
