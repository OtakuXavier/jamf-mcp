"""Jamf Pro API roles and integrations management tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_post
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_api_roles(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List API roles defined in Jamf Pro.

        API roles define sets of privileges that can be assigned to API integrations.

        Returns:
            List of API roles with ID, name, and privilege count.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get(
                "/api/v1/api-roles",
                cfg,
                params={"page": page, "page-size": page_size},
            )
            return ok(data, message="API roles retrieved")
        except Exception as exc:
            return err(f"Failed to get API roles: {exc}")

    @mcp.tool()
    async def jamf_get_api_role_privileges() -> dict:
        """List all available API privileges that can be assigned to API roles.

        Returns:
            Complete list of privilege names that can be used when creating API roles.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/api/v1/api-role-privileges", cfg)
            return ok(data, message="API role privileges retrieved")
        except Exception as exc:
            return err(f"Failed to get API role privileges: {exc}")

    @mcp.tool()
    async def jamf_create_api_role(
        display_name: str,
        privileges: list[str],
    ) -> dict:
        """Create a new API role in Jamf Pro.

        Args:
            display_name: Human-readable name for the role.
            privileges: List of privilege names to grant. Use jamf_get_api_role_privileges
                        to see available privilege names.

        Returns:
            Created API role ID and details.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_post(
                "/api/v1/api-roles",
                cfg,
                {"displayName": display_name, "privileges": privileges},
            )
            return ok(data, message=f"API role '{display_name}' created")
        except Exception as exc:
            return err(f"Failed to create API role: {exc}")

    @mcp.tool()
    async def jamf_get_api_integrations(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List API integrations (OAuth clients) in Jamf Pro.

        Returns:
            List of API integrations with ID, name, enabled status, and assigned roles.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get(
                "/api/v1/api-integrations",
                cfg,
                params={"page": page, "page-size": page_size},
            )
            return ok(data, message="API integrations retrieved")
        except Exception as exc:
            return err(f"Failed to get API integrations: {exc}")

    @mcp.tool()
    async def jamf_create_api_integration(
        display_name: str,
        api_role_ids: list[int],
        enabled: bool = True,
        access_token_lifetime_seconds: int = 1800,
    ) -> dict:
        """Create a new API integration (OAuth client) in Jamf Pro.

        After creation, use jamf_create_api_client_credentials to generate a client secret.

        Args:
            display_name: Human-readable name for the integration.
            api_role_ids: List of API role IDs to assign (from jamf_get_api_roles).
            enabled: Whether the integration is active (default True).
            access_token_lifetime_seconds: Token lifetime in seconds (default 1800 = 30 min).

        Returns:
            Created integration ID and details.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_post(
                "/api/v1/api-integrations",
                cfg,
                {
                    "displayName": display_name,
                    "enabled": enabled,
                    "accessTokenLifetimeSeconds": access_token_lifetime_seconds,
                    "apiRoleIds": api_role_ids,
                },
            )
            return ok(data, message=f"API integration '{display_name}' created")
        except Exception as exc:
            return err(f"Failed to create API integration: {exc}")

    @mcp.tool()
    async def jamf_create_api_client_credentials(
        integration_id: int,
    ) -> dict:
        """Generate client credentials (client ID and secret) for a Jamf Pro API integration.

        WARNING: The client secret is only shown once. Save it securely immediately.

        Args:
            integration_id: Numeric ID of the API integration.

        Returns:
            client_id and client_secret for use with OAuth2 client_credentials flow.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_post(
                f"/api/v1/api-integrations/{integration_id}/client-credentials",
                cfg,
                {},
            )
            return ok(
                data,
                message="Client credentials generated. Save the client_secret now — it cannot be retrieved again.",
            )
        except Exception as exc:
            return err(f"Failed to create client credentials: {exc}")

    @mcp.tool()
    async def jamf_create_computer_update_api_client(
        display_name: str = "Computer Update Client",
    ) -> dict:
        """Convenience tool: create a Jamf Pro API role and integration pre-configured
        with the minimum privileges needed to update computer records.

        Creates:
        1. An API role with 'Update Computers' and 'Read Computers' privileges
        2. An API integration using that role
        3. Client credentials for the integration

        Args:
            display_name: Base name for the role and integration (default: 'Computer Update Client').

        Returns:
            client_id and client_secret ready to use.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            role = await pro_post(
                "/api/v1/api-roles",
                cfg,
                {
                    "displayName": f"{display_name} Role",
                    "privileges": ["Read Computers", "Update Computers"],
                },
            )
            role_id = role.get("id")

            integration = await pro_post(
                "/api/v1/api-integrations",
                cfg,
                {
                    "displayName": display_name,
                    "enabled": True,
                    "accessTokenLifetimeSeconds": 1800,
                    "apiRoleIds": [role_id],
                },
            )
            integration_id = integration.get("id")

            creds = await pro_post(
                f"/api/v1/api-integrations/{integration_id}/client-credentials",
                cfg,
                {},
            )
            return ok(
                {
                    "role_id": role_id,
                    "integration_id": integration_id,
                    **creds,
                },
                message="Computer update API client created. Save the client_secret now.",
            )
        except Exception as exc:
            return err(f"Failed to create computer update API client: {exc}")
