from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from verity.memwal import MemWalBackend, MemWalError
from verity.registry import canonical_json
from verity.walrus import AGGREGATOR_URL

FAKE_BLOB_ID = "mw-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
SERVER_URL = "https://relayer.memwal.example"


def _make_client(blob_id: str = FAKE_BLOB_ID) -> MagicMock:
    """Return a mock MemWalSync client whose remember_and_wait returns blob_id."""
    client = MagicMock()
    result = MagicMock()
    result.blob_id = blob_id
    client.remember_and_wait.return_value = result
    return client


def _backend(**kwargs) -> tuple[MemWalBackend, MagicMock]:
    """Build a MemWalBackend with a mocked MemWalSync client. Returns (backend, mock_client)."""
    mock_client = _make_client(kwargs.pop("blob_id", FAKE_BLOB_ID))
    with patch("verity.memwal.MemWalSync") as MockSync:
        MockSync.create.return_value = mock_client
        b = MemWalBackend(
            key="0xdeadbeef",
            account_id="0xaccount",
            server_url=SERVER_URL,
            **kwargs,
        )
    b._client = mock_client
    return b, mock_client


# --- init ---

def test_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MEMWAL_KEY", raising=False)
    with pytest.raises(MemWalError, match="key"):
        with patch("verity.memwal.MemWalSync"):
            MemWalBackend(account_id="0xacc", server_url=SERVER_URL)


def test_raises_without_account_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MEMWAL_ACCOUNT_ID", raising=False)
    with pytest.raises(MemWalError, match="account_id"):
        with patch("verity.memwal.MemWalSync"):
            MemWalBackend(key="0xkey", server_url=SERVER_URL)


def test_reads_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEMWAL_KEY", "0xkeyfromenviron")
    monkeypatch.setenv("MEMWAL_ACCOUNT_ID", "0xaccfromenviron")
    monkeypatch.setenv("MEMWAL_SERVER_URL", SERVER_URL)
    with patch("verity.memwal.MemWalSync") as MockSync:
        MockSync.create.return_value = MagicMock()
        b = MemWalBackend()
    assert b._client is not None


def test_create_passes_key_and_account_id() -> None:
    with patch("verity.memwal.MemWalSync") as MockSync:
        MockSync.create.return_value = MagicMock()
        MemWalBackend(key="0xmykey", account_id="0xmyacc", server_url=SERVER_URL)
        call_kwargs = MockSync.create.call_args.kwargs
    assert call_kwargs["key"] == "0xmykey"
    assert call_kwargs["account_id"] == "0xmyacc"


def test_create_passes_namespace() -> None:
    with patch("verity.memwal.MemWalSync") as MockSync:
        MockSync.create.return_value = MagicMock()
        MemWalBackend(key="0xk", account_id="0xa", server_url=SERVER_URL, namespace="myns")
        call_kwargs = MockSync.create.call_args.kwargs
    assert call_kwargs["namespace"] == "myns"


def test_create_passes_env_when_set() -> None:
    with patch("verity.memwal.MemWalSync") as MockSync:
        MockSync.create.return_value = MagicMock()
        MemWalBackend(key="0xk", account_id="0xa", server_url=SERVER_URL, env="prod")
        call_kwargs = MockSync.create.call_args.kwargs
    assert call_kwargs["env"] == "prod"


# --- store ---

def test_store_returns_blob_id(minimal_registry) -> None:
    backend, _ = _backend()
    blob_id = backend.store(canonical_json(minimal_registry).encode())
    assert blob_id == FAKE_BLOB_ID


def test_store_calls_remember_and_wait(minimal_registry) -> None:
    backend, mock_client = _backend()
    content = canonical_json(minimal_registry).encode()
    backend.store(content)
    mock_client.remember_and_wait.assert_called_once()
    call_args = mock_client.remember_and_wait.call_args
    assert call_args.args[0] == content.decode("utf-8")


def test_store_passes_namespace(minimal_registry) -> None:
    backend, mock_client = _backend(namespace="proj-ns")
    backend.store(b"hello")
    call_kwargs = mock_client.remember_and_wait.call_args.kwargs
    assert call_kwargs.get("namespace") == "proj-ns"


def test_store_wraps_sdk_error() -> None:
    from memwal import MemWalError as SdkError

    backend, mock_client = _backend()
    mock_client.remember_and_wait.side_effect = SdkError("relayer down")
    with pytest.raises(MemWalError, match="MemWal store failed"):
        backend.store(b"data")


# --- fetch (goes to Walrus aggregator directly) ---

def _mock_http_response(status_code: int, content: bytes) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.text = content.decode(errors="replace")
    return resp


def test_fetch_returns_content(minimal_registry) -> None:
    content = canonical_json(minimal_registry).encode()
    backend, _ = _backend()
    with patch("verity.memwal.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = (
            _mock_http_response(200, content)
        )
        result = backend.fetch(FAKE_BLOB_ID)
    assert result == content


def test_fetch_requests_walrus_aggregator_url() -> None:
    backend, _ = _backend()
    with patch("verity.memwal.httpx.Client") as MockClient:
        mock_get = MockClient.return_value.__enter__.return_value.get
        mock_get.return_value = _mock_http_response(200, b"{}")
        backend.fetch(FAKE_BLOB_ID)
        url = mock_get.call_args.args[0]
    assert FAKE_BLOB_ID in url
    assert url.startswith(AGGREGATOR_URL)


def test_fetch_http_error_raises() -> None:
    backend, _ = _backend()
    with patch("verity.memwal.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = (
            _mock_http_response(404, b"not found")
        )
        with pytest.raises(MemWalError, match="fetch failed: HTTP 404"):
            backend.fetch(FAKE_BLOB_ID)


def test_fetch_uses_custom_aggregator_url() -> None:
    custom_url = "https://my-aggregator.example.com"
    backend, _ = _backend()
    backend._aggregator_url = custom_url
    with patch("verity.memwal.httpx.Client") as MockClient:
        mock_get = MockClient.return_value.__enter__.return_value.get
        mock_get.return_value = _mock_http_response(200, b"{}")
        backend.fetch(FAKE_BLOB_ID)
        url = mock_get.call_args.args[0]
    assert url.startswith(custom_url)
