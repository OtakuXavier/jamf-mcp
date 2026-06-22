"""Jamf Protect GraphQL API client."""
import time

import httpx

from jamf_mcp.config import JamfProtectConfig

_token_cache: dict[str, dict] = {}


async def _get_token(cfg: JamfProtectConfig) -> str:
    cached = _token_cache.get(cfg.url)
    if cached and cached["expires_at"] > time.time() + 60:
        return cached["token"]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{cfg.url}/oauth/v2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": cfg.client_id,
                "client_secret": cfg.password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        token = body["access_token"]
        expires_at = time.time() + body.get("expires_in", 3600)

    _token_cache[cfg.url] = {"token": token, "expires_at": expires_at}
    return token


async def protect_query(query: str, variables: dict, cfg: JamfProtectConfig) -> dict:
    """Execute a GraphQL query against Jamf Protect."""
    token = await _get_token(cfg)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{cfg.url}/graphql",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"query": query, "variables": variables},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise RuntimeError(f"GraphQL errors: {result['errors']}")
        return result.get("data", {})
