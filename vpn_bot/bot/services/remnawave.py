"""Async Remnawave REST API client (panel API v2.x).

Endpoints (verified against the Remnawave OpenAPI 2.8 spec):
  POST  /api/users                                 create user
  GET   /api/users/{uuid}                           get by uuid
  GET   /api/users/by-telegram-id/{telegramId}      get by telegram id (array)
  PATCH /api/users                                  update (body carries uuid)
  POST  /api/users/{uuid}/actions/reset-traffic     reset usage
  POST  /api/users/{uuid}/actions/revoke            reissue subscription
  GET   /api/internal-squads                        list squads (locations)

Auth: Authorization: Bearer <API token> (Settings → API Tokens in the panel).
All successful responses are wrapped as {"response": ...}; helpers unwrap it.
Traffic is in bytes; expireAt is an ISO-8601 date-time.
"""
from __future__ import annotations

from datetime import datetime, timezone

import aiohttp

from ..config import get_settings

_settings = get_settings()

GB = 1024 ** 3


class RemnawaveError(Exception):
    pass


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class RemnawaveClient:
    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = (base_url or _settings.remnawave_base_url).rstrip("/")
        self.token = token or _settings.remnawave_token

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    async def _request(self, method: str, path: str, *, json: dict | None = None):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, json=json, headers=headers
            ) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    raise RemnawaveError(f"{resp.status}: {text}")
                if resp.content_type == "application/json":
                    data = await resp.json()
                    # responses are wrapped in {"response": ...}
                    return data.get("response", data) if isinstance(data, dict) else data
                return {}

    # ---- users ----------------------------------------------------------

    async def create_user(
        self,
        username: str,
        expire_at: datetime,
        traffic_gb: float,
        squads: list[str],
        telegram_id: int | None = None,
    ) -> dict:
        body: dict = {
            "username": username,
            "status": "ACTIVE",
            "expireAt": _iso(expire_at),
            "trafficLimitBytes": int(traffic_gb * GB),
            "trafficLimitStrategy": _settings.remnawave_traffic_strategy,
            "activeInternalSquads": squads,
        }
        if telegram_id is not None:
            body["telegramId"] = telegram_id
        return await self._request("POST", "/api/users", json=body)

    async def get_user(self, uuid: str) -> dict:
        return await self._request("GET", f"/api/users/{uuid}")

    async def get_user_by_telegram_id(self, telegram_id: int) -> dict | None:
        data = await self._request(
            "GET", f"/api/users/by-telegram-id/{telegram_id}"
        )
        if isinstance(data, list):
            return data[0] if data else None
        return data or None

    async def update_user(self, uuid: str, **fields) -> dict:
        body = {"uuid": uuid, **fields}
        return await self._request("PATCH", "/api/users", json=body)

    async def extend_user(
        self, uuid: str, expire_at: datetime, traffic_gb: float | None = None
    ) -> dict:
        fields: dict = {"expireAt": _iso(expire_at), "status": "ACTIVE"}
        if traffic_gb is not None:
            fields["trafficLimitBytes"] = int(traffic_gb * GB)
        return await self.update_user(uuid, **fields)

    async def set_squads(self, uuid: str, squads: list[str]) -> dict:
        return await self.update_user(uuid, activeInternalSquads=squads)

    async def reset_traffic(self, uuid: str) -> dict:
        return await self._request(
            "POST", f"/api/users/{uuid}/actions/reset-traffic"
        )

    async def revoke_subscription(self, uuid: str) -> dict:
        """Reissue the subscription (new short uuid / links)."""
        return await self._request("POST", f"/api/users/{uuid}/actions/revoke")

    async def list_internal_squads(self) -> list[dict]:
        data = await self._request("GET", "/api/internal-squads")
        if isinstance(data, dict):
            return data.get("internalSquads", [])
        return []

    # ---- helpers --------------------------------------------------------

    @staticmethod
    def subscription_url(user: dict) -> str | None:
        return user.get("subscriptionUrl")

    @staticmethod
    def used_traffic_gb(user: dict) -> float:
        traffic = user.get("userTraffic") or {}
        used = traffic.get("usedTrafficBytes") or 0
        return round(used / GB, 2)


_client: RemnawaveClient | None = None


def get_remnawave() -> RemnawaveClient:
    global _client
    if _client is None:
        _client = RemnawaveClient()
    return _client
