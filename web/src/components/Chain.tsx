import { useEffect, useState } from 'react'

const NODES = [
  { id: 'feature',  label: 'feature',  num: '01', desc: 'A capability you intend to ship — the unit of work.' },
  { id: 'claim',    label: 'claim',    num: '02', desc: 'A testable statement about what that feature does.' },
  { id: 'test',     label: 'test',     num: '03', desc: 'The mechanism that exercises the claim.' },
  { id: 'evidence', label: 'evidence', num: '04', desc: 'The pass / fail signal the test produced.' },
  { id: 'release',  label: 'release',  num: '05', desc: 'A signed snapshot — pushed to Walrus, recallable anywhere.' },
]

export function VerityChain() {
  const [current, setCurrent] = useState(0)
  const [paused, setPaused] = useState(false)
  const [hover, setHover] = useState<number | null>(null)

  useEffect(() => {
    if (paused) return
    const t = setInterval(() => {
      setCurrent(c => (c + 1) % (NODES.length + 1))
    }, 1400)
    return () => clearInterval(t)
  }, [paused])

  const activeIdx = current < NODES.length ? current : -1

  return (
    <div
      className="v-chain-wrap"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => { setPaused(false); setHover(null) }}
    >
      {NODES.map((n, i) => (
        <div key={n.id} style={{ display: 'contents' }}>
          <div
            className={[
              'v-chain-node',
              i === activeIdx ? 'active' : '',
              i <= activeIdx ? 'lit' : '',
              i === hover ? 'active' : '',
            ].filter(Boolean).join(' ')}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          >
            <div className="v-chain-square">
              <span className="v-chain-num">{n.num}</span>
              {n.label}
            </div>
            <div className="v-chain-label">{n.label}</div>
            <div className="v-chain-desc">{n.desc}</div>
          </div>
          {i < NODES.length - 1 && (
            <div className={['v-chain-connector', i < activeIdx ? 'lit' : ''].filter(Boolean).join(' ')}>
              <div className="v-chain-connector-track">
                <div className="v-chain-connector-fill" />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export function VerityChainInline({ highlight }: { highlight?: string }) {
  const steps = ['feature', 'claim', 'test', 'evidence', 'release']
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      fontFamily: 'var(--font-mono)', fontSize: 11, textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-wide)', color: 'var(--muted)', padding: '8px 0',
    }}>
      {steps.map((s, i) => (
        <div key={s} style={{ display: 'contents' }}>
          <span style={{
            padding: '4px 8px',
            border: `1px solid ${highlight === s ? 'var(--accent)' : 'var(--border)'}`,
            color: highlight === s ? 'var(--accent)' : 'var(--muted-2)',
            background: highlight === s ? 'var(--accent-soft)' : 'transparent',
          }}>{s}</span>
          {i < steps.length - 1 && <span style={{ color: 'var(--border-strong)' }}>→</span>}
        </div>
      ))}
    </div>
  )
}

export function VerityMark({ size = 28 }: { size?: number }) {
  return (
    <div
      className="v-logo-mark"
      style={{ width: size, height: size }}
      aria-label="verity"
    />
  )
}
