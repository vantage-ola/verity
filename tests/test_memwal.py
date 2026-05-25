from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from verity.memwal import MemWalBackend, MemWalError
from verity.registry import canonical_json
from verity.walrus import WalrusError

FAKE_BLOB_ID = "mw-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
SERVER_URL = "https://relayer.memwal.example"


def _backend(**kwargs) -> tuple[MemWalBackend, MagicMock, MagicMock]:
    """
    Build a MemWalBackend with mocked internals.
    Returns (backend, mock_memwal_client, mock_walrus_backend).
    """
    mock_memwal = MagicMock()
    mock_walrus = MagicMock()
    mock_walrus.store.return_value = kwargs.pop("blob_id", FAKE_BLOB_ID)
    mock_walrus.fetch.return_value = kwargs.pop("fetch_content", b"{}")

    with patch("verity.memwal.MemWalSync") as MockSync, \
         patch("verity.memwal.WalrusBackend", return_value=mock_walrus):
        MockSync.create.return_value = mock_memwal
        b = MemWalBackend(
            key="0xdeadbeef",
            account_id="0xaccount",
            server_url=SERVER_URL,
            **kwargs,
        )
    b._client = mock_memwal
    b._walrus = mock_walrus
    return b, mock_memwal, mock_walrus


# ---------------------------------------------------------------------------
# init / config
# ---------------------------------------------------------------------------

def test_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MEMWAL_KEY", raising=False)
    with pytest.raises(MemWalError, match="key"):
        with patch("verity.memwal.MemWalSync"), patch("verity.memwal.WalrusBackend"):
            MemWalBackend(account_id="0xacc", server_url=SERVER_URL)


def test_raises_without_account_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MEMWAL_ACCOUNT_ID", raising=False)
    with pytest.raises(MemWalError, match="account_id"):
        with patch("verity.memwal.MemWalSync"), patch("verity.memwal.WalrusBackend"):
            MemWalBackend(key="0xkey", server_url=SERVER_URL)


def test_reads_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEMWAL_KEY", "0xkeyfromenviron")
    monkeypatch.setenv("MEMWAL_ACCOUNT_ID", "0xaccfromenviron")
    monkeypatch.setenv("MEMWAL_SERVER_URL", SERVER_URL)
    with patch("verity.memwal.MemWalSync") as MockSync, \
         patch("verity.memwal.WalrusBackend"):
        MockSync.create.return_value = MagicMock()
        b = MemWalBackend()
    assert b._client is not None


def test_create_passes_key_and_account_id() -> None:
    with patch("verity.memwal.MemWalSync") as MockSync, \
         patch("verity.memwal.WalrusBackend"):
        MockSync.create.return_value = MagicMock()
        MemWalBackend(key="0xmykey", account_id="0xmyacc", server_url=SERVER_URL)
        call_kwargs = MockSync.create.call_args.kwargs
    assert call_kwargs["key"] == "0xmykey"
    assert call_kwargs["account_id"] == "0xmyacc"


def test_create_passes_namespace() -> None:
    with patch("verity.memwal.MemWalSync") as MockSync, \
         patch("verity.memwal.WalrusBackend"):
        MockSync.create.return_value = MagicMock()
        MemWalBackend(key="0xk", account_id="0xa", server_url=SERVER_URL, namespace="myns")
        call_kwargs = MockSync.create.call_args.kwargs
    assert call_kwargs["namespace"] == "myns"


def test_create_passes_env_when_set() -> None:
    with patch("verity.memwal.MemWalSync") as MockSync, \
         patch("verity.memwal.WalrusBackend"):
        MockSync.create.return_value = MagicMock()
        MemWalBackend(key="0xk", account_id="0xa", server_url=SERVER_URL, env="prod")
        call_kwargs = MockSync.create.call_args.kwargs
    assert call_kwargs["env"] == "prod"


# ---------------------------------------------------------------------------
# store — Walrus primary, MemWal pointer secondary
# ---------------------------------------------------------------------------

def test_store_returns_walrus_blob_id(minimal_registry) -> None:
    backend, _, _ = _backend()
    result = backend.store(canonical_json(minimal_registry).encode())
    assert result == FAKE_BLOB_ID


def test_store_calls_walrus_store(minimal_registry) -> None:
    backend, _, mock_walrus = _backend()
    content = canonical_json(minimal_registry).encode()
    backend.store(content)
    mock_walrus.store.assert_called_once_with(content)


