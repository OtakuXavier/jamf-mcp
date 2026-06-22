"""Jamf Pro scripts and extension attributes tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_post, pro_post_xml
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import ensure_list, err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_scripts(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List scripts stored in Jamf Pro.

        Returns:
            List of scripts with ID, name, category, and info.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get(
                "/api/v1/scripts",
                cfg,
                params={"page": page, "page-size": page_size},
            )
            return ok(data, message="Scripts retrieved")
        except Exception as exc:
            return err(f"Failed to get scripts: {exc}")

    @mcp.tool()
    async def jamf_get_extension_attributes(
        device_type: str = "computer",
    ) -> dict:
        """List extension attributes defined in Jamf Pro.

        Extension attributes are custom inventory fields collected from devices.

        IMPORTANT: Ask user to clarify device_type if not specified.

        Args:
            device_type: One of: 'computer', 'mobile_device', 'user'.

        Returns:
            List of extension attributes with ID, name, data type, and input type.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            paths = {
                "computer": "/JSSResource/computerextensionattributes",
                "mobile_device": "/JSSResource/mobiledeviceextensionattributes",
                "user": "/JSSResource/userextensionattributes",
            }
            keys = {
                "computer": ("computer_extension_attributes", "computer_extension_attribute"),
                "mobile_device": ("mobile_device_extension_attributes", "mobile_device_extension_attribute"),
                "user": ("user_extension_attributes", "user_extension_attribute"),
            }
            if device_type not in paths:
                return err(f"Invalid device_type. Use: computer, mobile_device, user")

            data = await pro_get(paths[device_type], cfg)
            outer, inner = keys[device_type]
            attrs = ensure_list(data.get(outer, {}).get(inner, []))
            return ok({"extension_attributes": attrs, "total": len(attrs)},
                      message=f"Found {len(attrs)} extension attributes")
        except Exception as exc:
            return err(f"Failed to get extension attributes: {exc}")

    @mcp.tool()
    async def jamf_create_extension_attribute(
        name: str,
        device_type: str,
        description: str = "",
        data_type: str = "String",
        input_type: str = "Text Field",
        script: str | None = None,
        choices: list[str] | None = None,
    ) -> dict:
        """Create a new extension attribute in Jamf Pro.

        IMPORTANT: Ask user to clarify device_type if not specified.

        Args:
            name: Name for the extension attribute.
            device_type: One of: 'computer', 'mobile_device', 'user'.
            description: Optional description.
            data_type: Data type: 'String', 'Integer', 'Date'.
            input_type: Input type: 'Text Field', 'Pop-up Menu', 'Script'.
                        Use 'Script' when providing a script.
            script: Shell script content (for Script input type, computer only).
            choices: List of choices (for Pop-up Menu input type).

        Returns:
            Created extension attribute ID.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            paths = {
                "computer": "/JSSResource/computerextensionattributes/id/0",
                "mobile_device": "/JSSResource/mobiledeviceextensionattributes/id/0",
                "user": "/JSSResource/userextensionattributes/id/0",
            }
            tags = {
                "computer": "computer_extension_attribute",
                "mobile_device": "mobile_device_extension_attribute",
                "user": "user_extension_attribute",
            }
            if device_type not in paths:
                return err(f"Invalid device_type. Use: computer, mobile_device, user")

            input_xml = f"<input_type><type>{input_type}</type>"
            if script and input_type == "Script":
                import html
                input_xml += f"<script>{html.escape(script)}</script>"
            if choices and input_type == "Pop-up Menu":
                choice_items = "".join(f"<choice>{c}</choice>" for c in choices)
                input_xml += f"<choices>{choice_items}</choices>"
            input_xml += "</input_type>"

            tag = tags[device_type]
            xml_body = (
                f"<{tag}>"
                f"<name>{name}</name>"
                f"<description>{description}</description>"
                f"<data_type>{data_type}</data_type>"
                f"{input_xml}"
                f"</{tag}>"
            )

            result = await pro_post_xml(paths[device_type], cfg, xml_body)
            created_id = result.get(tag, {}).get("id")
            return ok({"id": created_id, "name": name}, message=f"Extension attribute '{name}' created")
        except Exception as exc:
            return err(f"Failed to create extension attribute: {exc}")
