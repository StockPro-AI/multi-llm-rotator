"""Claude (Anthropic) provider for multi-llm-rotator.

Uses the official anthropic SDK.
Install: pip install anthropic
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List

try:
    import anthropic
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "anthropic is required for the Claude provider. "
        "Install it with: pip install anthropic"
    ) from e


DEFAULT_MODEL = "claude-opus-4-5"


class ClaudeProvider:
    """
    Static provider class for Anthropic Claude.

    All methods are class-level so LLMRotator can call them
    without instantiation.
    """

    name = "claude"

    MODELS = {
        "haiku": "claude-haiku-4-5",
        "sonnet": "claude-sonnet-4-5",
        "opus": "claude-opus-4-5",
    }

    @classmethod
    def _client(cls, api_key: str) -> anthropic.Anthropic:
        return anthropic.Anthropic(api_key=api_key)

    @classmethod
    def chat(
        cls,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 8096,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """
        Send a chat request to Claude and return the response text.

        Args:
            api_key: Anthropic API key.
            model: Model name (e.g. 'claude-opus-4-5').
            messages: List of {role, content} dicts (OpenAI-style).
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum output tokens.
            system_prompt: System prompt string.

        Returns:
            Response text as string.
        """
        client = cls._client(api_key)

        # Extract system from messages if not explicitly provided
        sys_msg = system_prompt
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system" and not sys_msg:
                sys_msg = msg["content"]
            else:
                filtered_messages.append({"role": msg["role"], "content": msg["content"]})

        create_kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered_messages,
        }
        if sys_msg:
            create_kwargs["system"] = sys_msg

        response = client.messages.create(**create_kwargs)
        return response.content[0].text

    @classmethod
    def stream(
        cls,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 8096,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream response chunks from Claude."""
        client = cls._client(api_key)

        sys_msg = system_prompt
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system" and not sys_msg:
                sys_msg = msg["content"]
            else:
                filtered_messages.append({"role": msg["role"], "content": msg["content"]})

        create_kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered_messages,
        }
        if sys_msg:
            create_kwargs["system"] = sys_msg

        with client.messages.stream(**create_kwargs) as stream:
            for text in stream.text_stream:
                yield text


# Auto-register with LLMRotator when the module is imported
from ..rotator import LLMRotator  # noqa: E402
LLMRotator.register_provider("claude", ClaudeProvider)
