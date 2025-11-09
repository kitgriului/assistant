import pytest
from utils.qr import generate_qr_bytes


def test_generate_qr_bytes():
    bio = generate_qr_bytes("test123")
    # PNG files start with the 8-byte signature: \x89PNG\r\n\x1a\n
    sig = bio.read(8)
    assert sig[:4] == b"\x89PNG"
