# jamf-mcp

A Claude Desktop MCP (Model Context Protocol) server that gives Claude a natural-language interface to **Jamf Pro**, **Jamf Protect**, and **Jamf Security Cloud**.

Ask Claude things like:
- *"Show me all Macs running macOS 13 or older"*
- *"Update the department for serial number C02XL0THJGH7 to Engineering"*
- *"List all high-severity Jamf Protect alerts from the last 24 hours"*
- *"Create a smart group for all devices with a CRITICAL risk score"*
- *"What API roles do we have configured?"*

## Features

| Product | Tools | Capabilities |
|---|---|---|
| **Jamf Pro** | 37 | Computers, mobile devices, users, smart/static groups, policies, configuration profiles, patch policies, App Installers, scripts, extension attributes, categories, departments, buildings, printers, prestages, API roles & integrations |
| **Jamf Protect** | 6 | Security alerts, analytics (detection rules), enrolled computers |
| **Jamf Security Cloud** | 2 | Device risk levels, risk overrides |
| **Setup** | 2 | Configuration status, setup instructions |

Zero credentials required to start — tools for unconfigured products return setup guidance instead of errors.

## Requirements

- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Python 3.11+
- [Claude Desktop](https://claude.ai/download)

## Installation

```bash
git clone https://github.com/OtakuXavier/jamf-mcp.git
cd jamf-mcp
uv sync
```

## Configuration

### 1. Set up credentials

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
# Jamf Pro — OAuth (recommended)
JAMF_PRO_URL=https://yourorg.jamfcloud.com
JAMF_CLIENT_ID=your-client-id
JAMF_CLIENT_SECRET=your-client-secret

# Jamf Protect
JAMF_PROTECT_URL=https://yourorg.protect.jamfcloud.com
JAMF_PROTECT_CLIENT_ID=your-protect-client-id
JAMF_PROTECT_PASSWORD=your-protect-client-secret

# Jamf Security Cloud
JAMF_SECURITY_CLIENT_ID=your-security-client-id
JAMF_SECURITY_CLIENT_SECRET=your-security-client-secret
JAMF_SECURITY_REGION=us
```

You only need to configure the products you use — the others will be skipped gracefully.

### 2. Add to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (see `claude_desktop_config.example.json` for the full template):

```json
{
  "mcpServers": {
    "jamf": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/jamf-mcp", "jamf-mcp"],
      "env": {
        "JAMF_PRO_URL": "https://yourorg.jamfcloud.com",
        "JAMF_CLIENT_ID": "your-client-id",
        "JAMF_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

Restart Claude Desktop. You should see the Jamf tools available in the tool menu.

## Getting Jamf Pro API Credentials

1. Log in to Jamf Pro → **Settings → System → API Roles and Clients**
2. Create an **API Role** with the privileges you need (e.g., *Read Computers*, *Update Computers*)
3. Create an **API Client**, assign the role, enable it
4. Copy the **Client ID** and generate a **Client Secret**

Or ask Claude to do it for you once you have admin credentials: *"Create an API client with read-only access to computers and mobile devices"*

## Authentication

**Jamf Pro** supports two auth methods:
- **OAuth2** (recommended): Set `JAMF_CLIENT_ID` + `JAMF_CLIENT_SECRET`
- **Basic auth** fallback: Set `JAMF_USERNAME` + `JAMF_PASSWORD`

All three API clients cache bearer tokens in memory and refresh automatically 60 seconds before expiry.

## Architecture

```
src/jamf_mcp/
├── server.py           # FastMCP server, registers all tools
├── config.py           # Env-var config dataclasses
├── response.py         # Shared ok() / err() / not_configured() helpers
├── api/
│   ├── pro.py          # Jamf Pro HTTP client (XML + JSON, token cache)
│   ├── protect.py      # Jamf Protect GraphQL client
│   └── security.py     # Jamf Security Cloud REST client
└── tools/
    ├── setup.py        # jamf_get_setup_status, jamf_configure_help
    ├── pro/            # 37 Jamf Pro tools across 8 modules
    ├── protect/        # 6 Jamf Protect tools
    └── security/       # 2 Jamf Security Cloud tools
```

All tools return a consistent envelope:
```json
{ "success": true, "message": "Found 42 computers", "data": { ... } }
```

## API Documentation

- [Jamf Pro API](https://developer.jamf.com/jamf-pro/docs/jamf-pro-api-overview)
- [Jamf Protect API](https://learn.jamf.com/r/en-US/jamf-protect-documentation/Jamf_Protect_API)
- [Jamf Security Cloud RISK API](https://developer.jamf.com/jamf-security/docs/risk-api-2)

## License

MIT
