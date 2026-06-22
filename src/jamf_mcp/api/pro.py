"""Jamf Pro API client with OAuth2/Basic auth and token caching."""
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from jamf_mcp.config import JamfProConfig

# module-level token cache: url -> {token, expires_at}
_token_cache: dict[str, dict] = {}


def _xml_node_to_dict(node: ET.Element) -> Any:
    """Recursively convert an XML element to a dict/str."""
    children = list(node)
    if not children:
        return node.text or ""
    result: dict[str, Any] = {}
    for child in children:
        value = _xml_node_to_dict(child)
        if child.tag in result:
            existing = result[child.tag]
            if not isinstance(existing, list):
                result[child.tag] = [existing]
            result[child.tag].append(value)
        else:
            result[child.tag] = value
    return result


def xml_to_dict(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    return {root.tag: _xml_node_to_dict(root)}


async def _get_token(cfg: JamfProConfig) -> str:
    cached = _token_cache.get(cfg.url)
    if cached and cached["expires_at"] > time.time() + 60:
        return cached["token"]

    async with httpx.AsyncClient() as client:
        if cfg.uses_oauth:
            resp = await client.post(
                f"{cfg.url}/api/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": cfg.client_id,
                    "client_secret": cfg.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            resp.raise_for_status()
            body = resp.json()
            token = body["access_token"]
            expires_at = time.time() + body.get("expires_in", 1800)
        else:
            import base64
            creds = base64.b64encode(f"{cfg.username}:{cfg.password}".encode()).decode()
            resp = await client.post(
                f"{cfg.url}/api/v1/auth/token",
                headers={"Authorization": f"Basic {creds}"},
                timeout=30,
            )
            resp.raise_for_status()
            body = resp.json()
            token = body["token"]
            # Jamf Basic token expiry is returned as an ISO timestamp; default 30 min
            expires_at = time.time() + 1800

    _token_cache[cfg.url] = {"token": token, "expires_at": expires_at}
    return token


async def pro_get(path: str, cfg: JamfProConfig, params: dict | None = None) -> Any:
    """GET a Jamf Pro API endpoint. Handles both Classic XML and modern JSON APIs."""
    token = await _get_token(cfg)
    is_classic = path.startswith("/JSSResource")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/xml" if is_classic else "application/json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{cfg.url}{path}",
            headers=headers,
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        if is_classic:
            return xml_to_dict(resp.text)
        return resp.json()


async def pro_post(path: str, cfg: JamfProConfig, body: dict) -> Any:
    token = await _get_token(cfg)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{cfg.url}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return {}


async def pro_put(path: str, cfg: JamfProConfig, body: dict) -> Any:
    token = await _get_token(cfg)
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{cfg.url}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return {}


async def pro_post_xml(path: str, cfg: JamfProConfig, xml_body: str) -> Any:
    """POST to Classic API with XML body."""
    token = await _get_token(cfg)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{cfg.url}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/xml",
                "Accept": "application/xml",
            },
            content=xml_body.encode(),
            timeout=30,
        )
        resp.raise_for_status()
        if resp.content:
            return xml_to_dict(resp.text)
        return {}


async def pro_put_xml(path: str, cfg: JamfProConfig, xml_body: str) -> Any:
    """PUT to Classic API with XML body."""
    token = await _get_token(cfg)
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{cfg.url}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/xml",
                "Accept": "application/xml",
            },
            content=xml_body.encode(),
            timeout=30,
        )
        resp.raise_for_status()
        if resp.content:
            return xml_to_dict(resp.text)
        return {}
