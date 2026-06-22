"""Jamf Security Cloud RISK API client."""
import time

import httpx

from jamf_mcp.config import JamfSecurityConfig

_token_cache: dict[str, dict] = {}


async def _get_token(cfg: JamfSecurityConfig) -> str:
    cached = _token_cache.get(cfg.client_id)
    if cached and cached["expires_at"] > time.time() + 60:
        return cached["token"]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{cfg.auth_base}/oauth/token",
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
        expires_at = time.time() + body.get("expires_in", 3600)

    _token_cache[cfg.client_id] = {"token": token, "expires_at": expires_at}
    return token


async def security_get(path: str, cfg: JamfSecurityConfig, params: dict | None = None) -> dict:
    token = await _get_token(cfg)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{cfg.api_base}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


async def security_put(path: str, cfg: JamfSecurityConfig, body: dict) -> dict:
    token = await _get_token(cfg)
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{cfg.api_base}{path}",
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
