from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from verity.models import Registry, Release
from verity.registry import canonical_json
from verity.walrus import WalrusError, WalrusTransientError, pull, push

FAKE_BLOB_ID = "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcdef"


@pytest.fixture
def rich_registry(minimal_registry) -> Registry:
    """minimal_registry extended with a release row."""
    minimal_registry.releases.append(
        Release(id="rel:0.1.0", version="0.1.0", timestamp="2024-01-01T00:00:00Z")
    )
    return minimal_registry


def _mock_response(status_code: int, body: object) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.text = json.dumps(body)
    resp.content = json.dumps(body).encode("utf-8")
    return resp


# --- push ---

def test_push_newly_created(minimal_registry):
    body = {"newlyCreated": {"blobObject": {"blobId": FAKE_BLOB_ID}}}
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.put.return_value = _mock_response(200, body)
        blob_id = push(minimal_registry)
    assert blob_id == FAKE_BLOB_ID


def test_push_already_certified(minimal_registry):
    body = {"alreadyCertified": {"blobId": FAKE_BLOB_ID}}
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.put.return_value = _mock_response(200, body)
        blob_id = push(minimal_registry)
    assert blob_id == FAKE_BLOB_ID


def test_push_sends_canonical_json(minimal_registry):
    body = {"newlyCreated": {"blobObject": {"blobId": FAKE_BLOB_ID}}}
    with patch("verity.walrus.httpx.Client") as MockClient:
        mock_put = MockClient.return_value.__enter__.return_value.put
        mock_put.return_value = _mock_response(200, body)
        push(minimal_registry)
        call_kwargs = mock_put.call_args
    sent_content = call_kwargs.kwargs["content"]
    assert sent_content == canonical_json(minimal_registry).encode("utf-8")


def test_push_passes_epochs(minimal_registry):
    body = {"newlyCreated": {"blobObject": {"blobId": FAKE_BLOB_ID}}}
    with patch("verity.walrus.httpx.Client") as MockClient:
        mock_put = MockClient.return_value.__enter__.return_value.put
        mock_put.return_value = _mock_response(200, body)
        push(minimal_registry, epochs=10)
        call_kwargs = mock_put.call_args
    assert call_kwargs.kwargs["params"] == {"epochs": 10}


def test_push_http_error_raises(minimal_registry):
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.put.return_value = _mock_response(500, {"error": "server error"})
        with pytest.raises(WalrusError, match="Upload failed: HTTP 500"):
            push(minimal_registry)


def test_push_unexpected_response_shape(minimal_registry):
    body = {"unknownKey": {}}
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.put.return_value = _mock_response(200, body)
        with pytest.raises(WalrusError, match="Unexpected response shape"):
            push(minimal_registry)


# --- pull ---

def test_pull_returns_registry(minimal_registry):
    body = json.loads(canonical_json(minimal_registry))
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = _mock_response(200, body)
        result = pull(FAKE_BLOB_ID)
    assert result.repo_id == minimal_registry.repo_id
    assert len(result.features) == len(minimal_registry.features)


def test_pull_requests_correct_url():
    body = {"schema_version": "0.1.0", "repo_id": "repo:test"}
    with patch("verity.walrus.httpx.Client") as MockClient:
        mock_get = MockClient.return_value.__enter__.return_value.get
        mock_get.return_value = _mock_response(200, body)
        pull(FAKE_BLOB_ID)
        url = mock_get.call_args.args[0]
    assert FAKE_BLOB_ID in url
    assert url.startswith("https://aggregator")


def test_pull_http_error_raises():
    with patch("verity.walrus.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = _mock_response(404, {"error": "not found"})
        with pytest.raises(WalrusError, match="Download failed: HTTP 404"):
            pull(FAKE_BLOB_ID)


def test_pull_custom_aggregator_url(minimal_registry):
    body = json.loads(canonical_json(minimal_registry))
    custom_url = "https://my-aggregator.example.com"
    with patch("verity.walrus.httpx.Client") as MockClient:
        mock_get = MockClient.return_value.__enter__.return_value.get
        mock_get.return_value = _mock_response(200, body)
        pull(FAKE_BLOB_ID, aggregator_url=custom_url)
        url = mock_get.call_args.args[0]
    assert url.startswith(custom_url)


# --- retry ---

def test_store_retries_on_5xx_then_succeeds(minimal_registry):
    success_body = {"newlyCreated": {"blobObject": {"blobId": FAKE_BLOB_ID}}}
    responses = [
        _mock_response(503, {"error": "service unavailable"}),
        _mock_response(200, success_body),
    ]
    with patch("verity.walrus.httpx.Client") as MockClient:
        with patch("verity.walrus.time.sleep"):
            MockClient.return_value.__enter__.return_value.put.side_effect = responses
            blob_id = push(minimal_registry)
    assert blob_id == FAKE_BLOB_ID


def test_store_raises_after_all_retries_exhausted(minimal_registry):
    with patch("verity.walrus.httpx.Client") as MockClient:
        with patch("verity.walrus.time.sleep"):
            MockClient.return_value.__enter__.return_value.put.return_value = _mock_response(503, {})
            with pytest.raises(WalrusTransientError, match="Upload failed: HTTP 503"):
                push(minimal_registry)


def test_store_does_not_retry_4xx(minimal_registry):
    with patch("verity.walrus.httpx.Client") as MockClient:
        with patch("verity.walrus.time.sleep") as mock_sleep:
            MockClient.return_value.__enter__.return_value.put.return_value = _mock_response(400, {})
            with pytest.raises(WalrusError):
                push(minimal_registry)
            mock_sleep.assert_not_called()


def test_fetch_retries_on_transport_error(minimal_registry):
    body = json.loads(canonical_json(minimal_registry))
    with patch("verity.walrus.httpx.Client") as MockClient:
        with patch("verity.walrus.time.sleep"):
            MockClient.return_value.__enter__.return_value.get.side_effect = [
                httpx.TransportError("connection reset"),
                _mock_response(200, body),
            ]
            result = pull(FAKE_BLOB_ID)
    assert result.repo_id == minimal_registry.repo_id


def test_fetch_does_not_retry_404():
    with patch("verity.walrus.httpx.Client") as MockClient:
        with patch("verity.walrus.time.sleep") as mock_sleep:
            MockClient.return_value.__enter__.return_value.get.return_value = _mock_response(404, {})
            with pytest.raises(WalrusError, match="HTTP 404"):
                pull(FAKE_BLOB_ID)
            mock_sleep.assert_not_called()
