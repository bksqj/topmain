"""YooKassa payment creation and webhook verification.

Uses the official `yookassa` SDK. The SDK is synchronous, so calls are run in
a thread executor to avoid blocking the event loop.
"""
from __future__ import annotations

import asyncio
import uuid

from ..config import get_settings

_settings = get_settings()

try:  # optional import so the bot still boots without the SDK installed
    from yookassa import Configuration, Payment as YooPayment

    if _settings.yookassa_shop_id and _settings.yookassa_secret_key:
        Configuration.account_id = _settings.yookassa_shop_id
        Configuration.secret_key = _settings.yookassa_secret_key
    _SDK_AVAILABLE = True
except Exception:  # pragma: no cover - SDK missing
    YooPayment = None  # type: ignore
    _SDK_AVAILABLE = False


class PaymentResult:
    def __init__(self, provider_id: str, confirmation_url: str) -> None:
        self.provider_id = provider_id
        self.confirmation_url = confirmation_url


async def create_payment(
    amount_rub: int,
    description: str,
    metadata: dict,
    method: str = "yookassa",
) -> PaymentResult:
    """Create a YooKassa payment and return its id + confirmation url.

    `method` may be "sbp" to request the SBP payment method explicitly.
    """
    return_url = f"https://t.me/{_settings.bot_username}?start=paid"

    if not (_SDK_AVAILABLE and Configuration.account_id):
        # graceful stub for local development without credentials
        fake_id = f"stub-{uuid.uuid4().hex[:12]}"
        return PaymentResult(fake_id, f"{return_url}_{fake_id}")

    payload: dict = {
        "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": description,
        "metadata": metadata,
    }
    if method == "sbp":
        payload["payment_method_data"] = {"type": "sbp"}

    def _create() -> object:
        return YooPayment.create(payload, uuid.uuid4().hex)

    payment = await asyncio.to_thread(_create)
    confirmation_url = payment.confirmation.confirmation_url  # type: ignore[attr-defined]
    return PaymentResult(payment.id, confirmation_url)  # type: ignore[attr-defined]


async def fetch_payment(provider_id: str) -> dict:
    """Fetch a payment's current state from YooKassa."""
    if not (_SDK_AVAILABLE and Configuration.account_id):
        return {"id": provider_id, "status": "pending"}

    def _get():
        return YooPayment.find_one(provider_id)

    payment = await asyncio.to_thread(_get)
    return {
        "id": payment.id,  # type: ignore[attr-defined]
        "status": payment.status,  # type: ignore[attr-defined]
        "metadata": dict(payment.metadata or {}),  # type: ignore[attr-defined]
    }
