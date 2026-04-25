"""Core rotation engine for multi-llm-rotator."""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Type

from .accounts import Account, AccountManager

logger = logging.getLogger("multi_llm_rotator")


class RotationStrategy(str, Enum):
    ROUND_ROBIN = "round-robin"   # cycle through accounts evenly
    LEAST_USED = "least-used"     # prefer account with fewest requests
    RANDOM = "random"             # pick randomly among available


class AllAccountsRateLimited(Exception):
    """Raised when no account is currently available."""

    def __init__(self, provider: str, retry_after: float) -> None:
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(
            f"All {provider} accounts are rate-limited. "
            f"Retry after {retry_after:.1f}s."
        )


class LLMRotator:
    """
    High-level facade that ties AccountManager + Provider together.

    Usage::

        rotator = LLMRotator()
        rotator.add_account("gemini", "g1", api_key="AIza...", model="gemini-2.0-flash")
        rotator.add_account("gemini", "g2", api_key="AIza...", model="gemini-2.0-flash")

        response = rotator.chat("gemini", messages=[{"role": "user", "content": "Hello"}])
    """

    _PROVIDER_REGISTRY: Dict[str, Any] = {}  # populated by providers

    def __init__(
        self,
        strategy: RotationStrategy = RotationStrategy.ROUND_ROBIN,
        retry_on_rate_limit: bool = True,
        max_retries: int = 3,
        rate_limit_backoff: float = 60.0,
        account_manager: Optional[AccountManager] = None,
    ) -> None:
        self.strategy = strategy
        self.retry_on_rate_limit = retry_on_rate_limit
        self.max_retries = max_retries
        self.rate_limit_backoff = rate_limit_backoff
        self.accounts = account_manager or AccountManager()
        self._round_robin_idx: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Provider registration
    # ------------------------------------------------------------------
    @classmethod
    def register_provider(cls, name: str, provider_cls: Any) -> None:
        cls._PROVIDER_REGISTRY[name.lower()] = provider_cls

    def _get_provider(self, provider: str) -> Any:
        p = self._PROVIDER_REGISTRY.get(provider.lower())
        if p is None:
            raise ValueError(
                f"Unknown provider '{provider}'. "
                f"Available: {list(self._PROVIDER_REGISTRY.keys())}"
            )
        return p

    # ------------------------------------------------------------------
    # Account management helpers
    # ------------------------------------------------------------------
    def add_account(
        self,
        provider: str,
        label: str,
        api_key: str,
        model: str,
    ) -> Account:
        return self.accounts.add_account(provider, label, api_key, model)

    def remove_account(self, provider: str, label: str) -> bool:
        return self.accounts.remove_account(provider, label)

    def list_accounts(self, provider: Optional[str] = None) -> List[Account]:
        return self.accounts.list_accounts(provider)

    def set_enabled(self, provider: str, label: str, enabled: bool) -> bool:
        return self.accounts.set_enabled(provider, label, enabled)

    # ------------------------------------------------------------------
    # Account selection
    # ------------------------------------------------------------------
    def _select_account(self, provider: str) -> Account:
        available = self.accounts.get_available(provider)
        if not available:
            # compute earliest retry time
            all_accs = self.accounts.list_accounts(provider)
            if not all_accs:
                raise ValueError(f"No accounts registered for provider '{provider}'.")
            earliest = min(a.rate_limited_until for a in all_accs)
            raise AllAccountsRateLimited(provider, max(0.0, earliest - time.time()))

        if self.strategy == RotationStrategy.ROUND_ROBIN:
            idx = self._round_robin_idx.get(provider, 0) % len(available)
            self._round_robin_idx[provider] = idx + 1
            return available[idx]

        if self.strategy == RotationStrategy.LEAST_USED:
            return min(available, key=lambda a: a.request_count)

        if self.strategy == RotationStrategy.RANDOM:
            import random
            return random.choice(available)

        return available[0]

    # ------------------------------------------------------------------
    # Core chat interface
    # ------------------------------------------------------------------
    def chat(
        self,
        provider: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Send a chat request through the rotator.

        Automatically retries with the next available account on rate-limit
        errors (429 / RateLimitError).
        """
        provider_cls = self._get_provider(provider)
        attempt = 0

        while attempt < self.max_retries:
            account = self._select_account(provider)
            effective_model = model or account.model
            try:
                logger.debug(
                    "[%s] Using account '%s' (model=%s, attempt=%d)",
                    provider, account.label, effective_model, attempt + 1,
                )
                account.mark_used()
                result = provider_cls.chat(
                    api_key=account.api_key,
                    model=effective_model,
                    messages=messages,
                    **kwargs,
                )
                self.accounts.save()
                return result

            except Exception as exc:  # noqa: BLE001
                if self._is_rate_limit(exc):
                    retry_after = self._parse_retry_after(exc)
                    logger.warning(
                        "[%s] Account '%s' rate-limited. Back off %.0fs.",
                        provider, account.label, retry_after,
                    )
                    account.mark_rate_limited(retry_after)
                    self.accounts.save()
                    attempt += 1
                    if attempt >= self.max_retries:
                        raise
                    continue
                raise

        raise RuntimeError("Exceeded max_retries without success.")

    # ------------------------------------------------------------------
    # Streaming chat
    # ------------------------------------------------------------------
    def stream(
        self,
        provider: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Streaming variant — yields text chunks."""
        provider_cls = self._get_provider(provider)
        account = self._select_account(provider)
        effective_model = model or account.model
        account.mark_used()
        self.accounts.save()
        yield from provider_cls.stream(
            api_key=account.api_key,
            model=effective_model,
            messages=messages,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_rate_limit(exc: Exception) -> bool:
        name = type(exc).__name__.lower()
        msg = str(exc).lower()
        return (
            "ratelimit" in name
            or "rate_limit" in name
            or "429" in msg
            or "rate limit" in msg
            or "quota" in msg
            or "resource_exhausted" in msg
        )

    @staticmethod
    def _parse_retry_after(exc: Exception, default: float = 60.0) -> float:
        """Try to extract retry-after seconds from the exception."""
        for attr in ("retry_after", "retry_delay", "headers"):
            val = getattr(exc, attr, None)
            if val is not None:
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, dict):
                    ra = val.get("retry-after") or val.get("Retry-After")
                    if ra:
                        return float(ra)
        return default
