# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Claude Desktop MCP (Model Context Protocol) server providing a natural-language interface for three Jamf products:

- **Jamf Pro** — macOS/iOS/tvOS device management
- **Jamf Protect** — endpoint security and threat detection
- **Jamf Security Cloud** — device risk management (RISK API)

## Commands

```bash
# Install dependencies
uv sync

# Run the server (stdio, for Claude Desktop)
uv run jamf-mcp

# Run with environment file
uv run --env-file .env jamf-mcp

# Install in development mode
uv pip install -e .

# Test a tool directly (set env vars first)
python -c "
import asyncio, os
os.environ['JAMF_PRO_URL'] = 'https://yourorg.jamfcloud.com'
# ... set other vars
from jamf_mcp.tools.setup import register
from mcp.server.fastmcp import FastMCP
mcp = FastMCP('test')
register(mcp)
"
```

## API Documentation

- Jamf Pro: https://developer.jamf.com/jamf-pro/docs/jamf-pro-api-overview
- Jamf Protect: https://learn.jamf.com/r/en-US/jamf-protect-documentation/Jamf_Protect_API
- Jamf Security Cloud RISK API: https://developer.jamf.com/jamf-security/docs/risk-api-2

## Architecture

```
src/jamf_mcp/
├── server.py          # FastMCP server factory — registers all tools
├── config.py          # Env-var-backed config dataclasses (one per product)
├── response.py        # ok()/err()/not_configured() helpers + ensure_list()
├── api/
│   ├── pro.py         # Jamf Pro client — OAuth2/Basic, XML+JSON, token cache
│   ├── protect.py     # Jamf Protect GraphQL client + token cache
│   └── security.py    # Jamf Security Cloud REST client + token cache
└── tools/
    ├── setup.py       # jamf_get_setup_status, jamf_configure_help (always on)
    ├── pro/           # 37 Jamf Pro tools
    └── protect/       # 6 Jamf Protect tools
    └── security/      # 2 Jamf Security Cloud tools
```

### Tool Registration

`server.py` creates the `FastMCP` instance and calls `register(mcp)` from each tool module. Each tool module exports a single `register(mcp: FastMCP) -> None` function that decorates its tools with `@mcp.tool()`.

### API Layer

- **Jamf Pro** (`api/pro.py`): Supports OAuth2 client credentials (`/api/oauth/token`) and Basic auth (`/api/v1/auth/token`). Classic API endpoints (`/JSSResource/`) return XML, parsed via `xml_to_dict()`. Modern API endpoints (`/api/v1/`, `/api/v2/`) return JSON.
- **Jamf Protect** (`api/protect.py`): GraphQL at `/graphql`, OAuth2 via `/oauth/v2/token`.
- **Jamf Security Cloud** (`api/security.py`): REST via `api.wandera.com` (US) or `api.eu.wandera.com` (EU), OAuth2 via `auth.wandera.com`.

All three clients cache bearer tokens in module-level dicts (keyed by URL), refreshing 60 seconds before expiry.

### Response Format

All tools return `{"success": bool, "message": str, "data": any}`. Use the helpers:
- `ok(data, message="Success")` — successful result
- `err(message)` — error result
- `not_configured(product)` — product not set up (points user to `jamf_configure_help`)

### Tool Naming

- `jamf_<verb>_<noun>` — Jamf Pro
- `jamf_protect_<verb>_<noun>` — Jamf Protect
- `jamf_get_risk_devices` / `jamf_override_device_risk` — Jamf Security Cloud

### Clarification Rule

When the user's request is ambiguous about device type (computer vs. mobile device vs. user), ask for clarification before calling any tool. This applies to: extension attributes, smart/static groups, and prestage enrollments.

## Env Vars

| Variable | Product | Required |
|---|---|---|
| `JAMF_PRO_URL` | Pro | Yes |
| `JAMF_CLIENT_ID` | Pro | OAuth auth |
| `JAMF_CLIENT_SECRET` | Pro | OAuth auth |
| `JAMF_USERNAME` | Pro | Basic auth alternative |
| `JAMF_PASSWORD` | Pro | Basic auth alternative |
| `JAMF_PROTECT_URL` | Protect | Yes |
| `JAMF_PROTECT_CLIENT_ID` | Protect | Yes |
| `JAMF_PROTECT_PASSWORD` | Protect | Yes |
| `JAMF_SECURITY_CLIENT_ID` | Security Cloud | Yes |
| `JAMF_SECURITY_CLIENT_SECRET` | Security Cloud | Yes |
| `JAMF_SECURITY_REGION` | Security Cloud | Optional (`us`/`eu`) |
