# multi-llm-rotator

> Universal multi-account rotation for **Gemini**, **Claude** and **ChatGPT** — auto-rotate between accounts on rate limits, unified interface, pluggable into any Python project.

---

## Features

- **Multi-provider** — Gemini, Claude (Anthropic), OpenAI / ChatGPT in one package
- **Multi-account per provider** — add as many accounts as you have
- **Auto-rotation** — seamlessly switches to the next account on rate-limit (429) errors
- **3 rotation strategies** — `round-robin`, `least-used`, `random`
- **Streaming** — native streaming support for all providers
- **CLI** — manage accounts with `mlr add / remove / list / enable / disable / chat`
- **Persistent storage** — accounts saved to `~/.config/multi-llm-rotator/accounts.json`
- **Modular** — install only the provider SDKs you need
- **Drop-in** — OpenAI-style `{role, content}` message format across all providers

---

## Installation

```bash
# Install with all providers
pip install git+https://github.com/StockPro-AI/multi-llm-rotator.git[all]

# Or install only what you need
pip install git+https://github.com/StockPro-AI/multi-llm-rotator.git[gemini]
pip install git+https://github.com/StockPro-AI/multi-llm-rotator.git[claude]
pip install git+https://github.com/StockPro-AI/multi-llm-rotator.git[openai]
```

---

## Quick Start

### Python API

```python
from multi_llm_rotator import LLMRotator
from multi_llm_rotator.providers import GeminiProvider, ClaudeProvider, OpenAIProvider  # triggers auto-register

rotator = LLMRotator()

# Add multiple Gemini accounts
rotator.add_account("gemini", "g1", api_key="AIza...", model="gemini-2.0-flash")
rotator.add_account("gemini", "g2", api_key="AIza...", model="gemini-2.0-flash")

# Add multiple Claude accounts
rotator.add_account("claude", "c1", api_key="sk-ant-...", model="claude-opus-4-5")
rotator.add_account("claude", "c2", api_key="sk-ant-...", model="claude-sonnet-4-5")

# Add multiple ChatGPT accounts
rotator.add_account("openai", "o1", api_key="sk-...", model="gpt-4o")
rotator.add_account("openai", "o2", api_key="sk-...", model="gpt-4o-mini")

messages = [{"role": "user", "content": "Was ist die Hauptstadt von Deutschland?"}]

# Auto-rotates between g1 and g2, retries on rate-limit
response = rotator.chat("gemini", messages)
print(response)

# Streaming
for chunk in rotator.stream("claude", messages):
    print(chunk, end="", flush=True)
```

### CLI

```bash
# Add accounts
mlr add gemini g1 --key AIza... --model gemini-2.0-flash
mlr add gemini g2 --key AIza... --model gemini-2.0-flash
mlr add claude c1 --key sk-ant-... --model claude-opus-4-5
mlr add openai o1 --key sk-... --model gpt-4o

# List all accounts
mlr list

# List only Gemini accounts
mlr list gemini

# Quick chat test
mlr chat gemini "Hallo, wer bist du?"
mlr chat claude "Was ist 2+2?" --strategy least-used

# Manage accounts
mlr disable gemini g1
mlr enable gemini g1
mlr clear-rate-limits
mlr remove gemini g1
```

---

## Rotation Strategies

| Strategy | Best for |
|---|---|
| `round-robin` (default) | Even load distribution |
| `least-used` | Preserve quotas, prefer fresh accounts |
| `random` | Maximum unpredictability |

```python
from multi_llm_rotator import LLMRotator
from multi_llm_rotator.rotator import RotationStrategy

rotator = LLMRotator(strategy=RotationStrategy.LEAST_USED)
```

---

## Configuration

Accounts are stored in `~/.config/multi-llm-rotator/accounts.json` (auto-created).

Override the config directory:

```bash
export MLR_CONFIG_DIR=/path/to/my/config
```

Or in Python:

```python
from multi_llm_rotator.accounts import AccountManager
from multi_llm_rotator import LLMRotator

mgr = AccountManager(config_dir="/path/to/config")
rotator = LLMRotator(account_manager=mgr)
```

---

## Supported Models

### Gemini
| Alias | Model ID |
|---|---|
| flash | `gemini-2.0-flash` |
| pro | `gemini-2.5-pro` |
| flash-thinking | `gemini-2.0-flash-thinking-exp` |

### Claude
| Alias | Model ID |
|---|---|
| haiku | `claude-haiku-4-5` |
| sonnet | `claude-sonnet-4-5` |
| opus | `claude-opus-4-5` |

### OpenAI / ChatGPT
| Alias | Model ID |
|---|---|
| gpt4o | `gpt-4o` |
| gpt4o-mini | `gpt-4o-mini` |
| o3 | `o3` |
| o4-mini | `o4-mini` |

The `openai` provider also works with any **OpenAI-compatible API** (Together AI, Groq, etc.) via `base_url`.

---

## Integration into Existing Projects

```python
# trading_bot/llm.py
from multi_llm_rotator import LLMRotator
from multi_llm_rotator.providers import GeminiProvider, ClaudeProvider, OpenAIProvider

_rotator = None

def get_rotator() -> LLMRotator:
    global _rotator
    if _rotator is None:
        _rotator = LLMRotator()
    return _rotator

def ask_llm(provider: str, prompt: str, system: str = "") -> str:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return get_rotator().chat(provider, msgs)
```

---

## File Structure

```
multi-llm-rotator/
  multi_llm_rotator/
    __init__.py          # Public API
    accounts.py          # Account storage (JSON)
    rotator.py           # Rotation engine + LLMRotator class
    cli.py               # mlr CLI
    providers/
      __init__.py
      gemini.py          # Google Gemini
      claude.py          # Anthropic Claude
      openai.py          # OpenAI / ChatGPT
  examples/
    basic_usage.py
    trading_bot_integration.py
  pyproject.toml
  README.md
```

---

## License

MIT
