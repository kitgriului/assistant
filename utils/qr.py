"""Utilities for QR code generation."""
from io import BytesIO
from typing import Final

import qrcode


def generate_qr_bytes(data: str) -> BytesIO:
    """Generate a QR code PNG into a BytesIO buffer.

    This preserves the original behavior and parameters while
    documenting the defaults and adding type hints.

    Args:
        data: Arbitrary string payload to encode in the QR.

    Returns:
        BytesIO: Binary buffer positioned at start, containing PNG image.
    """
    VERSION: Final[int] = 1
    ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_H
    BOX_SIZE: Final[int] = 10
    BORDER: Final[int] = 4

    qr = qrcode.QRCode(
        version=VERSION,
        error_correction=ERROR_CORRECTION,
        box_size=BOX_SIZE,
        border=BORDER,
    )

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

