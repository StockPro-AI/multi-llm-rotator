"""Service factory for multi-llm-rotator.

Provides a convenience function to create a pre-configured LLMRotator
automatically loading all API keys from environment variables.
"""

from __future__ import annotations

import os

from .rotator import LLMRotator, RotationStrategy


def get_llm_service(
    strategy: str = RotationStrategy.ROUND_ROBIN,
    gemini_model: str = "gemini-2.0-flash",
    claude_model: str = "claude-sonnet-4-5",
    openai_model: str = "gpt-4o-mini",
    max_gemini_accounts: int = 10,
    max_claude_accounts: int = 10,
    max_openai_accounts: int = 10,
) -> LLMRotator:
    """Create a pre-configured LLMRotator from environment variables.

    Scans environment for API keys following the naming convention:
      GEMINI_KEY_1, GEMINI_KEY_2, ...  (up to max_gemini_accounts)
      CLAUDE_KEY_1, CLAUDE_KEY_2, ...  (up to max_claude_accounts)
      OPENAI_KEY_1, OPENAI_KEY_2, ...  (up to max_openai_accounts)

    Args:
        strategy: Rotation strategy (round-robin, least-used, random).
        gemini_model: Default Gemini model to use.
        claude_model: Default Claude model to use.
        openai_model: Default OpenAI model to use.
        max_gemini_accounts: Max number of Gemini accounts to scan for.
        max_claude_accounts: Max number of Claude accounts to scan for.
        max_openai_accounts: Max number of OpenAI accounts to scan for.

    Returns:
        Configured LLMRotator instance with all discovered accounts loaded.
    """
    rotator = LLMRotator(strategy=strategy)

    # Load Gemini accounts
    for i in range(1, max_gemini_accounts + 1):
        key = os.getenv(f"GEMINI_KEY_{i}")
        if key:
            rotator.add_account("gemini", f"g{i}", api_key=key, model=gemini_model)

    # Load Claude / Anthropic accounts
    for i in range(1, max_claude_accounts + 1):
        key = os.getenv(f"CLAUDE_KEY_{i}")
        if key:
            rotator.add_account("claude", f"c{i}", api_key=key, model=claude_model)

    # Load OpenAI accounts
    for i in range(1, max_openai_accounts + 1):
        key = os.getenv(f"OPENAI_KEY_{i}")
        if key:
            rotator.add_account("openai", f"o{i}", api_key=key, model=openai_model)

    return rotator
