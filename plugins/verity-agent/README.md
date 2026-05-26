# verity-agent

MCP server for the [verity](https://github.com/vantage-ola/verity) proof-chain registry. Exposes verity tools to any MCP-compatible AI editor (Claude Code, Cursor, Windsurf, Codex).

## Install

```bash
pip install verity-agent
```

Or from source:

```bash
cd plugins/verity-agent
pip install -e .
```

## Tools

| Tool | Description |
|------|-------------|
| `verity_init` | Initialise a new `verity.json` registry |
| `verity_add_feature` | Add a Feature (`feat:` prefix) |
| `verity_add_claim` | Add a Claim (`clm:` prefix) |
| `verity_add_test` | Add a Test (`tst:` prefix) |
| `verity_add_evidence` | Add Evidence (`evd:` prefix) |
| `verity_set_status` | Promote an entity's status after the chain is wired |
| `verity_validate` | Validate the full chain |
| `verity_release` | Create a fail-closed release |
| `verity_push` | Push to Walrus, returns `blob_id` |
| `verity_pull` | Pull a registry from Walrus by `blob_id` |
| `verity_log` | Show push history |
| `verity_status` | Summary of entity counts and validation state |

## Build order

Always build the chain bottom-up with neutral statuses, then promote:

1. `verity_add_feature` → `verity_add_claim` → `verity_add_test` → `verity_add_evidence`
2. Wire complete — promote: `verity_set_status(evd_id, "passed")`, `verity_set_status(tst_id, "passing")`, `verity_set_status(clm_id, "verified")`
3. `verity_validate` → `verity_release` → `verity_push`

Never set `verified`/`passing` before downstream entities exist — validation will reject it.

## Configure with Claude Code

Add to your `claude_mcp_config.json` (or `~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "verity": {
      "command": "verity-mcp",
      "env": {
        "WALRUS_PUBLISHER_URL": "https://publisher.walrus-testnet.walrus.space",
        "WALRUS_AGGREGATOR_URL": "https://aggregator.walrus-testnet.walrus.space"
      }
    }
  }
}
```

Or with `uvx` (no install needed):

```json
{
  "mcpServers": {
    "verity": {
      "command": "uvx",
      "args": ["verity-agent"],
      "env": {
        "WALRUS_PUBLISHER_URL": "https://publisher.walrus-testnet.walrus.space",
        "WALRUS_AGGREGATOR_URL": "https://aggregator.walrus-testnet.walrus.space"
      }
    }
  }
}
```

## Configure with Cursor

Add to `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "verity": {
      "command": "verity-mcp"
    }
  }
}
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WALRUS_PUBLISHER_URL` | testnet | Walrus publisher endpoint |
| `WALRUS_AGGREGATOR_URL` | testnet | Walrus aggregator endpoint |

Push/pull tools are no-ops without `WALRUS_PUBLISHER_URL` set.
