from __future__ import annotations

import json
from typing import Any

from versionghost.agent import anthropic, openai_compat


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class _Client:
    def __init__(self, payload: dict[str, Any], calls: list[dict[str, Any]]) -> None:
        self.payload = payload
        self.calls = calls

    def __enter__(self) -> "_Client":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def post(self, url: str, **kwargs: Any) -> _Response:
        self.calls.append({"url": url, **kwargs})
        return _Response(self.payload)


def test_openai_compatible_adapter_requests_json(monkeypatch: Any) -> None:
    calls: list[dict[str, Any]] = []
    expected = {"ok": True, "route": "local-open-model"}
    payload = {"choices": [{"message": {"content": json.dumps(expected)}}]}
    monkeypatch.setattr(
        openai_compat.httpx,
        "Client",
        lambda timeout: _Client(payload, calls),
    )
    monkeypatch.setenv("VERSIONGHOST_OPENAI_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("VERSIONGHOST_OPENAI_MODEL", "qwen-test")

    provider = openai_compat.OpenAICompatibleProvider()
    result = provider._chat_json("system", "user")

    assert result == expected
    assert calls[0]["url"] == "http://model.test/v1/chat/completions"
    assert calls[0]["json"]["model"] == "qwen-test"
    assert calls[0]["json"]["response_format"] == {"type": "json_object"}


def test_hosted_messages_adapter_parses_text_json(monkeypatch: Any) -> None:
    calls: list[dict[str, Any]] = []
    expected = {"ok": True, "route": "hosted"}
    payload = {"content": [{"type": "text", "text": json.dumps(expected)}]}
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only-key")
    monkeypatch.setattr(
        anthropic.httpx,
        "Client",
        lambda timeout: _Client(payload, calls),
    )

    provider = anthropic.AnthropicProvider()
    result = provider._chat_json("system", "user")

    assert result == expected
    assert calls[0]["url"] == "https://api.anthropic.com/v1/messages"
    assert calls[0]["headers"]["x-api-key"] == "test-only-key"
    assert calls[0]["json"]["temperature"] == 0
