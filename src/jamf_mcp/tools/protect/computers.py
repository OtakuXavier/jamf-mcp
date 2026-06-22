"""Jamf Protect enrolled computer tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.protect import protect_query
from jamf_mcp.config import JamfProtectConfig
from jamf_mcp.response import err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_protect_list_computers(
        limit: int = 50,
        after: str | None = None,
        os_version: str | None = None,
    ) -> dict:
        """List computers enrolled in Jamf Protect.

        Args:
            limit: Maximum results to return (default 50).
            after: Pagination cursor from previous response.
            os_version: Filter by OS version (partial match, e.g., '14.').

        Returns:
            List of enrolled computers with hostname, serial number, OS version,
            Protect version, and last check-in time.
        """
        cfg = JamfProtectConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Protect")
        try:
            cursor_arg = f'after: "{after}", ' if after else ""
            filter_arg = f'filter: {{ osVersion: {{ contains: "{os_version}" }} }}, ' if os_version else ""
            query = f"""
            query ListComputers {{
                listComputers(input: {{ {cursor_arg}{filter_arg}first: {limit} }}) {{
                    items {{
                        id
                        hostName
                        serialNumber
                        osVersion
                        protectVersion
                        lastCheckin
                        primaryUsername
                        hasMDM
                    }}
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                }}
            }}
            """
            data = await protect_query(query, {}, cfg)
            result = data.get("listComputers", {})
            items = result.get("items", [])
            page_info = result.get("pageInfo", {})
            return ok(
                {
                    "computers": items,
                    "total": len(items),
                    "has_next_page": page_info.get("hasNextPage", False),
                    "next_cursor": page_info.get("endCursor"),
                },
                message=f"Found {len(items)} computers in Jamf Protect",
            )
        except Exception as exc:
            return err(f"Failed to list Protect computers: {exc}")

    @mcp.tool()
    async def jamf_protect_get_computer(identifier: str) -> dict:
        """Get details about a specific computer enrolled in Jamf Protect.

        Args:
            identifier: Computer ID, hostname, or serial number.

        Returns:
            Computer details including Protect version, last check-in, OS version,
            open alerts count, and enrolled plan.
        """
        cfg = JamfProtectConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Protect")
        try:
            # Try as direct ID first
            query_by_id = """
            query GetComputer($id: ID!) {
                getComputer(input: {id: $id}) {
                    id
                    hostName
                    serialNumber
                    osVersion
                    protectVersion
                    lastCheckin
                    primaryUsername
                    hasMDM
                }
            }
            """
            try:
                data = await protect_query(query_by_id, {"id": identifier}, cfg)
                if data.get("getComputer"):
                    return ok(data["getComputer"], message="Computer retrieved")
            except Exception:
                pass

            # Fall back to listing and searching by hostname/serial
            query_list = f"""
            query FindComputer {{
                listComputers(input: {{
                    filter: {{ hostName: {{ eq: "{identifier}" }} }}
                    first: 1
                }}) {{
                    items {{
                        id
                        hostName
                        serialNumber
                        osVersion
                        protectVersion
                        lastCheckin
                        primaryUsername
                        hasMDM
                    }}
                }}
            }}
            """
            data = await protect_query(query_list, {}, cfg)
            items = data.get("listComputers", {}).get("items", [])
            if items:
                return ok(items[0], message="Computer retrieved")
            return err(f"Computer not found in Jamf Protect: {identifier}")
        except Exception as exc:
            return err(f"Failed to get Protect computer: {exc}")
