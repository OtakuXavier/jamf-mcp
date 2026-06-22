"""Jamf Pro mobile device management tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_put_xml
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_mobile_device(
        identifier: str,
    ) -> dict:
        """Get details about a specific mobile device (iPhone, iPad, Apple TV) managed by Jamf Pro.

        Args:
            identifier: Device ID (numeric), serial number, UDID, or name.

        Returns:
            Device record with hardware info, OS version, enrolled date, groups,
            installed apps, certificates, and more.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            try:
                int(identifier)
                path = f"/JSSResource/mobiledevices/id/{identifier}"
            except ValueError:
                path = f"/JSSResource/mobiledevices/serialnumber/{identifier}"

            data = await pro_get(path, cfg)
            return ok(data.get("mobile_device", data))
        except Exception:
            try:
                search = await pro_get(
                    "/JSSResource/mobiledevices/match/" + identifier.replace(" ", "%20"), cfg
                )
                devices = search.get("mobile_devices", {}).get("mobile_device", [])
                if isinstance(devices, dict):
                    devices = [devices]
                if devices:
                    did = devices[0].get("id")
                    data = await pro_get(f"/JSSResource/mobiledevices/id/{did}", cfg)
                    return ok(data.get("mobile_device", data))
                return err(f"Mobile device not found: {identifier}")
            except Exception as exc2:
                return err(f"Failed to get mobile device: {exc2}")

    @mcp.tool()
    async def jamf_update_mobile_device(
        device_id: str,
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
        """Update user and location information for a managed mobile device.

        Only the fields you provide will be updated.

        Args:
            device_id: Numeric Jamf Pro mobile device ID.
            asset_tag: Asset tag / property number.
            department: Department name (must exist in Jamf Pro).
            building: Building name (must exist in Jamf Pro).
            room: Room number or name.
            username: Username of the device's primary user.
            real_name: Full name of the primary user.
            email: Email address of the primary user.
            position: Job position/title of the primary user.
            phone: Phone number of the primary user.
            notes: Notes about the device.
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

            xml_body = f"<mobile_device>{''.join(sections)}</mobile_device>"
            await pro_put_xml(f"/JSSResource/mobiledevices/id/{device_id}", cfg, xml_body)
            return ok({"device_id": device_id}, message="Mobile device updated successfully")
        except Exception as exc:
            return err(f"Failed to update mobile device: {exc}")
