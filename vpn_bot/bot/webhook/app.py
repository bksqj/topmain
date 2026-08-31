"""FastAPI app exposing the YooKassa payment webhook.

Runs in the same process as the bot; shares the DB and a Bot instance so it
can provision the subscription and message the buyer on `payment.succeeded`.
"""
from __future__ import annotations

import ipaddress
import logging

from aiogram import Bot
from fastapi import FastAPI, Request, Response

from ..config import get_settings
from ..db import repo
from ..db.engine import async_session_factory
from ..services.orders import finalize_payment

logger = logging.getLogger(__name__)
_settings = get_settings()

# Official YooKassa notification source networks. Requests from other IPs are
# rejected. See https://yookassa.ru/developers/using-api/webhooks
YOOKASSA_NETWORKS = [
    ipaddress.ip_network(n)
    for n in (
        "185.71.76.0/27",
        "185.71.77.0/27",
        "77.75.153.0/25",
        "77.75.156.11/32",
        "77.75.156.35/32",
        "77.75.154.128/25",
        "2a02:5180::/32",
    )
]


def _ip_allowed(ip: str) -> bool:
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in YOOKASSA_NETWORKS)


def create_app(bot: Bot) -> FastAPI:
    app = FastAPI(title="VPN Bot Webhooks")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/webhook/yookassa")
    async def yookassa_webhook(request: Request) -> Response:
        client_ip = request.client.host if request.client else ""
        # allow configured shared-secret bypass OR IP allowlist
        secret_ok = False
        if _settings.yookassa_webhook_secret:
            header_secret = request.headers.get("X-Webhook-Secret", "")
            secret_ok = header_secret == _settings.yookassa_webhook_secret

        if not secret_ok and not _ip_allowed(client_ip):
            logger.warning("rejected webhook from %s", client_ip)
            return Response(status_code=403)

        try:
            body = await request.json()
        except Exception:
            return Response(status_code=400)

        event = body.get("event")
        obj = body.get("object", {})
        provider_id = obj.get("id")
        status = obj.get("status")

        if event != "payment.succeeded" or status != "succeeded" or not provider_id:
            # acknowledge everything else so YooKassa stops retrying
            return Response(status_code=200)

        async with async_session_factory() as session:
            payment = await repo.get_payment_by_provider_id(session, provider_id)
            if payment is None:
                logger.warning("webhook for unknown payment %s", provider_id)
                return Response(status_code=200)
            await finalize_payment(session, payment, bot=bot)

        return Response(status_code=200)

    return app
