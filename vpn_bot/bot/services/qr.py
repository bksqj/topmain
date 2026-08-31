"""QR-code generation for a subscription link."""
from __future__ import annotations

import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def make_qr_png(data: str) -> bytes:
    """Render `data` as a PNG QR code and return the raw bytes."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
