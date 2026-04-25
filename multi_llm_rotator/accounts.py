"""Account storage and management for multi-llm-rotator."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "multi-llm-rotator"
ACCOUNTS_FILE = "accounts.json"


@dataclass
class Account:
    provider: str          # "gemini" | "claude" | "openai"
    label: str             # human-readable label, e.g. "gmail1"
    api_key: str
    model: str             # default model for this account
    enabled: bool = True
    rate_limited_until: float = 0.0   # unix timestamp
    request_count: int = 0
    last_used: float = 0.0

    def is_available(self) -> bool:
        return self.enabled and time.time() >= self.rate_limited_until

    def mark_rate_limited(self, retry_after_seconds: float = 60.0) -> None:
        self.rate_limited_until = time.time() + retry_after_seconds

    def mark_used(self) -> None:
        self.last_used = time.time()
        self.request_count += 1


class AccountManager:
    """Persist and manage accounts per provider."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self.config_dir = Path(config_dir or os.getenv("MLR_CONFIG_DIR", DEFAULT_CONFIG_DIR))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._accounts_path = self.config_dir / ACCOUNTS_FILE
        self._accounts: Dict[str, List[Account]] = {}  # provider -> accounts
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self._accounts_path.exists():
            return
        try:
            raw = json.loads(self._accounts_path.read_text())
            for provider, accs in raw.items():
                self._accounts[provider] = [Account(**a) for a in accs]
        except Exception:
            pass  # corrupt file — start fresh

    def save(self) -> None:
        data = {
            p: [asdict(a) for a in accs]
            for p, accs in self._accounts.items()
        }
        self._accounts_path.write_text(json.dumps(data, indent=2))

    # ------------------------------------------------------------------
    # Account CRUD
    # ------------------------------------------------------------------
    def add_account(
        self,
        provider: str,
        label: str,
        api_key: str,
        model: str,
    ) -> Account:
        provider = provider.lower()
        if provider not in self._accounts:
            self._accounts[provider] = []
        # avoid duplicates by label
        for acc in self._accounts[provider]:
            if acc.label == label:
                acc.api_key = api_key
                acc.model = model
                self.save()
                return acc
        acc = Account(provider=provider, label=label, api_key=api_key, model=model)
        self._accounts[provider].append(acc)
        self.save()
        return acc

    def remove_account(self, provider: str, label: str) -> bool:
        provider = provider.lower()
        before = len(self._accounts.get(provider, []))
        self._accounts[provider] = [
            a for a in self._accounts.get(provider, []) if a.label != label
        ]
        if len(self._accounts[provider]) < before:
            self.save()
            return True
        return False

    def list_accounts(self, provider: Optional[str] = None) -> List[Account]:
        if provider:
            return list(self._accounts.get(provider.lower(), []))
        result = []
        for accs in self._accounts.values():
            result.extend(accs)
        return result

    def get_available(self, provider: str) -> List[Account]:
        return [
            a for a in self._accounts.get(provider.lower(), []) if a.is_available()
        ]

    def set_enabled(self, provider: str, label: str, enabled: bool) -> bool:
        for acc in self._accounts.get(provider.lower(), []):
            if acc.label == label:
                acc.enabled = enabled
                self.save()
                return True
        return False

    def clear_rate_limits(self, provider: Optional[str] = None) -> None:
        targets = [provider.lower()] if provider else list(self._accounts.keys())
        for p in targets:
            for acc in self._accounts.get(p, []):
                acc.rate_limited_until = 0.0
        self.save()
