"""OpenAI / ChatGPT provider for multi-llm-rotator.

Uses the official openai SDK (v1+).
Install: pip install openai

Also works with any OpenAI-compatible API
(e.g. Azure OpenAI, Together AI, Groq) by setting base_url.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

try:
    from openai import OpenAI, RateLimitError
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "openai is required for the OpenAI provider. "
        "Install it with: pip install openai"
    ) from e


DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider:
    """
    Static provider class for OpenAI / ChatGPT.

    All methods are class-level so LLMRotator can call them
    without instantiation.

    Supports custom base_url for OpenAI-compatible APIs.
    """

    name = "openai"

    MODELS = {
        "gpt4o": "gpt-4o",
        "gpt4o-mini": "gpt-4o-mini",
        "o1": "o1",
        "o3": "o3",
        "o4-mini": "o4-mini",
    }

    @classmethod
    def _client(cls, api_key: str, base_url: Optional[str] = None) -> OpenAI:
        kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAI(**kwargs)

    @classmethod
    def chat(
        cls,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Send a chat request to OpenAI and return the response text.

        Args:
            api_key: OpenAI API key.
            model: Model name (e.g. 'gpt-4o').
            messages: List of {role, content} dicts.
            temperature: Sampling temperature.
            max_tokens: Maximum completion tokens.
            base_url: Optional custom API base URL.

        Returns:
            Response text as string.
        """
        client = cls._client(api_key, base_url)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    @classmethod
    def stream(
        cls,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream response chunks from OpenAI."""
        client = cls._client(api_key, base_url)
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


# Auto-register with LLMRotator when the module is imported
from ..rotator import LLMRotator  # noqa: E402
LLMRotator.register_provider("openai", OpenAIProvider)
LLMRotator.register_provider("chatgpt", OpenAIProvider)  # alias
