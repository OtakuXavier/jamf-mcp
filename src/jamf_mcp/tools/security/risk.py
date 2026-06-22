"""Jamf Security Cloud RISK API tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.security import security_get, security_put
from jamf_mcp.config import JamfSecurityConfig
from jamf_mcp.response import err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_risk_devices(
        page: int = 0,
        page_size: int = 100,
        risk_level: str | None = None,
    ) -> dict:
        """List devices and their risk levels from Jamf Security Cloud.

        Args:
            page: Page number (0-indexed).
            page_size: Results per page (default 100).
            risk_level: Filter by risk level. One of: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.

        Returns:
            List of devices with risk scores, risk factors, and override status.
        """
        cfg = JamfSecurityConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Security Cloud")
        try:
            params: dict = {
                "pageNumber": page,
                "pageSize": page_size,
            }
            if risk_level:
                params["riskLevel"] = risk_level

            data = await security_get("/v1/devices/risk", cfg, params=params)
            devices = data.get("devices", data.get("content", data))
            total = data.get("totalElements", len(devices) if isinstance(devices, list) else 0)
            return ok(
                {
                    "devices": devices,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Retrieved device risk data",
            )
        except Exception as exc:
            return err(f"Failed to get risk devices: {exc}")

    @mcp.tool()
    async def jamf_override_device_risk(
        device_id: str,
        risk_level: str,
        reason: str,
        duration_days: int | None = None,
    ) -> dict:
        """Override the risk level for a specific device in Jamf Security Cloud.

        Use this to manually set a device's risk level when the automated assessment
        needs to be overridden (e.g., known false positive, device under investigation).

        Args:
            device_id: The device's unique identifier in Jamf Security Cloud.
            risk_level: Override risk level. One of: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.
            reason: Required justification for the override (audit trail).
            duration_days: Number of days the override should last. If None, override
                           is permanent until manually removed.

        Returns:
            Confirmation of the override with expiry date if duration was set.
        """
        cfg = JamfSecurityConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Security Cloud")
        try:
            body: dict = {
                "riskLevel": risk_level,
                "reason": reason,
            }
            if duration_days is not None:
                body["durationDays"] = duration_days

            data = await security_put(f"/v1/devices/{device_id}/risk/override", cfg, body)
            return ok(data, message=f"Risk override applied: device {device_id} → {risk_level}")
        except Exception as exc:
            return err(f"Failed to override device risk: {exc}")
