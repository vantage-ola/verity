"""Unit tests for src/verity/signing.py."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from verity.signing import (
    generate_keypair,
    load_private_key,
    load_public_key,
    pubkey_from_b64,
    pubkey_to_b64,
    save_private_key,
    save_public_key,
    sign_blob,
    verify_blob,
)


def test_generate_keypair_types() -> None:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )

    priv, pub = generate_keypair()
    assert isinstance(priv, Ed25519PrivateKey)
    assert isinstance(pub, Ed25519PublicKey)


def test_save_load_private_key(tmp_path: Path) -> None:
    priv, _ = generate_keypair()
    key_path = tmp_path / "signing.key"
    save_private_key(priv, key_path)
    assert key_path.exists()
    loaded = load_private_key(key_path)
    # round-trip: sign with original, verify with loaded public key
    pub_b64 = pubkey_to_b64(loaded.public_key())
    sig = sign_blob("test-blob", priv)
    assert verify_blob("test-blob", sig, pub_b64)


def test_save_load_public_key(tmp_path: Path) -> None:
    priv, pub = generate_keypair()
    pub_path = tmp_path / "signing.pub"
    save_public_key(pub, pub_path)
    assert pub_path.exists()
    loaded = load_public_key(pub_path)
    assert pubkey_to_b64(loaded) == pubkey_to_b64(pub)


def test_sign_verify_valid() -> None:
    priv, pub = generate_keypair()
    pub_b64 = pubkey_to_b64(pub)
    sig = sign_blob("AbCdEfGh123", priv)
    assert verify_blob("AbCdEfGh123", sig, pub_b64) is True


def test_verify_wrong_key_returns_false() -> None:
    priv, pub = generate_keypair()
    other_priv, other_pub = generate_keypair()
    sig = sign_blob("AbCdEfGh123", priv)
    # verify with different pubkey
    assert verify_blob("AbCdEfGh123", sig, pubkey_to_b64(other_pub)) is False


def test_verify_tampered_blob_id_returns_false() -> None:
    priv, pub = generate_keypair()
    sig = sign_blob("AbCdEfGh123", priv)
    assert verify_blob("tampered-blob-id", sig, pubkey_to_b64(pub)) is False


def test_pubkey_b64_roundtrip() -> None:
    _, pub = generate_keypair()
    b64 = pubkey_to_b64(pub)
    recovered = pubkey_from_b64(b64)
    assert pubkey_to_b64(recovered) == b64


def test_sign_returns_base64_string() -> None:
    priv, _ = generate_keypair()
    sig = sign_blob("some-blob-id", priv)
    # should be decodable base64 and 64 bytes (Ed25519 signature length)
    assert len(base64.b64decode(sig)) == 64


def test_load_nonexistent_key_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_private_key(tmp_path / "nonexistent.key")


def test_save_private_key_creates_parent_dirs(tmp_path: Path) -> None:
    priv, _ = generate_keypair()
    nested = tmp_path / "a" / "b" / "c" / "signing.key"
    save_private_key(priv, nested)
    assert nested.exists()
