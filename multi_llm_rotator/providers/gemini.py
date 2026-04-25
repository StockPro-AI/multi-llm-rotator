"""Gemini provider for multi-llm-rotator.

Uses the official google-generativeai SDK.
Install: pip install google-generativeai
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List

try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted, TooManyRequests
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "google-generativeai is required for the Gemini provider. "
        "Install it with: pip install google-generativeai"
    ) from e


DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiProvider:
    """
    Static provider class for Google Gemini.

    All methods are class-level so LLMRotator can call them
    without instantiation.
    """

    name = "gemini"

    # Default models available per tier
    MODELS = {
        "flash": "gemini-2.0-flash",
        "pro": "gemini-2.5-pro",
        "flash-thinking": "gemini-2.0-flash-thinking-exp",
    }

    @classmethod
    def _client(cls, api_key: str) -> genai.GenerativeModel:
        """Create a configured client (not cached to support multi-key rotation)."""
        genai.configure(api_key=api_key)
        return genai

    @classmethod
    def chat(
        cls,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 8192,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """
        Send a chat request to Gemini and return the response text.

        Args:
            api_key: Gemini API key.
            model: Model name (e.g. 'gemini-2.0-flash').
            messages: List of {role, content} dicts (OpenAI-style).
            temperature: Sampling temperature.
            max_tokens: Maximum output tokens.
            system_prompt: Optional system instruction.

        Returns:
            Response text as string.
        """
        genai.configure(api_key=api_key)

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        model_kwargs: Dict[str, Any] = {"generation_config": generation_config}
        if system_prompt:
            model_kwargs["system_instruction"] = system_prompt

        client_model = genai.GenerativeModel(model, **model_kwargs)

        # Convert OpenAI-style messages to Gemini format
        history = []
        last_user_msg = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                # Gemini handles system prompts at model level; skip here
                continue
            if role == "assistant":
                history.append({"role": "model", "parts": [content]})
            elif role == "user":
                last_user_msg = content
                if len(messages) > 1:
                    history.append({"role": "user", "parts": [content]})

        if not history or history[-1]["role"] != "user":
            chat = client_model.start_chat(history=history[:-1] if history else [])
            response = chat.send_message(last_user_msg)
        else:
            chat = client_model.start_chat(history=history[:-1])
            response = chat.send_message(history[-1]["parts"][0])

        return response.text

    @classmethod
    def stream(
        cls,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 8192,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream response chunks from Gemini."""
        genai.configure(api_key=api_key)

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        model_kwargs: Dict[str, Any] = {"generation_config": generation_config}
        if system_prompt:
            model_kwargs["system_instruction"] = system_prompt

        client_model = genai.GenerativeModel(model, **model_kwargs)

        last_user_msg = messages[-1]["content"] if messages else ""
        history = [
            {"role": "model" if m["role"] == "assistant" else m["role"],
             "parts": [m["content"]]}
            for m in messages[:-1]
            if m["role"] != "system"
        ]

        chat = client_model.start_chat(history=history)
        for chunk in chat.send_message(last_user_msg, stream=True):
            if chunk.text:
                yield chunk.text


# Auto-register with LLMRotator when the module is imported
from ..rotator import LLMRotator  # noqa: E402
LLMRotator.register_provider("gemini", GeminiProvider)
