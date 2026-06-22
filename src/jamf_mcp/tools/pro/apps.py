"""Jamf Pro app management tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_post
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import ensure_list, err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_app_installers(
        page: int = 0,
        page_size: int = 50,
    ) -> dict:
        """List App Installers configured in Jamf Pro.

        App Installers automatically install and update apps on managed Macs.

        Args:
            page: Page number (0-indexed).
            page_size: Results per page (default 50).

        Returns:
            List of App Installer packages with name, version, and status.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get(
                "/api/v2/app-installers",
                cfg,
                params={"page": page, "page-size": page_size},
            )
            return ok(data, message="App installers retrieved")
        except Exception as exc:
            return err(f"Failed to get app installers: {exc}")

    @mcp.tool()
    async def jamf_get_app_installer_titles(
        search: str | None = None,
        page: int = 0,
        page_size: int = 50,
    ) -> dict:
        """Search the App Installer catalog for available app titles.

        Args:
            search: Optional name filter (partial match).
            page: Page number (0-indexed).
            page_size: Results per page (default 50).

        Returns:
            List of available app titles from the App Installer catalog.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            params: dict = {"page": page, "page-size": page_size}
            if search:
                params["filter"] = f"name==\"*{search}*\""
            data = await pro_get("/api/v2/app-installers/titles", cfg, params=params)
            return ok(data, message="App installer titles retrieved")
        except Exception as exc:
            return err(f"Failed to get app installer titles: {exc}")

    @mcp.tool()
    async def jamf_get_app_installer_deployments(
        page: int = 0,
        page_size: int = 50,
    ) -> dict:
        """List App Installer deployments configured in Jamf Pro.

        Args:
            page: Page number (0-indexed).
            page_size: Results per page (default 50).

        Returns:
            List of deployments with app name, version, scope, and install status.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get(
                "/api/v2/app-installers/deployments",
                cfg,
                params={"page": page, "page-size": page_size},
            )
            return ok(data, message="App installer deployments retrieved")
        except Exception as exc:
            return err(f"Failed to get app installer deployments: {exc}")

    @mcp.tool()
    async def jamf_create_app_installer_deployment(
        title_id: str,
        smart_group_ids: list[int],
        auto_update: bool = True,
        deploy_action: str = "INSTALL_AUTOMATICALLY",
    ) -> dict:
        """Create a new App Installer deployment to push an app to devices.

        Args:
            title_id: App Installer title ID (from jamf_get_app_installer_titles).
            smart_group_ids: List of smart group IDs to deploy to.
            auto_update: Automatically update when new version available (default True).
            deploy_action: One of: 'INSTALL_AUTOMATICALLY', 'INSTALL_PROMPTED',
                           'SELF_SERVICE'. Default is 'INSTALL_AUTOMATICALLY'.

        Returns:
            Created deployment ID and details.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            body = {
                "titleId": title_id,
                "enabled": True,
                "deploymentType": deploy_action,
                "autoUpdate": auto_update,
                "smartGroupIds": smart_group_ids,
            }
            data = await pro_post("/api/v2/app-installers/deployments", cfg, body)
            return ok(data, message="App installer deployment created")
        except Exception as exc:
            return err(f"Failed to create app installer deployment: {exc}")

    @mcp.tool()
    async def jamf_get_mac_apps(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List Mac App Store apps configured for distribution in Jamf Pro.

        Returns:
            List of Mac App Store app deployments.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/macapplications", cfg)
            apps = ensure_list(data.get("mac_applications", {}).get("mac_application", []))
            start = page * page_size
            return ok(
                {
                    "mac_apps": apps[start : start + page_size],
                    "total": len(apps),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(apps)} Mac apps",
            )
        except Exception as exc:
            return err(f"Failed to get Mac apps: {exc}")

    @mcp.tool()
    async def jamf_get_mobile_device_apps(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List iOS/iPadOS apps configured for distribution in Jamf Pro.

        Returns:
            List of mobile device app deployments.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/mobiledeviceapplications", cfg)
            apps = ensure_list(
                data.get("mobile_device_applications", {}).get("mobile_device_application", [])
            )
            start = page * page_size
            return ok(
                {
                    "mobile_apps": apps[start : start + page_size],
                    "total": len(apps),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(apps)} mobile device apps",
            )
        except Exception as exc:
            return err(f"Failed to get mobile device apps: {exc}")

    @mcp.tool()
    async def jamf_get_ebooks(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List eBooks configured for distribution in Jamf Pro.

        Returns:
            List of eBooks with ID, name, and deployment details.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/ebooks", cfg)
            ebooks = ensure_list(data.get("ebooks", {}).get("ebook", []))
            start = page * page_size
            return ok(
                {
                    "ebooks": ebooks[start : start + page_size],
                    "total": len(ebooks),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(ebooks)} eBooks",
            )
        except Exception as exc:
            return err(f"Failed to get eBooks: {exc}")
