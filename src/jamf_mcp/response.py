from typing import Any


def ok(data: Any = None, message: str = "Success") -> dict:
    return {"success": True, "message": message, "data": data}


def err(message: str, data: Any = None) -> dict:
    return {"success": False, "message": message, "data": data}


def not_configured(product: str) -> dict:
    return {
        "success": False,
        "message": (
            f"{product} is not configured. "
            "Use the jamf_configure_help tool for setup instructions."
        ),
        "data": None,
    }


def ensure_list(value: Any) -> list:
    """Normalize None / single item / list to always return a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
