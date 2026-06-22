"""Jamf Pro printer management tools."""
from mcp.server.fastmcp import FastMCP

from jamf_mcp.api.pro import pro_get, pro_post_xml, pro_put_xml
from jamf_mcp.config import JamfProConfig
from jamf_mcp.response import ensure_list, err, not_configured, ok


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def jamf_get_printers(
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        """List printers configured in Jamf Pro.

        Returns:
            List of printers with ID, name, URI, and location.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            data = await pro_get("/JSSResource/printers", cfg)
            printers = ensure_list(data.get("printers", {}).get("printer", []))
            start = page * page_size
            return ok(
                {
                    "printers": printers[start : start + page_size],
                    "total": len(printers),
                    "page": page,
                    "page_size": page_size,
                },
                message=f"Found {len(printers)} printers",
            )
        except Exception as exc:
            return err(f"Failed to get printers: {exc}")

    @mcp.tool()
    async def jamf_create_printer(
        name: str,
        uri: str,
        ppd_name: str = "",
        ppd_path: str = "",
        location: str = "",
        model: str = "",
        info: str = "",
        notes: str = "",
        make_default: bool = False,
        use_generic: bool = False,
        cups_name: str = "",
    ) -> dict:
        """Add a new printer to Jamf Pro.

        Args:
            name: Display name for the printer.
            uri: Printer URI (e.g., ipp://printer.local, lpd://10.0.0.5).
            ppd_name: PPD file name (e.g., 'HP LaserJet 4').
            ppd_path: Path to the PPD file on client (e.g., '/Library/Printers/PPDs/...').
            location: Physical location of the printer.
            model: Printer model string.
            info: Additional info.
            notes: Admin notes.
            make_default: Make this the default printer when deployed.
            use_generic: Use generic PPD instead of model-specific.
            cups_name: CUPS printer name (used in policy deployment).

        Returns:
            Created printer ID.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            xml_body = (
                f"<printer>"
                f"<name>{name}</name>"
                f"<uri>{uri}</uri>"
                f"<ppd_name>{ppd_name}</ppd_name>"
                f"<ppd_path>{ppd_path}</ppd_path>"
                f"<location>{location}</location>"
                f"<model>{model}</model>"
                f"<info>{info}</info>"
                f"<notes>{notes}</notes>"
                f"<make_default>{str(make_default).lower()}</make_default>"
                f"<use_generic>{str(use_generic).lower()}</use_generic>"
                f"<cups_name>{cups_name}</cups_name>"
                f"</printer>"
            )
            result = await pro_post_xml("/JSSResource/printers/id/0", cfg, xml_body)
            created_id = result.get("printer", {}).get("id")
            return ok({"id": created_id, "name": name}, message=f"Printer '{name}' created")
        except Exception as exc:
            return err(f"Failed to create printer: {exc}")

    @mcp.tool()
    async def jamf_update_printer(
        printer_id: str,
        name: str | None = None,
        uri: str | None = None,
        location: str | None = None,
        notes: str | None = None,
        make_default: bool | None = None,
    ) -> dict:
        """Update an existing printer in Jamf Pro.

        Only provided fields are updated.

        Args:
            printer_id: Numeric Jamf Pro printer ID.
            name: New display name.
            uri: New printer URI.
            location: New physical location.
            notes: Admin notes.
            make_default: Whether to make this the default printer.
        """
        cfg = JamfProConfig.from_env()
        if not cfg.configured:
            return not_configured("Jamf Pro")
        try:
            parts = []
            if name is not None:
                parts.append(f"<name>{name}</name>")
            if uri is not None:
                parts.append(f"<uri>{uri}</uri>")
            if location is not None:
                parts.append(f"<location>{location}</location>")
            if notes is not None:
                parts.append(f"<notes>{notes}</notes>")
            if make_default is not None:
                parts.append(f"<make_default>{str(make_default).lower()}</make_default>")

            if not parts:
                return err("No fields provided to update")

            xml_body = f"<printer>{''.join(parts)}</printer>"
            await pro_put_xml(f"/JSSResource/printers/id/{printer_id}", cfg, xml_body)
            return ok({"printer_id": printer_id}, message="Printer updated successfully")
        except Exception as exc:
            return err(f"Failed to update printer: {exc}")
