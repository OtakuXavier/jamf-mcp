"""Jamf MCP Server — Claude Desktop MCP server for Jamf Pro, Protect, and Security Cloud."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp import __version__
from jamf_mcp.tools import setup
from jamf_mcp.tools.pro import api_mgmt, apps, computers, groups, mobile_devices, org, policies, printers, scripts, users
from jamf_mcp.tools.protect import alerts, computers as protect_computers
from jamf_mcp.tools.security import risk

mcp = FastMCP(
    "jamf-mcp",
    instructions=(
        "You are an expert Jamf administrator assistant. "
        "You can interact with Jamf Pro, Jamf Protect, and Jamf Security Cloud "
        "using the available tools. "
        "Always use jamf_get_setup_status first if unsure what's configured. "
        "When the user's request is ambiguous about device type (computer vs mobile device vs user), "
        "ask for clarification before calling any tool."
    ),
)

# Report the package version (__version__) in the MCP serverInfo. FastMCP does
# not expose a version parameter, so without this the low-level server falls
# back to the installed mcp SDK version.
mcp._mcp_server.version = __version__

# Register all tool modules
setup.register(mcp)

# Jamf Pro
computers.register(mcp)
mobile_devices.register(mcp)
users.register(mcp)
groups.register(mcp)
policies.register(mcp)
apps.register(mcp)
scripts.register(mcp)
org.register(mcp)
printers.register(mcp)
api_mgmt.register(mcp)

# Jamf Protect
alerts.register(mcp)
protect_computers.register(mcp)

# Jamf Security Cloud
risk.register(mcp)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
