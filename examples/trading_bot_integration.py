"""trading_bot_integration.py

Shows how to integrate multi-llm-rotator into a trading bot / NexusTrader.
Demonstrates:
  - Singleton rotator pattern
  - Provider-aware routing (use Claude for analysis, Gemini for screening)
  - Graceful fallback between providers
  - Structured market analysis prompts
"""

from __future__ import annotations

import os
from typing import Optional

from multi_llm_rotator import LLMRotator
from multi_llm_rotator.providers import GeminiProvider, ClaudeProvider, OpenAIProvider  # noqa
from multi_llm_rotator.rotator import RotationStrategy, AllAccountsRateLimited


# ---------------------------------------------------------------------------
# Singleton LLM service
# ---------------------------------------------------------------------------

_rotator: Optional[LLMRotator] = None


def get_llm_service() -> LLMRotator:
    """Return the shared rotator (lazy init)."""
    global _rotator
    if _rotator is None:
        _rotator = LLMRotator(strategy=RotationStrategy.LEAST_USED)
        _setup_accounts(_rotator)
    return _rotator


def _setup_accounts(rotator: LLMRotator) -> None:
    """Load all accounts from environment variables."""
    # Gemini - multiple accounts for high-volume screening
    for i in range(1, 6):
        key = os.getenv(f"GEMINI_KEY_{i}")
        if key:
            rotator.add_account("gemini", f"g{i}", api_key=key, model="gemini-2.0-flash")

    # Claude - premium accounts for deep analysis
    for i in range(1, 4):
        key = os.getenv(f"CLAUDE_KEY_{i}")
        if key:
            rotator.add_account("claude", f"c{i}", api_key=key, model="claude-opus-4-5")

    # OpenAI - fallback
    for i in range(1, 3):
        key = os.getenv(f"OPENAI_KEY_{i}")
        if key:
            rotator.add_account("openai", f"o{i}", api_key=key, model="gpt-4o")


# ---------------------------------------------------------------------------
# Trading-specific LLM functions
# ---------------------------------------------------------------------------

MARKET_SYSTEM_PROMPT = """You are an expert quantitative analyst and trader.
Analyze market data objectively and provide concise, actionable insights.
Always include: trend direction, key levels, risk factors, and a bias (bullish/bearish/neutral).
"""


def analyze_market(
    symbol: str,
    price_data: str,
    provider: str = "claude",
    fallback_provider: str = "gemini",
) -> str:
    """
    Get AI market analysis for a given symbol.

    Args:
        symbol: Trading pair, e.g. 'BTC/USDT'
        price_data: String representation of OHLCV data or summary.
        provider: Primary provider to use ('claude' for best analysis).
        fallback_provider: Provider to fall back to if primary is rate-limited.

    Returns:
        Analysis text string.
    """
    rotator = get_llm_service()
    messages = [
        {"role": "system", "content": MARKET_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Analyze {symbol}:\n\n{price_data}\n\nProvide a concise trading analysis.",
        },
    ]

    try:
        return rotator.chat(provider, messages)
    except (AllAccountsRateLimited, ValueError):
        # Fallback to alternative provider
        return rotator.chat(fallback_provider, messages)


def screen_symbols(
    symbols: list[str],
    market_summary: str,
    provider: str = "gemini",
) -> str:
    """Screen multiple symbols quickly using the fast Gemini Flash model."""
    rotator = get_llm_service()
    symbols_str = ", ".join(symbols)
    messages = [
        {"role": "system", "content": MARKET_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Screen these symbols for trading opportunities: {symbols_str}\n\n"
                f"Market context: {market_summary}\n\n"
                "Rank top 3 by opportunity score (1-10) with brief reasoning."
            ),
        },
    ]
    return rotator.chat(provider, messages)


def generate_trade_report(
    trades: list[dict],
    provider: str = "openai",
) -> str:
    """Generate a human-readable trade report."""
    rotator = get_llm_service()
    trade_data = "\n".join(
        f"- {t['symbol']}: {t['side']} {t['qty']} @ {t['price']} | P&L: {t.get('pnl', 'N/A')}"
        for t in trades
    )
    messages = [
        {"role": "system", "content": "You are a professional trading journal assistant."},
        {
            "role": "user",
            "content": f"Generate a concise trading report for today:\n\n{trade_data}",
        },
    ]
    return rotator.chat(provider, messages)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Trading Bot LLM Integration Demo")
    print("=" * 40)

    rotator = get_llm_service()
    accounts = rotator.list_accounts()
    print(f"Loaded {len(accounts)} accounts:")
    for acc in accounts:
        print(f"  {acc.provider}/{acc.label}: {acc.model}")

    if not accounts:
        print("\nNo accounts found. Set environment variables:")
        print("  GEMINI_KEY_1, CLAUDE_KEY_1, OPENAI_KEY_1")
    else:
        # Demo market analysis
        sample_data = """
        BTC/USDT - 4H Chart:
        Open: 94,200 | High: 95,800 | Low: 93,400 | Close: 95,100
        Volume: 12,400 BTC | RSI: 62 | MACD: bullish crossover
        Key levels: Support 93,000 | Resistance 96,500
        """

        print("\nRunning market analysis...")
        analysis = analyze_market("BTC/USDT", sample_data)
        print(analysis)
