"""basic_usage.py - Demonstrates multi-llm-rotator with all three providers.

Run:
    pip install multi-llm-rotator[all]   # or from local clone
    python examples/basic_usage.py

Set your API keys as environment variables before running:
    export GEMINI_KEY_1=AIza...
    export GEMINI_KEY_2=AIza...
    export CLAUDE_KEY_1=sk-ant-...
    export OPENAI_KEY_1=sk-...
"""

import os
from multi_llm_rotator import LLMRotator
from multi_llm_rotator.providers import GeminiProvider, ClaudeProvider, OpenAIProvider  # noqa: F401
from multi_llm_rotator.rotator import RotationStrategy

# --- Setup rotator ---
rotator = LLMRotator(strategy=RotationStrategy.ROUND_ROBIN)

# Add Gemini accounts (from env vars)
for i in range(1, 4):
    key = os.getenv(f"GEMINI_KEY_{i}")
    if key:
        rotator.add_account("gemini", f"g{i}", api_key=key, model="gemini-2.0-flash")
        print(f"Added Gemini account g{i}")

# Add Claude accounts
for i in range(1, 4):
    key = os.getenv(f"CLAUDE_KEY_{i}")
    if key:
        rotator.add_account("claude", f"c{i}", api_key=key, model="claude-sonnet-4-5")
        print(f"Added Claude account c{i}")

# Add OpenAI accounts
for i in range(1, 4):
    key = os.getenv(f"OPENAI_KEY_{i}")
    if key:
        rotator.add_account("openai", f"o{i}", api_key=key, model="gpt-4o-mini")
        print(f"Added OpenAI account o{i}")

# --- List accounts ---
print("\n--- Registered Accounts ---")
for acc in rotator.list_accounts():
    print(f"  {acc.provider}/{acc.label}: {acc.model} [{'enabled' if acc.enabled else 'disabled'}]")

messages = [{"role": "user", "content": "Say 'Hello from multi-llm-rotator!' in one sentence."}]

# --- Send requests (rotates automatically) ---
if rotator.accounts.get_available("gemini"):
    print("\n--- Gemini Response ---")
    response = rotator.chat("gemini", messages)
    print(response)

if rotator.accounts.get_available("claude"):
    print("\n--- Claude Response (streaming) ---")
    for chunk in rotator.stream("claude", messages):
        print(chunk, end="", flush=True)
    print()

if rotator.accounts.get_available("openai"):
    print("\n--- OpenAI Response ---")
    response = rotator.chat("openai", messages)
    print(response)

print("\nDone! Accounts have been persisted to ~/.config/multi-llm-rotator/accounts.json")
