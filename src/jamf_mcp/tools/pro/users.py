"""Jamf Pro user management tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_put_xml
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_user(
        identifier: str,
    ) -> dict:
        """Get details about a user in Jamf Pro.

        Args:
            identifier: User ID (numeric), username, or email address.

        Returns:
            User record including name, email, assigned devices, and groups.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            try:
                int(identifier)
                path = f"/JSSResource/users/id/{identifier}"
            except ValueError:
                if "@" in identifier:
                    path = f"/JSSResource/users/email/{identifier}"
                else:
                    path = f"/JSSResource/users/name/{identifier}"

            data = await pro_get(path, cfg)
            return ok(data.get("user", data))
        except Exception as exc:
            return err(f"Failed to get user: {exc}")

    @mcp.tool()
    async def jamf_update_user(
        user_id: str,
        full_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        position: str | None = None,
        department: str | None = None,
        building: str | None = None,
        room: str | None = None,
    ) -> dict:
        """Update information for a user in Jamf Pro.

        Only provided fields are updated.

        Args:
            user_id: Numeric Jamf Pro user ID.
            full_name: User's full name.
            email: Email address.
            phone: Phone number.
            position: Job title / position.
            department: Department name.
            building: Building name.
            room: Room.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            parts = []
            if full_name is not None:
                parts.append(f"<full_name>{full_name}</full_name>")
            if email is not None:
                parts.append(f"<email>{email}</email>")
            if phone is not None:
                parts.append(f"<phone_number>{phone}</phone_number>")
            if position is not None:
                parts.append(f"<position>{position}</position>")
            if department is not None:
                parts.append(f"<department>{department}</department>")
            if building is not None:
                parts.append(f"<building>{building}</building>")
            if room is not None:
                parts.append(f"<room>{room}</room>")

            if not parts:
                return err("No fields provided to update")

            xml_body = f"<user>{''.join(parts)}</user>"
            await pro_put_xml(f"/JSSResource/users/id/{user_id}", cfg, xml_body)
            return ok({"user_id": user_id}, message="User updated successfully")
        except Exception as exc:
            return err(f"Failed to update user: {exc}")
