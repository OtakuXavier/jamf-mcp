"""Always-available setup and status tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.config import JamfProConfig, JamfProtectConfig, JamfSecurityConfig
from jamf_mcp.response import ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def jamf_get_setup_status() -> dict:
        """Get the configuration status for all Jamf products.

        Shows which products are configured and ready, which environment variables
        are missing, and how many tools are available for each product. Use this
        tool to understand what's configured and what needs setup.

        This tool always works, even when no credentials are configured.

        Returns:
            JSON containing configuration status for each product:
            - jamf_pro: Core device management status
            - jamf_protect: Endpoint security status
            - jamf_security_cloud: Risk management status
            - summary: Overall counts and status
        """
        pro = JamfProConfig.from_env()
        protect = JamfProtectConfig.from_env()
        security = JamfSecurityConfig.from_env()

        products = {
            "jamf_pro": {
                "configured": pro.configured,
                "url": pro.url or None,
                "auth_method": "oauth" if pro.uses_oauth else ("basic" if pro.configured else None),
                "missing_vars": pro.missing_vars(),
                "available_tools": 37 if pro.configured else 0,
                "description": "Device management for macOS, iOS/iPadOS, tvOS",
            },
            "jamf_protect": {
                "configured": protect.configured,
                "url": protect.url or None,
                "missing_vars": protect.missing_vars(),
                "available_tools": 6 if protect.configured else 0,
                "description": "Endpoint security and threat detection",
            },
            "jamf_security_cloud": {
                "configured": security.configured,
                "region": security.region if security.configured else None,
                "missing_vars": security.missing_vars(),
                "available_tools": 2 if security.configured else 0,
                "description": "Device risk management (RISK API)",
            },
        }

        configured_count = sum(1 for p in products.values() if p["configured"])
        total_tools = sum(p["available_tools"] for p in products.values())
        # setup tools are always available
        total_tools += 2

        return ok(
            {
                **products,
                "summary": {
                    "products_configured": configured_count,
                    "total_products": 3,
                    "total_tools_available": total_tools,
                    "setup_complete": configured_count == 3,
                },
            },
            message=f"{configured_count}/3 products configured, {total_tools} tools available",
        )

    @mcp.tool()
    def jamf_configure_help(product: str = "all") -> dict:
        """Get step-by-step setup instructions for Jamf products.

        This tool always works, even when no credentials are configured.

        Args:
            product: Which product to get help for. One of: 'all', 'jamf_pro',
                     'jamf_protect', 'jamf_security_cloud'. Defaults to 'all'.

        Returns:
            Step-by-step instructions and required environment variables.
        """
        instructions = {
            "jamf_pro": {
                "description": "Jamf Pro — Device management for macOS, iOS/iPadOS, tvOS",
                "required_env_vars": {
                    "JAMF_PRO_URL": "Your Jamf Pro server URL (e.g. https://yourorg.jamfcloud.com)",
                    "JAMF_CLIENT_ID": "OAuth client ID (recommended)",
                    "JAMF_CLIENT_SECRET": "OAuth client secret (recommended)",
                },
                "alternative_auth": {
                    "JAMF_USERNAME": "Jamf Pro admin username (Basic auth)",
                    "JAMF_PASSWORD": "Jamf Pro admin password (Basic auth)",
                },
                "setup_steps": [
                    "1. Log in to your Jamf Pro server",
                    "2. Go to Settings > System > API Roles and Clients",
                    "3. Create an API Role with the privileges you need",
                    "4. Create an API Client, assign the role, and enable it",
                    "5. Copy the Client ID and generate a Client Secret",
                    "6. Set JAMF_PRO_URL, JAMF_CLIENT_ID, JAMF_CLIENT_SECRET in your environment",
                ],
                "docs": "https://developer.jamf.com/jamf-pro/docs/jamf-pro-api-overview",
            },
            "jamf_protect": {
                "description": "Jamf Protect — Endpoint security and threat detection",
                "required_env_vars": {
                    "JAMF_PROTECT_URL": "Your Jamf Protect tenant URL (e.g. https://yourorg.protect.jamfcloud.com)",
                    "JAMF_PROTECT_CLIENT_ID": "Jamf Protect API client ID",
                    "JAMF_PROTECT_PASSWORD": "Jamf Protect API client secret/password",
                },
                "setup_steps": [
                    "1. Log in to Jamf Protect",
                    "2. Go to Settings > API Clients",
                    "3. Create a new API client and copy the credentials",
                    "4. Set JAMF_PROTECT_URL, JAMF_PROTECT_CLIENT_ID, JAMF_PROTECT_PASSWORD",
                ],
                "docs": "https://learn.jamf.com/r/en-US/jamf-protect-documentation/Jamf_Protect_API",
            },
            "jamf_security_cloud": {
                "description": "Jamf Security Cloud — Device risk management (RISK API)",
                "required_env_vars": {
                    "JAMF_SECURITY_CLIENT_ID": "Jamf Security Cloud API client ID",
                    "JAMF_SECURITY_CLIENT_SECRET": "Jamf Security Cloud API client secret",
                    "JAMF_SECURITY_REGION": "Region: 'us' (default) or 'eu'",
                },
                "setup_steps": [
                    "1. Log in to Jamf Security Cloud",
                    "2. Go to Settings > Integrations > API Clients",
                    "3. Create a new API client with RISK API access",
                    "4. Set JAMF_SECURITY_CLIENT_ID, JAMF_SECURITY_CLIENT_SECRET",
                    "5. Optionally set JAMF_SECURITY_REGION=eu if your tenant is in Europe",
                ],
                "docs": "https://developer.jamf.com/jamf-security/docs/risk-api-2",
            },
        }

        if product == "all":
            data = instructions
        elif product in instructions:
            data = {product: instructions[product]}
        else:
            data = instructions

        return ok(data, message="Setup instructions retrieved")
