"""Field-level encryption and masking for restricted HR data classes (bank, national ID, salary, medical)."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet() -> Fernet:
    raw_key = getattr(settings, "FIELD_ENCRYPTION_KEY", "nice-hris-default-key")
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)


def encrypt_value(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith("enc::"):
        return value
    token = _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return f"enc::{token}"


def decrypt_value(value: str | None) -> str | None:
    if not value:
        return value
    if not value.startswith("enc::"):
        return value
    raw_token = value[5:]
    try:
        return _get_fernet().decrypt(raw_token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return "***ENCRYPTED***"


def mask_sensitive(value: str | None, visible_tail: int = 4) -> str:
    if not value:
        return ""
    plain = decrypt_value(value) or ""
    if len(plain) <= visible_tail:
        return "*" * len(plain)
    return f"{'*' * (len(plain) - visible_tail)}{plain[-visible_tail:]}"