def test_store_registers_pointer_in_memwal(minimal_registry) -> None:
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(minimal_registry).encode())
    mock_memwal.remember_and_wait.assert_called_once()
    text = mock_memwal.remember_and_wait.call_args.args[0]
    assert FAKE_BLOB_ID in text
    assert "verity registry" in text


def test_store_pointer_includes_repo_id(minimal_registry) -> None:
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(minimal_registry).encode())
    text = mock_memwal.remember_and_wait.call_args.args[0]
    assert minimal_registry.repo_id in text


def test_store_passes_namespace_to_memwal(minimal_registry) -> None:
    backend, mock_memwal, _ = _backend(namespace="proj-ns")
    backend.store(canonical_json(minimal_registry).encode())
    call_kwargs = mock_memwal.remember_and_wait.call_args.kwargs
    assert call_kwargs.get("namespace") == "proj-ns"


def test_store_walrus_error_raises(minimal_registry) -> None:
    backend, _, mock_walrus = _backend()
    mock_walrus.store.side_effect = WalrusError("publisher down")
    with pytest.raises(MemWalError, match="Walrus upload"):
        backend.store(b"data")


def test_store_context_entries_sent_to_memwal() -> None:
    from verity.models import ContextEntry, Registry
    from verity.registry import canonical_json

    reg = Registry(
        repo_id="repo:ctx-test",
        context=[
            ContextEntry(key="arch", value="5-layer chain"),
            ContextEntry(key="why", value="agents need memory"),
        ],
    )
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(reg).encode())
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    assert any("arch" in c and "5-layer chain" in c for c in calls)
    assert any("why" in c and "agents need memory" in c for c in calls)


def test_store_context_includes_repo_id() -> None:
    from verity.models import ContextEntry, Registry
    from verity.registry import canonical_json

    reg = Registry(
        repo_id="repo:myproject",
        context=[ContextEntry(key="stack", value="python + walrus")],
    )
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(reg).encode())
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    context_calls = [c for c in calls if "stack" in c]
    assert context_calls
    assert "repo:myproject" in context_calls[0]


def test_store_non_json_content_does_not_raise() -> None:
    backend, mock_memwal, _ = _backend()
    result = backend.store(b"not valid json at all")
    assert result == FAKE_BLOB_ID
    text = mock_memwal.remember_and_wait.call_args.args[0]
    assert "unknown" in text


def test_store_context_nonfatal_on_memwal_error() -> None:
    from memwal import MemWalError as SdkError
    from verity.models import ContextEntry, Registry
    from verity.registry import canonical_json

    reg = Registry(
        repo_id="repo:test",
        context=[ContextEntry(key="k", value="v")],
    )
    backend, mock_memwal, _ = _backend()
    mock_memwal.remember_and_wait.side_effect = SdkError("relayer down")
    result = backend.store(canonical_json(reg).encode())
    assert result == FAKE_BLOB_ID


def test_store_memwal_error_is_nonfatal(minimal_registry) -> None:
    from memwal import MemWalError as SdkError

    backend, mock_memwal, _ = _backend()
    mock_memwal.remember_and_wait.side_effect = SdkError("relayer down")
    # should NOT raise — blob is on Walrus, MemWal pointer is best-effort
    result = backend.store(canonical_json(minimal_registry).encode())
    assert result == FAKE_BLOB_ID


# ---------------------------------------------------------------------------
# fetch — direct Walrus, no MemWal
# ---------------------------------------------------------------------------

def test_fetch_returns_content(minimal_registry) -> None:
    content = canonical_json(minimal_registry).encode()
    backend, _, _ = _backend(fetch_content=content)
    assert backend.fetch(FAKE_BLOB_ID) == content


def test_fetch_calls_walrus_fetch() -> None:
    backend, _, mock_walrus = _backend()
    backend.fetch(FAKE_BLOB_ID)
    mock_walrus.fetch.assert_called_once_with(FAKE_BLOB_ID)


def test_fetch_does_not_call_memwal() -> None:
    backend, mock_memwal, _ = _backend()
    backend.fetch(FAKE_BLOB_ID)
    mock_memwal.recall.assert_not_called()
    mock_memwal.remember_and_wait.assert_not_called()


def test_fetch_walrus_error_wraps_as_memwal_error() -> None:
    backend, _, mock_walrus = _backend()
    mock_walrus.fetch.side_effect = WalrusError("blob not found")
    with pytest.raises(MemWalError, match="fetch failed"):
        backend.fetch(FAKE_BLOB_ID)
