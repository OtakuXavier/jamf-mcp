"""Jamf Pro computer management tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_put
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_computer(
        identifier: str,
        detail: bool = True,
    ) -> dict:
        """Get details about a specific Mac computer managed by Jamf Pro.

        Args:
            identifier: Computer ID (numeric), serial number, MAC address, or name.
            detail: If True (default), returns full inventory details. If False, returns summary only.

        Returns:
            Computer record with hardware info, OS, enrolled date, groups, policies,
            certificates, applications, and more.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            # Try as numeric ID first, then fall back to search
            try:
                int(identifier)
                path = f"/JSSResource/computers/id/{identifier}"
            except ValueError:
                # Try serial number
                path = f"/JSSResource/computers/serialnumber/{identifier}"

            data = await pro_get(path, cfg)
            computer = data.get("computer", data)

            if not detail:
                # Return just the general subset
                general = computer.get("general", computer)
                return ok(general)

            return ok(computer)
        except Exception as exc:
            # Try by name if serial lookup failed
            try:
                search = await pro_get(
                    "/JSSResource/computers/match/" + identifier.replace(" ", "%20"), cfg
                )
                computers = search.get("computers", {}).get("computer", [])
                if isinstance(computers, dict):
                    computers = [computers]
                if computers:
                    first = computers[0]
                    cid = first.get("id")
                    data = await pro_get(f"/JSSResource/computers/id/{cid}", cfg)
                    return ok(data.get("computer", data))
                return err(f"Computer not found: {identifier}")
            except Exception as exc2:
                return err(f"Failed to get computer: {exc2}")

    @mcp.tool()
    async def jamf_update_computer(
        computer_id: str,
        asset_tag: str | None = None,
        department: str | None = None,
        building: str | None = None,
        room: str | None = None,
        username: str | None = None,
        real_name: str | None = None,
        email: str | None = None,
        position: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Update user and location information for a managed Mac computer.

        Only the fields you provide will be updated; omitted fields are left unchanged.

        Args:
            computer_id: Numeric Jamf Pro computer ID.
            asset_tag: Asset tag / property number.
            department: Department name (must exist in Jamf Pro).
            building: Building name (must exist in Jamf Pro).
            room: Room number or name.
            username: Username of the computer's primary user.
            real_name: Full name of the primary user.
            email: Email address of the primary user.
            position: Job position/title of the primary user.
            phone: Phone number of the primary user.
            notes: Notes about the computer.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            location_parts = []
            if username is not None:
                location_parts.append(f"<username>{username}</username>")
            if real_name is not None:
                location_parts.append(f"<real_name>{real_name}</real_name>")
            if email is not None:
                location_parts.append(f"<email_address>{email}</email_address>")
            if position is not None:
                location_parts.append(f"<position>{position}</position>")
            if phone is not None:
                location_parts.append(f"<phone>{phone}</phone>")
            if department is not None:
                location_parts.append(f"<department>{department}</department>")
            if building is not None:
                location_parts.append(f"<building>{building}</building>")
            if room is not None:
                location_parts.append(f"<room>{room}</room>")

            general_parts = []
            if asset_tag is not None:
                general_parts.append(f"<asset_tag>{asset_tag}</asset_tag>")
            if notes is not None:
                general_parts.append(f"<notes>{notes}</notes>")

            sections = []
            if location_parts:
                sections.append(f"<location>{''.join(location_parts)}</location>")
            if general_parts:
                sections.append(f"<general>{''.join(general_parts)}</general>")

            if not sections:
                return err("No fields provided to update")

            xml_body = f"<computer>{''.join(sections)}</computer>"

            from jamf_mcp.api.pro import pro_put_xml
            await pro_put_xml(f"/JSSResource/computers/id/{computer_id}", cfg, xml_body)
            return ok({"computer_id": computer_id}, message="Computer updated successfully")
        except Exception as exc:
            return err(f"Failed to update computer: {exc}")
