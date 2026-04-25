"""multi-llm-rotator: Universal multi-account rotation for Gemini, Claude & ChatGPT."""

__version__ = "1.0.0"
__author__ = "StockPro-AI"

from .rotator import LLMRotator
from .accounts import AccountManager
from .service import get_llm_service
from .providers.gemini import GeminiProvider
from .providers.claude import ClaudeProvider
from .providers.openai import OpenAIProvider

__all__ = [
    "LLMRotator",
    "AccountManager",
    "get_llm_service",
    "GeminiProvider",
    "ClaudeProvider",
    "OpenAIProvider",
]
