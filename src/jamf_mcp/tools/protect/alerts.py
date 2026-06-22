"""Jamf Protect alert and analytic tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.protect import protect_query
from jamf_mcp.config import JamfProtectConfig
from jamf_mcp.response import err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_protect_list_alerts(
        limit: int = 50,
        severity: str | None = None,
        status: str | None = None,
        after: str | None = None,
    ) -> dict:
        """List security alerts from Jamf Protect.

        Args:
            limit: Maximum number of alerts to return (default 50, max 200).
            severity: Filter by severity. One of: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.
            status: Filter by status. One of: 'OPEN', 'IN_PROGRESS', 'CLOSED'.
            after: Cursor for pagination (from previous response's nextCursor field).

        Returns:
            List of security alerts with ID, severity, description, device info,
            and timestamps. Includes nextCursor for pagination.
        """
        cfg = JamfProtectConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Protect")
        try:
            filters = []
            if severity:
                filters.append(f'severity: {{value: {severity}}}')
            if status:
                filters.append(f'status: {{value: {status}}}')

            filter_arg = (", ".join(filters) + ", ") if filters else ""
            cursor_arg = f'after: "{after}", ' if after else ""

            query = f"""
            query ListAlerts {{
                listAlerts(
                    input: {{
                        {cursor_arg}
                        first: {limit}
                        {filter_arg}
                    }}
                ) {{
                    items {{
                        id
                        severity
                        status
                        description
                        created
                        updated
                        computer {{
                            hostName
                            serialNumber
                        }}
                    }}
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                }}
            }}
            """
            data = await protect_query(query, {}, cfg)
            result = data.get("listAlerts", {})
            items = result.get("items", [])
            page_info = result.get("pageInfo", {})
            return ok(
                {
                    "alerts": items,
                    "total": len(items),
                    "has_next_page": page_info.get("hasNextPage", False),
                    "next_cursor": page_info.get("endCursor"),
                },
                message=f"Found {len(items)} alerts",
            )
        except Exception as exc:
            return err(f"Failed to list alerts: {exc}")

    @mcp.tool()
    async def jamf_protect_get_alert(alert_id: str) -> dict:
        """Get detailed information about a specific Jamf Protect alert.

        Args:
            alert_id: The unique alert ID.

        Returns:
            Full alert details including event data, affected files, network connections,
            process tree, and remediation steps.
        """
        cfg = JamfProtectConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Protect")
        try:
            query = """
            query GetAlert($id: ID!) {
                getAlert(input: {id: $id}) {
                    id
                    severity
                    status
                    description
                    created
                    updated
                    tags
                    computer {
                        hostName
                        serialNumber
                        osVersion
                        primaryUsername
                    }
                    event {
                        ... on AlertEventGPURegistryRead {
                            __typename
                        }
                    }
                    facts {
                        human
                    }
                    actions {
                        parameters {
                            ... on ActionParametersBundleId {
                                bundleId
                            }
                        }
                    }
                }
            }
            """
            data = await protect_query(query, {"id": alert_id}, cfg)
            return ok(data.get("getAlert"), message="Alert retrieved")
        except Exception as exc:
            return err(f"Failed to get alert: {exc}")

    @mcp.tool()
    async def jamf_protect_list_analytics(
        limit: int = 50,
        after: str | None = None,
    ) -> dict:
        """List analytics (behavioral detection rules) in Jamf Protect.

        Args:
            limit: Maximum results to return (default 50).
            after: Pagination cursor from previous response.

        Returns:
            List of analytics with ID, name, description, and enabled status.
        """
        cfg = JamfProtectConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Protect")
        try:
            cursor_arg = f'after: "{after}", ' if after else ""
            query = f"""
            query ListAnalytics {{
                listAnalytics(input: {{ {cursor_arg} first: {limit} }}) {{
                    items {{
                        id
                        name
                        description
                        enabled
                        created
                        updated
                    }}
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                }}
            }}
            """
            data = await protect_query(query, {}, cfg)
            result = data.get("listAnalytics", {})
            items = result.get("items", [])
            page_info = result.get("pageInfo", {})
            return ok(
                {
                    "analytics": items,
                    "total": len(items),
                    "has_next_page": page_info.get("hasNextPage", False),
                    "next_cursor": page_info.get("endCursor"),
                },
                message=f"Found {len(items)} analytics",
            )
        except Exception as exc:
            return err(f"Failed to list analytics: {exc}")

    @mcp.tool()
    async def jamf_protect_get_analytic(analytic_id: str) -> dict:
        """Get details about a specific Jamf Protect analytic (detection rule).

        Args:
            analytic_id: The unique analytic ID.

        Returns:
            Full analytic details including predicates, actions, and event types.
        """
        cfg = JamfProtectConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Protect")
        try:
            query = """
            query GetAnalytic($id: ID!) {
                getAnalytic(input: {id: $id}) {
                    id
                    name
                    description
                    enabled
                    created
                    updated
                    tags
                    actions {
                        type
                    }
                }
            }
            """
            data = await protect_query(query, {"id": analytic_id}, cfg)
            return ok(data.get("getAnalytic"), message="Analytic retrieved")
        except Exception as exc:
            return err(f"Failed to get analytic: {exc}")
