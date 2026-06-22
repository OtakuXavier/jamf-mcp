"""Jamf Pro smart and static group tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_post_xml
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import ensure_list, err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_smart_groups(
        device_type: str = "computer",
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List all smart groups in Jamf Pro.

        Smart groups use criteria to dynamically include devices or users.

        Args:
            device_type: Type of smart group. One of: 'computer', 'mobile_device', 'user'.
                         Ask user to clarify if not specified.
            page: Page number (0-indexed).
            page_size: Results per page (default 100, max 200).

        Returns:
            List of smart groups with ID, name, and member count.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            paths = {
                "computer": "/JSSResource/computergroups",
                "mobile_device": "/JSSResource/mobiledevicegroups",
                "user": "/JSSResource/usergroups",
            }
            if device_type not in paths:
                return err(f"Invalid device_type '{device_type}'. Use: computer, mobile_device, user")

            data = await pro_get(paths[device_type], cfg)
            key_map = {
                "computer": ("computer_groups", "computer_group"),
                "mobile_device": ("mobile_device_groups", "mobile_device_group"),
                "user": ("user_groups", "user_group"),
            }
            outer, inner = key_map[device_type]
            all_groups = ensure_list(data.get(outer, {}).get(inner, []))
            # Filter to smart groups only
            smart = [g for g in all_groups if str(g.get("is_smart", "false")).lower() == "true"]

            start = page * page_size
            end = start + page_size
            return ok(
                {
                    "smart_groups": smart[start:end],
                    "total": len(smart),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(smart)} smart groups",
            )
        except Exception as exc:
            return err(f"Failed to get smart groups: {exc}")

    @mcp.tool()
    async def jamf_get_static_groups(
        device_type: str = "computer",
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List all static groups in Jamf Pro.

        Static groups have manually assigned members.

        Args:
            device_type: Type of static group. One of: 'computer', 'mobile_device', 'user'.
                         Ask user to clarify if not specified.
            page: Page number (0-indexed).
            page_size: Results per page (default 100, max 200).

        Returns:
            List of static groups with ID, name, and member count.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            paths = {
                "computer": "/JSSResource/computergroups",
                "mobile_device": "/JSSResource/mobiledevicegroups",
                "user": "/JSSResource/usergroups",
            }
            if device_type not in paths:
                return err(f"Invalid device_type '{device_type}'. Use: computer, mobile_device, user")

            data = await pro_get(paths[device_type], cfg)
            key_map = {
                "computer": ("computer_groups", "computer_group"),
                "mobile_device": ("mobile_device_groups", "mobile_device_group"),
                "user": ("user_groups", "user_group"),
            }
            outer, inner = key_map[device_type]
            all_groups = ensure_list(data.get(outer, {}).get(inner, []))
            static = [g for g in all_groups if str(g.get("is_smart", "true")).lower() != "true"]

            start = page * page_size
            end = start + page_size
            return ok(
                {
                    "static_groups": static[start:end],
                    "total": len(static),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(static)} static groups",
            )
        except Exception as exc:
            return err(f"Failed to get static groups: {exc}")

    @mcp.tool()
    async def jamf_create_smart_group(
        name: str,
        device_type: str,
        criteria: list[dict],
        site_id: int = -1,
    ) -> dict:
        """Create a new smart group in Jamf Pro.

        IMPORTANT: Ask user to clarify device_type if not specified.

        Args:
            name: Name for the new smart group.
            device_type: One of: 'computer', 'mobile_device', 'user'.
            criteria: List of criteria dicts. Each dict requires:
                - name: Criterion name (e.g., 'Operating System', 'Department')
                - priority: Integer priority (0 = highest)
                - and_or: 'and' or 'or' (how this joins with next criterion)
                - search_type: Operator (e.g., 'is', 'is not', 'like', 'greater than')
                - value: The value to match against
            site_id: Jamf Pro site ID (-1 for no site / all sites).

        Returns:
            The created group's ID.

        Example criteria:
            [{"name": "Operating System", "priority": 0, "and_or": "and",
              "search_type": "like", "value": "14."}]
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            paths = {
                "computer": "/JSSResource/computergroups/id/0",
                "mobile_device": "/JSSResource/mobiledevicegroups/id/0",
                "user": "/JSSResource/usergroups/id/0",
            }
            tags = {
                "computer": "computer_group",
                "mobile_device": "mobile_device_group",
                "user": "user_group",
            }
            if device_type not in paths:
                return err(f"Invalid device_type '{device_type}'. Use: computer, mobile_device, user")

            criteria_xml = ""
            for i, c in enumerate(criteria):
                criteria_xml += (
                    f"<criterion>"
                    f"<name>{c.get('name', '')}</name>"
                    f"<priority>{c.get('priority', i)}</priority>"
                    f"<and_or>{c.get('and_or', 'and')}</and_or>"
                    f"<search_type>{c.get('search_type', 'is')}</search_type>"
                    f"<value>{c.get('value', '')}</value>"
                    f"</criterion>"
                )

            tag = tags[device_type]
            xml_body = (
                f"<{tag}>"
                f"<name>{name}</name>"
                f"<is_smart>true</is_smart>"
                f"<site><id>{site_id}</id></site>"
                f"<criteria>{criteria_xml}</criteria>"
                f"</{tag}>"
            )

            result = await pro_post_xml(paths[device_type], cfg, xml_body)
            created_id = result.get(tag, {}).get("id")
            return ok({"id": created_id, "name": name}, message=f"Smart group '{name}' created")
        except Exception as exc:
            return err(f"Failed to create smart group: {exc}")

    @mcp.tool()
    async def jamf_create_static_group(
        name: str,
        device_type: str,
        device_ids: list[int] | None = None,
        site_id: int = -1,
    ) -> dict:
        """Create a new static group in Jamf Pro.

        IMPORTANT: Ask user to clarify device_type if not specified.

        Args:
            name: Name for the new static group.
            device_type: One of: 'computer', 'mobile_device', 'user'.
            device_ids: Optional list of device/user IDs to add as initial members.
            site_id: Jamf Pro site ID (-1 for no site / all sites).

        Returns:
            The created group's ID.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            paths = {
                "computer": "/JSSResource/computergroups/id/0",
                "mobile_device": "/JSSResource/mobiledevicegroups/id/0",
                "user": "/JSSResource/usergroups/id/0",
            }
            tags = {
                "computer": "computer_group",
                "mobile_device": "mobile_device_group",
                "user": "user_group",
            }
            member_tags = {
                "computer": ("computers", "computer"),
                "mobile_device": ("mobile_devices", "mobile_device"),
                "user": ("users", "user"),
            }
            if device_type not in paths:
                return err(f"Invalid device_type '{device_type}'. Use: computer, mobile_device, user")

            members_xml = ""
            if device_ids:
                outer, inner = member_tags[device_type]
                member_items = "".join(f"<{inner}><id>{mid}</id></{inner}>" for mid in device_ids)
                members_xml = f"<{outer}>{member_items}</{outer}>"

            tag = tags[device_type]
            xml_body = (
                f"<{tag}>"
                f"<name>{name}</name>"
                f"<is_smart>false</is_smart>"
                f"<site><id>{site_id}</id></site>"
                f"{members_xml}"
                f"</{tag}>"
            )

            result = await pro_post_xml(paths[device_type], cfg, xml_body)
            created_id = result.get(tag, {}).get("id")
            return ok({"id": created_id, "name": name}, message=f"Static group '{name}' created")
        except Exception as exc:
            return err(f"Failed to create static group: {exc}")
