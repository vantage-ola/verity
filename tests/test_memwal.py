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
    mock_memwal.remember_and_wait.assert_called()
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    registry_call = next(c for c in calls if "verity registry" in c)
    assert FAKE_BLOB_ID in registry_call
    assert "verity registry" in registry_call


def test_store_pointer_includes_repo_id(minimal_registry) -> None:
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(minimal_registry).encode())
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    registry_call = next(c for c in calls if "verity registry" in c)
    assert minimal_registry.repo_id in registry_call


def test_store_passes_namespace_to_memwal(minimal_registry) -> None:
    backend, mock_memwal, _ = _backend(namespace="proj-ns")
    backend.store(canonical_json(minimal_registry).encode())
    assert all(c.kwargs.get("namespace") == "proj-ns" for c in mock_memwal.remember_and_wait.call_args_list)


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


# ---------------------------------------------------------------------------
# store — batch summary memories
# ---------------------------------------------------------------------------

def _rich_registry():
    from verity.models import Claim, Feature, Release, Registry
    return Registry(
        repo_id="repo:rich",
        features=[
            Feature(id="feat:auth", title="User Auth", status="active"),
            Feature(id="feat:export", title="Data Export", status="deprecated"),
        ],
        claims=[
            Claim(id="clm:auth.t1", feature_id="feat:auth", title="Login works", tier="T1", status="verified"),
            Claim(id="clm:export.t1", feature_id="feat:export", title="CSV export", tier="T2", status="open"),
        ],
        releases=[
            Release(id="rel:0.1.0", version="0.1.0", timestamp="2025-01-01T00:00:00Z", claim_ids=["clm:auth.t1"]),
        ],
    )


def test_store_registers_features_summary() -> None:
    from verity.registry import canonical_json
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(_rich_registry()).encode())
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    feat_call = next(c for c in calls if "verity features" in c)
    assert "User Auth" in feat_call
    assert "feat:auth" in feat_call
    assert "Data Export" in feat_call
    assert "feat:export" in feat_call


def test_store_registers_verified_claims_summary() -> None:
    from verity.registry import canonical_json
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(_rich_registry()).encode())
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    vc_call = next(c for c in calls if "verity verified-claims" in c)
    assert "Login works" in vc_call
    assert "clm:auth.t1" in vc_call
    assert "CSV export" not in vc_call


def test_store_registers_latest_release() -> None:
    from verity.registry import canonical_json
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(_rich_registry()).encode())
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    rel_call = next(c for c in calls if "verity latest-release" in c)
    assert "0.1.0" in rel_call
    assert "1 claims" in rel_call


def test_store_no_release_skips_release_memory() -> None:
    from verity.models import Registry
    from verity.registry import canonical_json
    reg = _rich_registry()
    reg = reg.model_copy(update={"releases": []})
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(reg).encode())
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    assert not any("verity latest-release" in c for c in calls)


def test_store_no_features_skips_features_memory() -> None:
    from verity.models import Registry
    from verity.registry import canonical_json
    reg = Registry(repo_id="repo:empty")
    backend, mock_memwal, _ = _backend()
    backend.store(canonical_json(reg).encode())
    calls = [c.args[0] for c in mock_memwal.remember_and_wait.call_args_list]
    assert not any("verity features" in c for c in calls)
    assert not any("verity verified-claims" in c for c in calls)


# ---------------------------------------------------------------------------
# recall()
# ---------------------------------------------------------------------------


class _FakeMemory:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeResult:
    def __init__(self, results: list) -> None:
        self.results = results


def test_recall_calls_sdk_recall() -> None:
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.return_value = "You have 2 features."
    result = backend.recall("what features do we have")
    mock_memwal.recall.assert_called_once_with("what features do we have", namespace=backend.namespace)
    assert result == "You have 2 features."


def test_recall_passes_namespace() -> None:
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.return_value = "answer"
    backend.recall("any query", namespace="custom-ns")
    mock_memwal.recall.assert_called_once_with("any query", namespace="custom-ns")


def test_recall_sdk_error_raises_memwal_error() -> None:
    from memwal import MemWalError as SdkError
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.side_effect = SdkError("relayer down")
    with pytest.raises(MemWalError, match="MemWal recall failed"):
        backend.recall("any query")


def test_recall_string_return_path() -> None:
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.return_value = "plain string answer"
    result = backend.recall("q")
    assert result == "plain string answer"


def test_recall_result_object_top3() -> None:
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.return_value = _FakeResult([
        _FakeMemory("entry one"),
        _FakeMemory("entry two"),
        _FakeMemory("entry three"),
        _FakeMemory("entry four"),
        _FakeMemory("entry five"),
    ])
    result = backend.recall("q")
    lines = result.split("\n")
    assert lines == ["entry one", "entry two", "entry three"]


def test_recall_result_object_empty_results() -> None:
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.return_value = _FakeResult([])
    result = backend.recall("q")
    assert result == "(no results)"


def test_recall_skips_json_blobs() -> None:
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.return_value = _FakeResult([
        _FakeMemory('{"blob_id": "abc", "repo_id": "test"}'),
        _FakeMemory("verity features repo=test: Feature A"),
    ])
    result = backend.recall("q")
    assert "verity features" in result
    assert "{" not in result


def test_recall_deduplicates_results() -> None:
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.return_value = _FakeResult([
        _FakeMemory("verity features repo=test: Feature A"),
        _FakeMemory("verity features repo=test: Feature A"),
        _FakeMemory("verity verified-claims repo=test: Claim 1"),
    ])
    result = backend.recall("q")
    assert result.count("verity features") == 1
    assert "verity verified-claims" in result


def test_recall_fallback_when_all_filtered() -> None:
    backend, mock_memwal, _ = _backend()
    mock_memwal.recall.return_value = _FakeResult([
        _FakeMemory('{"blob_id": "abc"}'),
        _FakeMemory('{"blob_id": "def"}'),
    ])
    result = backend.recall("q")
    assert result == '{"blob_id": "abc"}'
