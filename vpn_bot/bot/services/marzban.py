"""Minimal async Marzban REST API client.

Docs: https://github.com/Gozargah/Marzban — endpoints used:
  POST /api/admin/token        -> auth
  POST /api/user               -> create user
  GET  /api/user/{username}    -> fetch (traffic sync, subscription_url)
  PUT  /api/user/{username}    -> modify (extend expiry, change inbounds)
  POST /api/user/{username}/reset -> reset usage
  POST /api/user/{username}/revoke_sub -> reissue subscription link
  GET  /api/inbounds           -> available inbounds (locations)

The client caches the admin token and refreshes it on 401.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import aiohttp

from ..config import get_settings

_settings = get_settings()

GB = 1024 ** 3


class MarzbanError(Exception):
    pass


class MarzbanClient:
    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.base_url = (base_url or _settings.marzban_base_url).rstrip("/")
        self.username = username or _settings.marzban_username
        self.password = password or _settings.marzban_password
        self._token: str | None = None
        self._token_exp: float = 0.0

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.username and self.password)

    async def _get_token(self, session: aiohttp.ClientSession) -> str:
        if self._token and time.time() < self._token_exp:
            return self._token
        url = f"{self.base_url}/api/admin/token"
        data = {"username": self.username, "password": self.password}
        async with session.post(url, data=data) as resp:
            if resp.status != 200:
                raise MarzbanError(f"auth failed: {resp.status}")
            payload = await resp.json()
        self._token = payload["access_token"]
        # tokens are typically valid ~1 day; refresh conservatively
        self._token_exp = time.time() + 3600
        return self._token

    async def _request(
        self, method: str, path: str, *, json: dict | None = None
    ) -> dict:
        async with aiohttp.ClientSession() as session:
            token = await self._get_token(session)
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{self.base_url}{path}"
            async with session.request(
                method, url, json=json, headers=headers
            ) as resp:
                if resp.status == 401:
                    # token expired mid-flight; refresh once
                    self._token = None
                    token = await self._get_token(session)
                    headers["Authorization"] = f"Bearer {token}"
                    async with session.request(
                        method, url, json=json, headers=headers
                    ) as resp2:
                        return await self._handle(resp2)
                return await self._handle(resp)

    @staticmethod
    async def _handle(resp: aiohttp.ClientResponse) -> dict:
        if resp.status >= 400:
            text = await resp.text()
            raise MarzbanError(f"{resp.status}: {text}")
        if resp.content_type == "application/json":
            return await resp.json()
        return {}

    # ---- high-level operations ------------------------------------------

    @staticmethod
    def _expire_ts(days: int) -> int:
        return int(
            (datetime.now(timezone.utc) + timedelta(days=days)).timestamp()
        )

    async def create_user(
        self,
        username: str,
        traffic_gb: float,
        days: int,
        inbounds: dict | None = None,
        proxies: dict | None = None,
    ) -> dict:
        body = {
            "username": username,
            "proxies": proxies or _settings.marzban_default_proxies,
            "inbounds": inbounds or _settings.marzban_default_inbounds,
            "data_limit": int(traffic_gb * GB),
            "expire": self._expire_ts(days),
            "data_limit_reset_strategy": "month",
            "status": "active",
        }
        return await self._request("POST", "/api/user", json=body)

    async def get_user(self, username: str) -> dict:
        return await self._request("GET", f"/api/user/{username}")

    async def extend_user(
        self, username: str, add_days: int, traffic_gb: float | None = None
    ) -> dict:
        """Extend expiry from the later of now/current expiry; optionally reset limit."""
        current = await self.get_user(username)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        base = max(current.get("expire") or now_ts, now_ts)
        new_expire = base + add_days * 86400
        body: dict = {"expire": new_expire, "status": "active"}
        if traffic_gb is not None:
            body["data_limit"] = int(traffic_gb * GB)
        return await self._request("PUT", f"/api/user/{username}", json=body)

    async def set_inbounds(self, username: str, inbounds: dict) -> dict:
        return await self._request(
            "PUT", f"/api/user/{username}", json={"inbounds": inbounds}
        )

    async def reset_usage(self, username: str) -> dict:
        return await self._request("POST", f"/api/user/{username}/reset")

    async def revoke_subscription(self, username: str) -> dict:
        """Reissue the subscription link / vless uuid."""
        return await self._request("POST", f"/api/user/{username}/revoke_sub")

    async def list_inbounds(self) -> dict:
        return await self._request("GET", "/api/inbounds")

    def subscription_url(self, user_payload: dict) -> str | None:
        """Extract absolute subscription url from a user payload."""
        url = user_payload.get("subscription_url")
        if not url:
            return None
        if url.startswith("http"):
            return url
        return f"{self.base_url}{url}"

    @staticmethod
    def used_traffic_gb(user_payload: dict) -> float:
        used = user_payload.get("used_traffic") or 0
        return round(used / GB, 2)


_client: MarzbanClient | None = None


def get_marzban() -> MarzbanClient:
    global _client
    if _client is None:
        _client = MarzbanClient()
    return _client
