from __future__ import annotations

from versionghost.agent.base import AgentProvider
from versionghost.agent.anthropic import AnthropicProvider
from versionghost.agent.deterministic import DeterministicDemoProvider
from versionghost.agent.openai_compat import OpenAICompatibleProvider


def build_provider(name: str) -> AgentProvider:
    if name == "deterministic-demo":
        return DeterministicDemoProvider()
    if name in {"openai-compatible", "ollama"}:
        return OpenAICompatibleProvider()
    if name == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"Unsupported provider: {name}")
