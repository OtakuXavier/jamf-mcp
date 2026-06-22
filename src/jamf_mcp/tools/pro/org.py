"""Jamf Pro org structure tools: categories, departments, buildings."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_post_xml
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import ensure_list, err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_categories(
        page: int = 0,
        page_size: int = 200,
    ) -> dict:
        """List all categories defined in Jamf Pro.

        Categories are used to organize policies, scripts, apps, and profiles.

        Returns:
            List of categories with ID and name.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/categories", cfg)
            categories = ensure_list(data.get("categories", {}).get("category", []))
            start = page * page_size
            return ok(
                {
                    "categories": categories[start : start + page_size],
                    "total": len(categories),
                },
                message=f"Found {len(categories)} categories",
            )
        except Exception as exc:
            return err(f"Failed to get categories: {exc}")

    @mcp.tool()
    async def jamf_create_category(
        name: str,
        priority: int = 9,
    ) -> dict:
        """Create a new category in Jamf Pro.

        Args:
            name: Category name.
            priority: Priority for Self Service display (1 = highest, 9 = default).

        Returns:
            Created category ID.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            xml_body = f"<category><name>{name}</name><priority>{priority}</priority></category>"
            result = await pro_post_xml("/JSSResource/categories/id/0", cfg, xml_body)
            created_id = result.get("category", {}).get("id")
            return ok({"id": created_id, "name": name}, message=f"Category '{name}' created")
        except Exception as exc:
            return err(f"Failed to create category: {exc}")

    @mcp.tool()
    async def jamf_get_departments(
        page: int = 0,
        page_size: int = 200,
    ) -> dict:
        """List all departments defined in Jamf Pro.

        Returns:
            List of departments with ID and name.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/departments", cfg)
            departments = ensure_list(data.get("departments", {}).get("department", []))
            start = page * page_size
            return ok(
                {
                    "departments": departments[start : start + page_size],
                    "total": len(departments),
                },
                message=f"Found {len(departments)} departments",
            )
        except Exception as exc:
            return err(f"Failed to get departments: {exc}")

    @mcp.tool()
    async def jamf_get_buildings(
        page: int = 0,
        page_size: int = 200,
    ) -> dict:
        """List all buildings defined in Jamf Pro.

        Returns:
            List of buildings with ID and name.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/buildings", cfg)
            buildings = ensure_list(data.get("buildings", {}).get("building", []))
            start = page * page_size
            return ok(
                {
                    "buildings": buildings[start : start + page_size],
                    "total": len(buildings),
                },
                message=f"Found {len(buildings)} buildings",
            )
        except Exception as exc:
            return err(f"Failed to get buildings: {exc}")

    @mcp.tool()
    async def jamf_get_prestages(
        device_type: str = "computer",
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List enrollment prestages in Jamf Pro.

        Prestages define the enrollment experience for new devices.

        IMPORTANT: Ask user to clarify device_type if not specified.

        Args:
            device_type: One of: 'computer', 'mobile_device'.
            page: Page number (0-indexed).
            page_size: Results per page (default 100).

        Returns:
            List of prestages with ID, name, and enrollment settings.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            paths = {
                "computer": "/api/v2/computer-prestages",
                "mobile_device": "/api/v2/mobile-device-prestages",
            }
            if device_type not in paths:
                return err(f"Invalid device_type. Use: computer, mobile_device")

            data = await pro_get(paths[device_type], cfg, params={"page": page, "page-size": page_size})
            return ok(data, message="Prestages retrieved")
        except Exception as exc:
            return err(f"Failed to get prestages: {exc}")
