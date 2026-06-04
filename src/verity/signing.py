from __future__ import annotations

import base64
from pathlib import Path

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
except ImportError as _e:  # pragma: no cover
    raise ImportError(
        "Signing support requires the cryptography package. "
        "Install it with: pip install 'walrus-verity[sign]'"
    ) from _e


def generate_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    private_key = Ed25519PrivateKey.generate()
    return private_key, private_key.public_key()


def save_private_key(key: Ed25519PrivateKey, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)


def load_private_key(path: Path) -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(path.read_bytes(), password=None)  # type: ignore[return-value]


def save_public_key(key: Ed25519PublicKey, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pem = key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    path.write_bytes(pem)


def load_public_key(path: Path) -> Ed25519PublicKey:
    return serialization.load_pem_public_key(path.read_bytes())  # type: ignore[return-value]


def pubkey_to_b64(key: Ed25519PublicKey) -> str:
    raw = key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


def pubkey_from_b64(b64: str) -> Ed25519PublicKey:
    raw = base64.b64decode(b64)
    return Ed25519PublicKey.from_public_bytes(raw)


def sign_blob(blob_id: str, private_key: Ed25519PrivateKey) -> str:
    sig_bytes = private_key.sign(blob_id.encode("utf-8"))
    return base64.b64encode(sig_bytes).decode("ascii")


def verify_blob(blob_id: str, signature_b64: str, pubkey_b64: str) -> bool:
    pub = pubkey_from_b64(pubkey_b64)
    try:
        pub.verify(base64.b64decode(signature_b64), blob_id.encode("utf-8"))
        return True
    except InvalidSignature:
        return False
