from __future__ import annotations

import base64
import hashlib
import os
import platform
import traceback
import uuid


def _machine_seed() -> str:
    return "".join([
        platform.node(),
        platform.machine(),
        str(uuid.getnode()),
        os.environ.get("COMPUTERNAME", ""),
        os.environ.get("USERNAME", ""),
    ])


def _derive_key(salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", _machine_seed().encode(), salt, 100000, 32
    )


def encrypt_password(plain: str) -> str:
    if not plain:
        return ""
    salt = os.urandom(16)
    key = _derive_key(salt)
    cipher = bytes([b ^ key[i % 32] for i, b in enumerate(plain.encode())])
    return base64.b64encode(salt + cipher).decode()


def decrypt_password(stored: str) -> str:
    if not stored:
        return ""
    try:
        raw = base64.b64decode(stored)
        salt, cipher = raw[:16], raw[16:]
        key = _derive_key(salt)
        return bytes([b ^ key[i % 32] for i, b in enumerate(cipher)]).decode()
    except Exception:
        traceback.print_exc()
        return ""
