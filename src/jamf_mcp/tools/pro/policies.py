"""Jamf Pro policies and configuration profiles tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import ensure_list, err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_policies(
        page: int = 0,
        page_size: int = 100,
        category: str | None = None,
    ) -> dict:
        """List Jamf Pro policies (computer policies only).

        Args:
            page: Page number (0-indexed).
            page_size: Results per page (default 100).
            category: Filter by category name (optional).

        Returns:
            List of policies with ID, name, and category.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            if category:
                data = await pro_get(
                    f"/JSSResource/policies/category/{category.replace(' ', '%20')}", cfg
                )
            else:
                data = await pro_get("/JSSResource/policies", cfg)

            policies = ensure_list(data.get("policies", {}).get("policy", []))
            start = page * page_size
            return ok(
                {
                    "policies": policies[start : start + page_size],
                    "total": len(policies),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(policies)} policies",
            )
        except Exception as exc:
            return err(f"Failed to get policies: {exc}")

    @mcp.tool()
    async def jamf_get_computer_configuration_profiles(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List configuration profiles deployed to Mac computers.

        Args:
            page: Page number (0-indexed).
            page_size: Results per page (default 100).

        Returns:
            List of configuration profiles with ID, name, description, and scope.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/osxconfigurationprofiles", cfg)
            profiles = ensure_list(
                data.get("os_x_configuration_profiles", {}).get("os_x_configuration_profile", [])
            )
            start = page * page_size
            return ok(
                {
                    "profiles": profiles[start : start + page_size],
                    "total": len(profiles),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(profiles)} computer configuration profiles",
            )
        except Exception as exc:
            return err(f"Failed to get computer configuration profiles: {exc}")

    @mcp.tool()
    async def jamf_get_mobile_device_configuration_profiles(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List configuration profiles deployed to mobile devices (iPhone, iPad, Apple TV).

        Args:
            page: Page number (0-indexed).
            page_size: Results per page (default 100).

        Returns:
            List of configuration profiles with ID, name, and description.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/mobiledeviceconfigurationprofiles", cfg)
            profiles = ensure_list(
                data.get("configuration_profiles", {}).get("configuration_profile", [])
            )
            start = page * page_size
            return ok(
                {
                    "profiles": profiles[start : start + page_size],
                    "total": len(profiles),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(profiles)} mobile device configuration profiles",
            )
        except Exception as exc:
            return err(f"Failed to get mobile device configuration profiles: {exc}")

    @mcp.tool()
    async def jamf_get_patch_policies(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List patch management policies in Jamf Pro.

        Returns:
            List of patch policies with ID, name, software title, and version.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/api/v2/patch-policies", cfg, params={"page": page, "page-size": page_size})
            return ok(data, message=f"Found patch policies")
        except Exception as exc:
            return err(f"Failed to get patch policies: {exc}")

    @mcp.tool()
    async def jamf_get_restricted_software(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List restricted software entries in Jamf Pro.

        Restricted software entries block specified applications from running.

        Returns:
            List of restricted software with ID, name, and process name.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/restrictedsoftware", cfg)
            items = ensure_list(
                data.get("restricted_software", {}).get("restricted_software_title", [])
            )
            start = page * page_size
            return ok(
                {
                    "restricted_software": items[start : start + page_size],
                    "total": len(items),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(items)} restricted software entries",
            )
        except Exception as exc:
            return err(f"Failed to get restricted software: {exc}")
