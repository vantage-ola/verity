import { useState } from 'react'
import { VerityMark } from './Chain'

// ── helpers ──────────────────────────────────────────────────────────────────

function Code({ children }: { children: React.ReactNode }) {
  return (
    <div className="v-code" style={{ padding: '18px 20px', marginBottom: 24 }}>
      {children}
    </div>
  )
}

function InlineCode({ children }: { children: React.ReactNode }) {
  return (
    <code style={{
      fontFamily: 'var(--font-mono)', fontSize: '0.85em',
      background: 'var(--surface)', padding: '2px 6px',
      border: '1px solid var(--border)', color: 'var(--text-strong)',
    }}>{children}</code>
  )
}

function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="v-h2" style={{ margin: '0 0 16px', paddingTop: 40, borderTop: '1px solid var(--border)' }}>{children}</h2>
}

function H3({ children }: { children: React.ReactNode }) {
  return <h3 className="v-h3" style={{ margin: '28px 0 10px' }}>{children}</h3>
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="v-body" style={{ color: 'var(--muted-2)', margin: '0 0 16px', lineHeight: 1.65 }}>{children}</p>
}

function Table({ headers, rows }: { headers: string[]; rows: (string | React.ReactNode)[][] }) {
  return (
    <div style={{ overflowX: 'auto', marginBottom: 24 }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            {headers.map(h => (
              <th key={h} style={{ textAlign: 'left', padding: '8px 12px', fontFamily: 'var(--font-mono)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)', color: 'var(--muted)', fontWeight: 600 }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
              {row.map((cell, j) => (
                <td key={j} style={{ padding: '10px 12px', color: 'var(--muted-2)', fontFamily: j === 0 ? 'var(--font-mono)' : undefined, fontSize: j === 0 ? 12 : 13 }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Callout({ children }: { children: React.ReactNode }) {
  return <div className="v-callout" style={{ marginBottom: 24 }}>{children}</div>
}

// ── sections ─────────────────────────────────────────────────────────────────

function QuickStart() {
  return (
    <div>
      <div className="v-overline-accent" style={{ marginBottom: 12 }}>Getting started</div>
      <h1 className="v-h1" style={{ margin: '0 0 16px' }}>Quick Start</h1>
      <P>Install verity, build a proof chain, push it to Walrus in under five minutes.</P>

      <H2>Install</H2>
      <Code>pip install walrus-verity</Code>
      <P>For MemWal semantic discovery, add the optional extra:</P>
      <Code>pip install "walrus-verity[memwal]"</Code>

      <H2>Initialise</H2>
      <Code>
        <span className="c-prompt">$ </span><span className="c-cmd">verity init</span>{'\n'}
        <span className="c-out">Initialized verity.json</span>{'\n\n'}
        <span className="c-comm"># or in a specific directory</span>{'\n'}
        <span className="c-prompt">$ </span><span className="c-cmd">verity init</span> /path/to/project <span className="c-flag">--repo-id</span> repo:my-agent
      </Code>

      <H2>Build a proof chain</H2>
      <P>Every entity links to the one before it: feature → claim → test → evidence. The CLI validates on every write. Build with neutral statuses first, then promote them once the chain is fully linked.</P>
      <Code>
        <span className="c-comm"># Phase 1 — build the chain (neutral statuses)</span>{'\n'}
        <span className="c-prompt">$ </span><span className="c-cmd">verity add feature</span>  <span className="c-id">feat:auth</span>   <span className="c-str">"User authentication"</span>{'\n'}
        <span className="c-prompt">$ </span><span className="c-cmd">verity add claim</span>    <span className="c-id">clm:auth.t1</span> <span className="c-str">"Login succeeds"</span>  <span className="c-flag">--feature</span> <span className="c-id">feat:auth</span>{'\n'}
        <span className="c-prompt">$ </span><span className="c-cmd">verity add test</span>     <span className="c-id">tst:auth.unit</span> <span className="c-str">"Login unit test"</span> <span className="c-flag">--claim</span> <span className="c-id">clm:auth.t1</span> <span className="c-flag">--path</span> tests/test_auth.py{'\n'}
        <span className="c-prompt">$ </span><span className="c-cmd">verity add evidence</span> <span className="c-id">evd:auth.ci</span>   <span className="c-str">"CI run #1"</span>       <span className="c-flag">--test</span> <span className="c-id">tst:auth.unit</span> <span className="c-flag">--artifact</span> ci.json <span className="c-flag">--status</span> passed{'\n\n'}
        <span className="c-comm"># Phase 2 — promote statuses in verity.json, then validate</span>{'\n'}
        <span className="c-comm"># set claim → verified, test → passing</span>{'\n'}
        <span className="c-prompt">$ </span><span className="c-cmd">verity validate</span>{'\n'}
        <span className="c-ok">OK</span>
      </Code>

      <Callout>
        <strong>Why two phases?</strong> A claim can only be <code>verified</code> once a linked test exists. A test can only be <code>passing</code> once linked passed evidence exists. Build links first, set statuses after. Or use the <strong>Python API</strong> which defers validation until <code>validate()</code>.
      </Callout>

      <H2>Release and push</H2>
      <Code>
        <span className="c-prompt">$ </span><span className="c-cmd">verity release</span> <span className="c-num">1.0.0</span>{'\n'}
        <span className="c-out">Released rel:1.0.0 at 2026-05-25T12:00:00Z</span>{'\n'}
        <span className="c-out">  claims: clm:auth.t1</span>{'\n\n'}
        <span className="c-prompt">$ </span><span className="c-cmd">verity push</span>{'\n'}
        <span className="c-out">blob: </span><span className="c-id">AbCdEfGhIjKlMnOpQrStUvWxYz…</span>
      </Code>

      <Callout>
        <strong>Fail-closed releases.</strong> <code>verity release</code> aborts if any verified claim has no passing test with passed evidence. Fix the gaps before releasing.
      </Callout>

      <H2>View the push log</H2>
      <Code>
        <span className="c-prompt">$ </span><span className="c-cmd">verity log</span>{'\n'}
        <span className="c-out">  1.  [walrus]  2026-05-25T12:00:00Z  AbCdEfGhIjKlMnOpQrStUvWxYz…</span>
      </Code>
    </div>
  )
}

function CliRef() {
  return (
    <div>
      <div className="v-overline-accent" style={{ marginBottom: 12 }}>Reference</div>
      <h1 className="v-h1" style={{ margin: '0 0 16px' }}>CLI Reference</h1>
      <P>All commands read <InlineCode>verity.json</InlineCode> from the current directory unless <InlineCode>--dir</InlineCode> is passed.</P>

      <H2>verity init</H2>
      <P>Create <InlineCode>verity.json</InlineCode>. Fails if it already exists.</P>
      <Code>
        verity init [DIRECTORY] [<span className="c-flag">--repo-id</span> TEXT]
      </Code>
      <Table
        headers={['Option', 'Default', 'Description']}
        rows={[
          ['DIRECTORY', '.', 'Where to create verity.json'],
          ['--repo-id', 'repo:default', 'Registry identifier'],
        ]}
      />

      <H2>verity add feature</H2>
      <Code>verity add feature ID TITLE</Code>
      <Code>
        <span className="c-prompt">$ </span>verity add feature <span className="c-id">feat:auth</span> <span className="c-str">"User authentication"</span>
      </Code>

      <H2>verity add claim</H2>
      <Code>verity add claim ID TITLE <span className="c-flag">--feature</span> FEAT_ID [<span className="c-flag">--tier</span> T1|T2|T3] [<span className="c-flag">--status</span> open|verified|rejected]</Code>
      <Table
        headers={['Option', 'Default', 'Description']}
        rows={[
          ['--feature', 'required', 'Parent feature ID'],
          ['--tier', 'T1', 'Claim tier'],
          ['--status', 'open', 'Do not pass verified here; promote after test is linked'],
        ]}
      />

      <H2>verity add test</H2>
      <Code>verity add test ID TITLE <span className="c-flag">--claim</span> CLM_ID [<span className="c-flag">--kind</span> unit|integration] [<span className="c-flag">--path</span> PATH] [<span className="c-flag">--status</span> pending|passing|failing]</Code>
      <p style={{ fontSize: 12, color: 'var(--muted)', margin: '0 0 16px' }}>Do not pass <InlineCode>--status passing</InlineCode> here; promote after evidence is linked.</p>

      <H2>verity add evidence</H2>
      <Code>verity add evidence ID TITLE <span className="c-flag">--test</span> TST_ID [<span className="c-flag">--artifact</span> PATH] [<span className="c-flag">--kind</span> TEXT] [<span className="c-flag">--status</span> passed|failed|collected]</Code>
      <p style={{ fontSize: 12, color: 'var(--muted)', margin: '0 0 16px' }}>Evidence status can be set at add time with no downstream dependencies.</p>

      <H2>verity track</H2>
      <Code>verity track FEATURE_ID TEST_PATH [<span className="c-flag">--status</span> passed|failed|collected] [<span className="c-flag">--title</span> TITLE] [<span className="c-flag">--kind</span> unit|integration]</Code>
      <P>Auto-create a claim, test, and evidence entry for a feature in one step. The full chain is wired and validated before saving. No two-phase setup required.</P>
      <Table
        headers={['--status', 'claim', 'test', 'evidence']}
        rows={[
          ['passed (default)', 'verified', 'passing', 'passed'],
          ['failed', 'open', 'failing', 'failed'],
          ['collected', 'open', 'pending', 'collected'],
        ]}
      />
      <p style={{ fontSize: 12, color: 'var(--muted)', margin: '0 0 8px' }}>IDs are auto-generated from the feature slug (<code>feat:auth</code> → <code>clm:auth.track</code>, <code>tst:auth.track</code>, <code>evd:auth.track</code>). Repeated calls append <code>.2</code>, <code>.3</code>, etc.</p>
      <Code>
        <span className="c-prompt">$ </span><span className="c-cmd">verity track</span> <span className="c-id">feat:auth</span> tests/test_auth.py{'\n'}
        Tracked feat:auth via tests/test_auth.py{'\n'}
        {'  '}<span className="c-id">clm:auth.track</span>  (verified){'\n'}
        {'  '}<span className="c-id">tst:auth.track</span>  (passing){'\n'}
        {'  '}<span className="c-id">evd:auth.track</span>  (passed)
      </Code>

      <H2>verity validate</H2>
      <P>Checks all links, duplicate IDs, and status consistency. Exits non-zero on any error.</P>
      <Table
        headers={['Rule', '']}
        rows={[
          ['Broken links', 'claim→feature, test→claim, evidence→test, release→claim'],
          ['Duplicate IDs', 'within each entity type'],
          ['Verified claims', 'must have ≥1 linked test'],
          ['Passing tests', 'must have ≥1 linked evidence'],
        ]}
      />

      <H2>verity release</H2>
      <P>Create a named release snapshot. <strong>Fail-closed</strong>: every verified claim must have a passing test with passed evidence or the command aborts.</P>
      <Code>
        verity release VERSION{'\n\n'}
        <span className="c-prompt">$ </span>verity release 1.0.0{'\n'}
        <span className="c-out">Released rel:1.0.0 at 2026-05-25T12:00:00Z</span>
      </Code>

      <H2>verity push</H2>
      <P>Serialize the registry to canonical JSON and upload to Walrus (or MemWal). Records the blob ID locally.</P>
      <Code>verity push [<span className="c-flag">--backend</span> walrus|memwal] [<span className="c-flag">--epochs</span> N]</Code>
      <Table
        headers={['Option', 'Default', 'Description']}
        rows={[
          ['--backend', 'walrus', 'Storage backend'],
          ['--epochs', '5', 'Walrus storage duration in epochs'],
        ]}
      />
      <Code>
        <span className="c-prompt">$ </span>verity push{'\n'}
        <span className="c-out">blob: AbCdEfGhIjKlMnOpQrStUvWxYz…</span>{'\n\n'}
        <span className="c-prompt">$ </span>verity push <span className="c-flag">--backend</span> memwal{'\n'}
        <span className="c-out">blob: AbCdEfGhIjKlMnOpQrStUvWxYz…</span>
      </Code>

      <H2>verity pull</H2>
      <P>Fetch a registry blob by ID and write it to <InlineCode>verity.json</InlineCode>. Overwrites any existing file.</P>
      <Code>
        verity pull BLOB_ID [<span className="c-flag">--backend</span> walrus|memwal]{'\n\n'}
        <span className="c-prompt">$ </span>verity pull AbCdEfGhIjKlMnOpQrStUvWxYz…
      </Code>

      <H2>verity status</H2>
      <P>Show a compact health summary of the registry: entity counts with status breakdowns, latest release, and validation result. Exits non-zero if the registry has validation errors.</P>
      <Code>verity status [DIRECTORY]</Code>
      <Code>
        <span className="c-prompt">$ </span>verity status{'\n'}
        <span className="c-out">repo:my-project  schema 0.1.0</span>{'\n'}
        <span className="c-out">features   6   claims    11  (10 verified, 1 open)</span>{'\n'}
        <span className="c-out">tests     11  (11 passing)</span>{'\n'}
        <span className="c-out">evidence  11  (11 passed)</span>{'\n'}
        <span className="c-out">releases   2   latest: rel:0.1.5  blob: AbCdEfGh…</span>{'\n'}
        <span className="c-out">valid      ✓</span>
      </Code>

      <H2>verity log</H2>
      <P>Print all push records stored in the registry.</P>
      <Code>
        <span className="c-prompt">$ </span>verity log{'\n'}
        <span className="c-out">  1.  [walrus]  2026-05-25T12:00:00Z  AbCdEfGhIjKlMnOpQrStUvWxYz…</span>
      </Code>

      <H2>verity site</H2>
      <P>Generate a human-readable HTML page from <InlineCode>verity.json</InlineCode> showing all entities, releases, and pushes.</P>
      <Code>verity site [<span className="c-flag">--output</span> PATH] [<span className="c-flag">--push</span>] [<span className="c-flag">--epochs</span> N]</Code>
      <Code>
        <span className="c-comm"># save locally</span>{'\n'}
        <span className="c-prompt">$ </span>verity site <span className="c-flag">--output</span> proof.html{'\n\n'}
        <span className="c-comm"># push HTML to Walrus and get a URL</span>{'\n'}
        <span className="c-prompt">$ </span>verity site <span className="c-flag">--push</span>{'\n'}
        <span className="c-out">blob: AbCdEfGh…</span>{'\n'}
        <span className="c-out">url:  https://aggregator.walrus-testnet.walrus.space/v1/blobs/AbCdEfGh…</span>
      </Code>

      <H2>verity context</H2>
      <P>Manage named key/value context entries inside <InlineCode>verity.json</InlineCode>. Entries travel with the registry and are stored as MemWal memories on <InlineCode>verity push --backend memwal</InlineCode>.</P>
      <Code>
        verity context set KEY VALUE{'\n'}
        verity context list{'\n'}
        verity context remove KEY{'\n\n'}
        <span className="c-prompt">$ </span>verity context set architecture <span className="c-str">"5-layer proof chain"</span>{'\n'}
        <span className="c-out">Set: architecture</span>{'\n\n'}
        <span className="c-prompt">$ </span>verity context list{'\n'}
        <span className="c-out">architecture: 5-layer proof chain</span>
      </Code>

      <H2>verity recall</H2>
      <P>Query MemWal with a natural language question and get an answer synthesized from memories registered during the last <InlineCode>verity push --backend memwal</InlineCode>. Requires <InlineCode>MEMWAL_KEY</InlineCode> and <InlineCode>MEMWAL_ACCOUNT_ID</InlineCode>.</P>
      <Code>verity recall QUERY [<span className="c-flag">--namespace</span> NS]</Code>
      <Table
        headers={['Option', 'Default', 'Description']}
        rows={[
          ['--namespace / -n', 'verity', 'MemWal namespace (overrides MEMWAL_NAMESPACE env var)'],
        ]}
      />
      <Code>
        <span className="c-prompt">$ </span>verity recall <span className="c-str">"what features have we built"</span>{'\n'}
        <span className="c-out">User authentication, Claim tracking, MemWal Natural Language Recall, …</span>{'\n\n'}
        <span className="c-prompt">$ </span>verity recall <span className="c-str">"what claims are verified"</span>{'\n'}
        <span className="c-out">Login succeeds (clm:auth.t1, T1), …</span>{'\n\n'}
        <span className="c-prompt">$ </span>verity recall <span className="c-str">"what was the latest release"</span>{'\n'}
        <span className="c-out">0.1.8 at 2026-05-31T… — 16 claims</span>{'\n\n'}
        <span className="c-prompt">$ </span>verity recall <span className="c-str">"architecture of this project"</span> <span className="c-flag">--namespace</span> my-project{'\n'}
        <span className="c-out">5-layer proof chain: feature → claim → test → evidence → release</span>
      </Code>
      <P>What gets indexed on each <InlineCode>verity push --backend memwal</InlineCode>: a registry blob pointer, all feature titles and statuses, all verified claim titles, the latest release version, and any context entries set via <InlineCode>verity context set</InlineCode>. All writes are non-fatal — if the MemWal relayer is unreachable the blob is still safely on Walrus.</P>

      <H2>verity install-skill</H2>
      <P>Install the verity context skill into your AI coding assistant. The skill teaches the tool verity's proof chain model, CLI, Python API, and multi-agent patterns, so you don't have to re-explain them each session.</P>
      <Code>
        verity install-skill [<span className="c-flag">--tool</span> claude|cursor|windsurf|aider|codex]{'\n\n'}
        <span className="c-comm"># Claude Code (global — all sessions)</span>{'\n'}
        <span className="c-prompt">$ </span>verity install-skill{'\n'}
        <span className="c-out">Installed for Claude Code → ~/.claude/CLAUDE.md</span>{'\n\n'}
        <span className="c-comm"># Cursor, Windsurf, Codex, Aider (project-level — run in your repo)</span>{'\n'}
        <span className="c-prompt">$ </span>verity install-skill <span className="c-flag">--tool</span> cursor{'\n'}
        <span className="c-out">Installed for cursor → .cursorrules</span>{'\n'}
        <span className="c-prompt">$ </span>verity install-skill <span className="c-flag">--tool</span> windsurf{'\n'}
        <span className="c-out">Installed for windsurf → .windsurfrules</span>{'\n'}
        <span className="c-prompt">$ </span>verity install-skill <span className="c-flag">--tool</span> codex{'\n'}
        <span className="c-out">Installed for codex → AGENTS.md</span>{'\n'}
        <span className="c-prompt">$ </span>verity install-skill <span className="c-flag">--tool</span> aider{'\n'}
        <span className="c-out">Installed for aider → CONVENTIONS.md</span>
      </Code>
      <Table
        headers={['Tool', 'Default', 'File written']}
        rows={[
          ['claude', 'yes', '~/.claude/CLAUDE.md (global)'],
          ['cursor', '', '.cursorrules (project)'],
          ['windsurf', '', '.windsurfrules (project)'],
          ['codex', '', 'AGENTS.md (project)'],
          ['aider', '', 'CONVENTIONS.md (project)'],
        ]}
      />
      <P>Running the command a second time is safe. It detects the existing skill block and skips.</P>

      <H2>MCP server</H2>
      <P>Expose all verity tools natively to any MCP-compatible editor (Claude Code, Cursor, Windsurf, Codex). No subprocess; the editor calls the tools directly.</P>
      <Code>
        <span className="c-comm"># install with MCP support</span>{'\n'}
        pip install <span className="c-str">"walrus-verity[mcp]"</span>{'\n\n'}
        <span className="c-comm"># add to claude_mcp_config.json (or equivalent)</span>{'\n'}
        {'{\n'}
        {'  '}<span className="c-str">"mcpServers"</span>{': {\n'}
        {'    '}<span className="c-str">"verity"</span>{': {\n'}
        {'      '}<span className="c-str">"command"</span>{': '}<span className="c-str">"verity-mcp"</span>{',\n'}
        {'      '}<span className="c-str">"env"</span>{': {\n'}
        {'        '}<span className="c-str">"WALRUS_PUBLISHER_URL"</span>{': '}<span className="c-str">"https://publisher.walrus-testnet.walrus.space"</span>{'\n'}
        {'      }\n'}
        {'    }\n'}
        {'  }\n'}
        {'}'}
      </Code>
      <Table
        headers={['MCP tool', 'Description']}
        rows={[
          ['verity_init', 'Create verity.json'],
          ['verity_add_feature / claim / test / evidence', 'Add chain entities'],
          ['verity_set_status', 'Promote status after chain is wired'],
          ['verity_validate', 'Validate the full chain'],
          ['verity_release', 'Fail-closed release'],
          ['verity_push / pull', 'Walrus push and pull'],
          ['verity_log', 'Push history'],
          ['verity_status', 'Entity counts + validation summary'],
        ]}
      />
    </div>
  )
}

function PythonApi() {
  return (
    <div>
      <div className="v-overline-accent" style={{ marginBottom: 12 }}>Reference</div>
      <h1 className="v-h1" style={{ margin: '0 0 16px' }}>Python API</h1>
      <P>The same operations as the CLI, exposed as Python methods for use in agent scripts and pipelines.</P>

      <H2>VeritySession</H2>
      <P>The primary interface. All mutating methods write through to <InlineCode>verity.json</InlineCode> immediately.</P>
      <Code>
        <span className="c-flag">from</span> verity <span className="c-flag">import</span> VeritySession, WalrusBackend{'\n\n'}
        <span className="c-comm"># backend is optional — required only if you call push() or pull()</span>{'\n'}
        v = VeritySession(<span className="c-str">"verity.json"</span>, backend=WalrusBackend())
      </Code>

      <H3>Constructor</H3>
      <Code>VeritySession(path=<span className="c-str">"verity.json"</span>, *, backend: StorageBackend | None = None)</Code>

      <H3>Methods</H3>
      <Table
        headers={['Method', 'Returns', 'Description']}
        rows={[
          ['init(repo_id?)', 'Registry', 'Create verity.json; raises FileExistsError if present'],
          ['add_feature(id, title, status?)', 'Feature', 'Append a feature'],
          ['add_claim(id, title, *, feature_id, tier?, status?)', 'Claim', 'Append a claim'],
          ['add_test(id, *, claim_id, kind?, path?, status?)', 'Test', 'Append a test'],
          ['add_evidence(id, *, test_id, artifact_path, kind?, status?)', 'Evidence', 'Append evidence'],
          ['validate()', 'list[str]', 'Return errors; empty list means clean'],
          ['release(version)', 'Release', 'Fail-closed snapshot; raises VerityReleaseError on guard failure'],
          ['push(*, epochs?)', 'str', 'Upload to backend; returns blob ID string'],
          ['pull(blob_id)', 'None', 'Fetch from backend; overwrites local registry'],
          ['log()', 'list[PushRecord]', 'All push records'],
          ['registry()', 'Registry', 'Current registry object'],
          ['set_context(key, value)', 'None', 'Upsert a context entry'],
          ['get_context(key)', 'str | None', 'Value for key, or None'],
          ['remove_context(key)', 'bool', 'Remove entry; True if it existed'],
        ]}
      />

      <H3>Full example</H3>
      <Code>
        <span className="c-flag">from</span> verity <span className="c-flag">import</span> VeritySession, WalrusBackend{'\n\n'}
        v = VeritySession(<span className="c-str">"verity.json"</span>, backend=WalrusBackend()){'\n'}
        v.init(repo_id=<span className="c-str">"repo:my-agent"</span>){'\n\n'}
        v.add_feature(<span className="c-str">"feat:auth"</span>, <span className="c-str">"User authentication"</span>){'\n'}
        v.add_claim(<span className="c-str">"clm:auth.t1"</span>, <span className="c-str">"Login succeeds"</span>,{'\n'}
        {'         '}feature_id=<span className="c-str">"feat:auth"</span>, status=<span className="c-str">"verified"</span>){'\n'}
        v.add_test(<span className="c-str">"tst:auth.unit"</span>,{'\n'}
        {'          '}claim_id=<span className="c-str">"clm:auth.t1"</span>,{'\n'}
        {'          '}path=<span className="c-str">"tests/test_auth.py"</span>,{'\n'}
        {'          '}status=<span className="c-str">"passing"</span>){'\n'}
        v.add_evidence(<span className="c-str">"evd:auth.ci"</span>,{'\n'}
        {'              '}test_id=<span className="c-str">"tst:auth.unit"</span>,{'\n'}
        {'              '}artifact_path=<span className="c-str">"reports/ci.json"</span>,{'\n'}
        {'              '}status=<span className="c-str">"passed"</span>){'\n\n'}
        errors = v.validate(){'\n'}
        assert errors == [], errors{'\n\n'}
        v.release(<span className="c-str">"1.0.0"</span>){'\n'}
        blob_id = v.push()  <span className="c-comm"># returns a plain string blob ID</span>{'\n'}
        print(blob_id)
      </Code>

      <H2>Low-level functions</H2>
      <P>Direct access without VeritySession, for one-off scripts.</P>
      <Code>
        <span className="c-flag">from</span> verity <span className="c-flag">import</span> load_registry, save_registry, validate, push, pull{'\n'}
        <span className="c-flag">from</span> pathlib <span className="c-flag">import</span> Path{'\n\n'}
        registry = load_registry(Path(<span className="c-str">"verity.json"</span>)){'\n'}
        errors = validate(registry){'\n\n'}
        <span className="c-comm"># push(registry, ...) → str blob ID</span>{'\n'}
        blob_id = push(registry, publisher_url=<span className="c-str">"https://…"</span>){'\n\n'}
        <span className="c-comm"># pull(blob_id, ...) → Registry object</span>{'\n'}
        restored = pull(blob_id, aggregator_url=<span className="c-str">"https://…"</span>)
      </Code>

      <H2>Custom backend</H2>
      <P>Any object with <InlineCode>store(bytes) → str</InlineCode> and <InlineCode>fetch(str) → bytes</InlineCode> works:</P>
      <Code>
        <span className="c-flag">from</span> verity.backends <span className="c-flag">import</span> StorageBackend{'\n\n'}
        <span className="c-flag">class</span> S3Backend:{'\n'}
        {'    '}<span className="c-flag">def</span> store(self, content: bytes) {'-> str:'}{'\n'}
        {'        '}key = upload_to_s3(content){'\n'}
        {'        '}<span className="c-flag">return</span> key{'\n\n'}
        {'    '}<span className="c-flag">def</span> fetch(self, key: str) {'-> bytes:'}{'\n'}
        {'        '}<span className="c-flag">return</span> download_from_s3(key){'\n\n'}
        v = VeritySession(<span className="c-str">"verity.json"</span>, backend=S3Backend())
      </Code>

      <H2>Error types</H2>
      <Table
        headers={['Exception', 'When']}
        rows={[
          ['VerityReleaseError', 'release() fails proof-chain guards'],
          ['VerityPushError', 'push() or pull() called with no backend'],
          ['WalrusError', 'Walrus HTTP call fails'],
          ['MemWalError', 'MemWal SDK call fails'],
        ]}
      />
    </div>
  )
}

function MemWalDoc() {
  return (
    <div>
      <div className="v-overline-accent" style={{ marginBottom: 12 }}>Backends</div>
      <h1 className="v-h1" style={{ margin: '0 0 16px' }}>MemWal</h1>
      <P>MemWal is a Walrus-backed memory layer for AI agents. verity uses it as a <em>discovery layer</em> on top of Walrus. Blobs live on Walrus directly; MemWal registers semantic pointers so agents can find them later.</P>

      <H2>Install</H2>
      <Code>pip install "walrus-verity[memwal]"</Code>

      <H2>Configure</H2>
      <P>Get a delegate key at memwal.ai, then set environment variables:</P>
      <Code>
        export MEMWAL_KEY=<span className="c-str">"&lt;ed25519-delegate-key-hex&gt;"</span>        <span className="c-comm"># required</span>{'\n'}
        export MEMWAL_ACCOUNT_ID=<span className="c-str">"&lt;your-account-id&gt;"</span>          <span className="c-comm"># required</span>{'\n'}
        export MEMWAL_SERVER_URL=<span className="c-str">"https://relayer.memwal.ai"</span>   <span className="c-comm"># default</span>{'\n'}
        export MEMWAL_NAMESPACE=<span className="c-str">"my-project"</span>                   <span className="c-comm"># default: verity</span>
      </Code>

      <H2>Use</H2>
      <Code>
        <span className="c-comm"># CLI</span>{'\n'}
        verity push <span className="c-flag">--backend</span> memwal{'\n'}
        verity pull BLOB_ID <span className="c-flag">--backend</span> memwal
      </Code>
      <Code>
        <span className="c-comm"># Python</span>{'\n'}
        <span className="c-flag">from</span> verity <span className="c-flag">import</span> VeritySession, MemWalBackend{'\n\n'}
        backend = MemWalBackend()  <span className="c-comm"># reads env vars</span>{'\n'}
        v = VeritySession(<span className="c-str">"verity.json"</span>, backend=backend){'\n'}
        blob_id = v.push()  <span className="c-comm"># uploads to Walrus + registers in MemWal</span>{'\n\n'}
        <span className="c-comm"># restore in another session (still needs the blob_id)</span>{'\n'}
        v2 = VeritySession(<span className="c-str">"restored.json"</span>, backend=backend){'\n'}
        v2.pull(blob_id)
      </Code>

      <H2>What push actually does</H2>
      <P>When you call <InlineCode>verity push --backend memwal</InlineCode>, two things happen:</P>
      <ol style={{ color: 'var(--muted-2)', paddingLeft: 20, lineHeight: 2, marginBottom: 24 }}>
        <li><strong style={{ color: 'var(--text-strong)' }}>Walrus upload:</strong> the registry is serialized to canonical JSON and stored on Walrus. This is the primary, permanent store.</li>
        <li><strong style={{ color: 'var(--text-strong)' }}>MemWal registration:</strong> a semantic pointer and any context entries are registered via <InlineCode>remember_and_wait()</InlineCode>. This is non-fatal: if the MemWal relayer is down, the blob is already safely on Walrus.</li>
      </ol>

      <P>The memories registered look like:</P>
      <Code>
        <span className="c-str">"verity registry blob_id=AbCdEfGh… repo=repo:my-agent"</span>{'\n'}
        <span className="c-str">"verity context key=architecture repo=repo:my-agent: 5-layer proof chain…"</span>
      </Code>

      <Callout>
        <strong>Recall is via the MemWal SDK, not verity.</strong> verity registers the memories on push. To query them later (e.g. "find the registry for repo:my-agent"), use the MemWal SDK's <InlineCode>recall()</InlineCode> to get the blob ID, then pass that blob ID to <InlineCode>verity pull</InlineCode>.
      </Callout>

      <H2>Why not encrypted storage?</H2>
      <P>MemWal encrypts with SEAL before writing to Walrus, so a direct Walrus fetch returns ciphertext. verity needs deterministic canonical JSON round-trips, so it keeps registries unencrypted on Walrus and uses MemWal only for the discovery layer.</P>
    </div>
  )
}

function MultiAgent() {
  return (
    <div>
      <div className="v-overline-accent" style={{ marginBottom: 12 }}>Patterns</div>
      <h1 className="v-h1" style={{ margin: '0 0 16px' }}>Multi-Agent Patterns</h1>
      <P>verity's core handoff is simple: Agent A builds a proof chain and pushes it to Walrus, gets back a blob ID, and passes that ID to Agent B by any channel. Agent B pulls, validates, and continues building.</P>

      <H2>The handoff pattern</H2>
      <Code>
        <span className="c-comm">Agent A                          Agent B</span>{'\n'}
        <span className="c-comm">  │                                  │</span>{'\n'}
        <span className="c-comm">  ├─ build proof chain               │</span>{'\n'}
        <span className="c-comm">  ├─ validate()                      │</span>{'\n'}
        <span className="c-comm">  ├─ release("0.1.0")                │</span>{'\n'}
        <span className="c-comm">  ├─ push() ── blob_id ────────────► │</span>{'\n'}
        <span className="c-comm">  │                                  ├─ pull(blob_id)</span>{'\n'}
        <span className="c-comm">  │                                  ├─ validate()</span>{'\n'}
        <span className="c-comm">  │                                  ├─ add_evidence(...)  ← extend</span>{'\n'}
        <span className="c-comm">  │                                  ├─ release("1.0.0")</span>{'\n'}
        <span className="c-comm">  │                                  └─ push() ──► new_blob_id</span>
      </Code>
      <P>The original blob ID is immutable. It always resolves to exactly what Agent A published. Agent B's push creates a new blob that extends the chain.</P>

      <H2>Code example</H2>
      <Code>
        <span className="c-flag">from</span> verity <span className="c-flag">import</span> VeritySession, WalrusBackend{'\n\n'}
        <span className="c-comm"># Agent A — researcher</span>{'\n'}
        a = VeritySession(<span className="c-str">"agent_a/verity.json"</span>, backend=WalrusBackend()){'\n'}
        a.init(repo_id=<span className="c-str">"repo:quality-check"</span>){'\n'}
        a.add_feature(<span className="c-str">"feat:supplier.quality"</span>, <span className="c-str">"Evaluate supplier quality"</span>){'\n'}
        a.add_claim(<span className="c-str">"clm:supplier.ok"</span>, <span className="c-str">"Supplier X meets threshold"</span>,{'\n'}
        {'           '}feature_id=<span className="c-str">"feat:supplier.quality"</span>, status=<span className="c-str">"verified"</span>){'\n'}
        a.add_test(<span className="c-str">"tst:supplier.eval"</span>, claim_id=<span className="c-str">"clm:supplier.ok"</span>,{'\n'}
        {'          '}path=<span className="c-str">"tests/test_supplier.py"</span>, status=<span className="c-str">"passing"</span>){'\n'}
        a.add_evidence(<span className="c-str">"evd:supplier.run1"</span>, test_id=<span className="c-str">"tst:supplier.eval"</span>,{'\n'}
        {'              '}artifact_path=<span className="c-str">"reports/eval.json"</span>, status=<span className="c-str">"passed"</span>){'\n'}
        a.release(<span className="c-str">"0.1.0"</span>){'\n'}
        blob_id = a.push(){'\n\n'}
        <span className="c-comm"># --- pass blob_id to Agent B via any channel ---</span>{'\n\n'}
        <span className="c-comm"># Agent B — auditor (different machine)</span>{'\n'}
        b = VeritySession(<span className="c-str">"agent_b/verity.json"</span>, backend=WalrusBackend()){'\n'}
        b.pull(blob_id){'\n'}
        b.validate()  <span className="c-comm"># confirm the restored chain is clean</span>{'\n\n'}
        b.add_evidence(<span className="c-str">"evd:supplier.audit"</span>, test_id=<span className="c-str">"tst:supplier.eval"</span>,{'\n'}
        {'              '}artifact_path=<span className="c-str">"audit/sign-off.json"</span>, status=<span className="c-str">"passed"</span>){'\n'}
        b.release(<span className="c-str">"1.0.0"</span>){'\n'}
        new_blob_id = b.push()
      </Code>

      <H2>Dry-run (no Walrus)</H2>
      <P>For testing agent logic locally, both agents share one in-memory store:</P>
      <Code>
        <span className="c-flag">class</span> _SharedStore:{'\n'}
        {'    '}<span className="c-flag">def</span> __init__(self) {'-> None:'} self._blobs: dict[str, bytes] = {'{}'}{'\n'}
        {'    '}<span className="c-flag">def</span> store(self, c: bytes) {'-> str:'}{'\n'}
        {'        '}key = f<span className="c-str">"blob-{'{'}len(self._blobs){'}'}"</span>; self._blobs[key] = c; <span className="c-flag">return</span> key{'\n'}
        {'    '}<span className="c-flag">def</span> fetch(self, key: str) {'-> bytes:'} <span className="c-flag">return</span> self._blobs[key]{'\n\n'}
        shared = _SharedStore(){'\n'}
        a = VeritySession(<span className="c-str">"agent_a/verity.json"</span>, backend=shared){'\n'}
        b = VeritySession(<span className="c-str">"agent_b/verity.json"</span>, backend=shared)
      </Code>

      <H2>Passing the blob ID</H2>
      <P>The blob ID is a plain string. Pass it however makes sense for your pipeline:</P>
      <Table
        headers={['Channel', 'Example']}
        rows={[
          ['Environment variable', 'os.environ["VERITY_BLOB_ID"] = blob_id'],
          ['Shared file', 'Path("handoff.txt").write_text(blob_id)'],
          ['GitHub issue / PR comment', 'Comment the blob ID on the task'],
          ['Message queue', 'Publish to Redis, Slack, etc.'],
        ]}
      />
    </div>
  )
}

// ── nav config ────────────────────────────────────────────────────────────────

const SECTIONS = [
  { id: 'quickstart', label: 'Quick Start', component: QuickStart },
  { id: 'cli',        label: 'CLI Reference', component: CliRef },
  { id: 'python',     label: 'Python API', component: PythonApi },
  { id: 'memwal',     label: 'MemWal', component: MemWalDoc },
  { id: 'multiagent', label: 'Multi-Agent', component: MultiAgent },
]

// ── Docs page ─────────────────────────────────────────────────────────────────

export function Docs({ onBack }: { onBack: () => void }) {
  const [active, setActive] = useState('quickstart')
  const [menuOpen, setMenuOpen] = useState(false)
  const Section = SECTIONS.find(s => s.id === active)?.component ?? QuickStart

  return (
    <div className="v-app" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* Top bar */}
      <header className="v-nav-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={onBack} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}>
            <VerityMark size={26} />
          </button>
          <button onClick={onBack} className="v-wordmark" style={{ fontSize: 18, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>verity</button>
          <span className="v-overline" style={{ marginLeft: 12, color: 'var(--muted)' }}>docs</span>
        </div>
        <nav style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div className="v-nav-text">
            <a href="https://github.com/vantage-ola/verity" className="v-overline" style={{ textDecoration: 'none' }}>GitHub</a>
            <a href="https://pypi.org/project/walrus-verity/" className="v-overline" style={{ textDecoration: 'none' }}>PyPI</a>
          </div>
          {/* mobile menu toggle */}
          <button
            className="v-docs-menu-btn"
            onClick={() => setMenuOpen(o => !o)}
            style={{ background: 'none', border: '1px solid var(--border)', cursor: 'pointer', padding: '6px 10px', color: 'var(--muted-2)' }}
          >
            <span className="v-mono" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)' }}>
              {menuOpen ? 'Close' : 'Menu'}
            </span>
          </button>
        </nav>
      </header>

      {/* Mobile nav drawer */}
      {menuOpen && (
        <div style={{ background: 'var(--surface)', borderBottom: '1px solid var(--border)', padding: '16px 20px' }}>
          {SECTIONS.map(s => (
            <button
              key={s.id}
              onClick={() => { setActive(s.id); setMenuOpen(false) }}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                background: 'none', border: 'none', cursor: 'pointer',
                padding: '10px 0', borderBottom: '1px solid var(--border)',
                fontFamily: 'var(--font-sans)', fontSize: 14,
                color: active === s.id ? 'var(--accent)' : 'var(--muted-2)',
                fontWeight: active === s.id ? 600 : 400,
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {/* Body */}
      <div style={{ display: 'flex', flex: 1 }}>

        {/* Sidebar */}
        <aside className="v-docs-sidebar">
          <div style={{ padding: '32px 24px' }}>
            <div className="v-overline" style={{ marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
              v0.1.5
            </div>
            {SECTIONS.map(s => (
              <button
                key={s.id}
                onClick={() => setActive(s.id)}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  background: active === s.id ? 'var(--accent-soft)' : 'none',
                  border: 'none',
                  borderLeft: `2px solid ${active === s.id ? 'var(--accent)' : 'transparent'}`,
                  cursor: 'pointer', padding: '8px 12px', marginBottom: 2,
                  fontFamily: 'var(--font-sans)', fontSize: 13,
                  color: active === s.id ? 'var(--accent)' : 'var(--muted-2)',
                  fontWeight: active === s.id ? 600 : 400,
                  transition: 'color .12s, background .12s',
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </aside>

        {/* Content */}
        <main style={{ flex: 1, padding: '40px 48px', maxWidth: 760, overflowX: 'hidden' }}>
          <Section />
        </main>

      </div>
    </div>
  )
}
