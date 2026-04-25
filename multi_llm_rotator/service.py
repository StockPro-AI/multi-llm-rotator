"""Service factory for multi-llm-rotator.

Provides convenience functions to create a pre-configured LLMRotator
automatically loading API keys from environment variables.

Supports:
  - All three providers at once (Gemini + Claude + OpenAI)
  - A single provider with multiple accounts
  - Any combination of providers
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from .rotator import LLMRotator, RotationStrategy

logger = logging.getLogger("multi_llm_rotator")


def get_llm_service(
    strategy: str = RotationStrategy.ROUND_ROBIN,
    # --- Provider selection (None = auto-detect from env, False = disabled) ---
    use_gemini: Optional[bool] = None,
    use_claude: Optional[bool] = None,
    use_openai: Optional[bool] = None,
    # --- Model defaults ---
    gemini_model: str = "gemini-2.0-flash",
    claude_model: str = "claude-sonnet-4-5",
    openai_model: str = "gpt-4o-mini",
    # --- How many accounts to scan per provider ---
    max_gemini_accounts: int = 10,
    max_claude_accounts: int = 10,
    max_openai_accounts: int = 10,
) -> LLMRotator:
    """Create a pre-configured LLMRotator from environment variables.

    You can use ALL providers together, or restrict to just one or two:

    Examples::

        # All providers (auto-detect whatever keys are set in the environment)
        rotator = get_llm_service()

        # Gemini only — multiple accounts
        rotator = get_llm_service(use_gemini=True, use_claude=False, use_openai=False)

        # Claude + OpenAI only
        rotator = get_llm_service(use_gemini=False)

        # Explicit opt-in to specific providers
        rotator = get_llm_service(use_gemini=True, use_openai=True, use_claude=False)

    When ``use_*`` is ``None`` (default), the provider is loaded automatically
    **if** at least one matching environment variable is found.
    When ``use_*`` is ``False``, the provider is always skipped.
    When ``use_*`` is ``True``, the provider is required — a warning is logged
    if no keys are found for it.

    Environment variable naming convention::

        GEMINI_KEY_1, GEMINI_KEY_2, ...  (up to max_gemini_accounts)
        CLAUDE_KEY_1, CLAUDE_KEY_2, ...  (up to max_claude_accounts)
        OPENAI_KEY_1, OPENAI_KEY_2, ...  (up to max_openai_accounts)

    Args:
        strategy:             Rotation strategy (round-robin, least-used, random).
        use_gemini:           True=force on, False=force off, None=auto-detect.
        use_claude:           True=force on, False=force off, None=auto-detect.
        use_openai:           True=force on, False=force off, None=auto-detect.
        gemini_model:         Default Gemini model.
        claude_model:         Default Claude / Anthropic model.
        openai_model:         Default OpenAI model.
        max_gemini_accounts:  Max number of Gemini env-var slots to scan.
        max_claude_accounts:  Max number of Claude env-var slots to scan.
        max_openai_accounts:  Max number of OpenAI env-var slots to scan.

    Returns:
        Configured LLMRotator with all discovered accounts loaded.

    Raises:
        ValueError: If no accounts could be loaded at all.
    """
    rotator = LLMRotator(strategy=strategy)

    # ------------------------------------------------------------------ Gemini
    if use_gemini is not False:
        keys = _collect_keys("GEMINI_KEY", max_gemini_accounts)
        if keys:
            for idx, key in enumerate(keys, start=1):
                rotator.add_account("gemini", f"g{idx}", api_key=key, model=gemini_model)
            logger.info("Loaded %d Gemini account(s).", len(keys))
        elif use_gemini is True:
            logger.warning(
                "use_gemini=True but no GEMINI_KEY_* environment variables found!"
            )

    # ------------------------------------------------------------------ Claude
    if use_claude is not False:
        keys = _collect_keys("CLAUDE_KEY", max_claude_accounts)
        if keys:
            for idx, key in enumerate(keys, start=1):
                rotator.add_account("claude", f"c{idx}", api_key=key, model=claude_model)
            logger.info("Loaded %d Claude account(s).", len(keys))
        elif use_claude is True:
            logger.warning(
                "use_claude=True but no CLAUDE_KEY_* environment variables found!"
            )

    # ------------------------------------------------------------------ OpenAI
    if use_openai is not False:
        keys = _collect_keys("OPENAI_KEY", max_openai_accounts)
        if keys:
            for idx, key in enumerate(keys, start=1):
                rotator.add_account("openai", f"o{idx}", api_key=key, model=openai_model)
            logger.info("Loaded %d OpenAI account(s).", len(keys))
        elif use_openai is True:
            logger.warning(
                "use_openai=True but no OPENAI_KEY_* environment variables found!"
            )

    accounts = rotator.list_accounts()
    if not accounts:
        raise ValueError(
            "No LLM accounts loaded. "
            "Set at least one of GEMINI_KEY_1, CLAUDE_KEY_1 or OPENAI_KEY_1 "
            "in your environment (or .env file)."
        )

    logger.info(
        "LLM service ready — %d account(s) across provider(s): %s",
        len(accounts),
        ", ".join(sorted({a.provider for a in accounts})),
    )
    return rotator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_gemini_service(
    strategy: str = RotationStrategy.ROUND_ROBIN,
    model: str = "gemini-2.0-flash",
    max_accounts: int = 10,
) -> LLMRotator:
    """Shortcut: Gemini-only rotator with multiple accounts.

    Example::

        rotator = get_gemini_service()  # loads GEMINI_KEY_1 .. GEMINI_KEY_N
    """
    return get_llm_service(
        strategy=strategy,
        use_gemini=True,
        use_claude=False,
        use_openai=False,
        gemini_model=model,
        max_gemini_accounts=max_accounts,
    )


def get_claude_service(
    strategy: str = RotationStrategy.ROUND_ROBIN,
    model: str = "claude-sonnet-4-5",
    max_accounts: int = 10,
) -> LLMRotator:
    """Shortcut: Claude-only rotator with multiple accounts.

    Example::

        rotator = get_claude_service()  # loads CLAUDE_KEY_1 .. CLAUDE_KEY_N
    """
    return get_llm_service(
        strategy=strategy,
        use_gemini=False,
        use_claude=True,
        use_openai=False,
        claude_model=model,
        max_claude_accounts=max_accounts,
    )


def get_openai_service(
    strategy: str = RotationStrategy.ROUND_ROBIN,
    model: str = "gpt-4o-mini",
    max_accounts: int = 10,
) -> LLMRotator:
    """Shortcut: OpenAI-only rotator with multiple accounts.

    Example::

        rotator = get_openai_service()  # loads OPENAI_KEY_1 .. OPENAI_KEY_N
    """
    return get_llm_service(
        strategy=strategy,
        use_gemini=False,
        use_claude=False,
        use_openai=True,
        openai_model=model,
        max_openai_accounts=max_accounts,
    )


def _collect_keys(prefix: str, max_count: int) -> List[str]:
    """Scan environment for KEY_1 .. KEY_N and return all non-empty values."""
    keys: List[str] = []
    for i in range(1, max_count + 1):
        val = os.getenv(f"{prefix}_{i}")
        if val and val.strip():
            keys.append(val.strip())
    return keys
