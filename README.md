# multi-llm-rotator

> Universal multi-account rotation for **Gemini**, **Claude** and **ChatGPT** — auto-rotate between accounts on rate limits, unified interface, pluggable into any Python project.

---

## Features

- **Multi-provider** — Gemini, Claude (Anthropic), OpenAI / ChatGPT in one package
- **Multi-account per provider** — add as many accounts as you have across all providers
- **Optional providers** — use all three, just one, or any combination via `use_gemini`, `use_claude`, `use_openai` flags
- **Auto-rotation** — seamlessly switches to the next account on rate-limit (429) errors
- **3 rotation strategies** — `round-robin`, `least-used`, `random`
- **Streaming** — native streaming support for all providers
- **CLI** — manage accounts with `mlr add / remove / list / enable / disable / chat`
- **Persistent storage** — accounts saved to `~/.config/multi-llm-rotator/accounts.json`
- **Modular** — install only the provider SDKs you need
- **Drop-in** — OpenAI-style `{role, content}` message format across all providers
- **Docker-ready** — includes Dockerfile, docker-compose.yml and one-click `setup.bat`

---

## Prerequisites

Before installing, make sure the following are available on your system:

### For local Python usage

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.10+ | Required |
| **pip** | latest | `pip install --upgrade pip` |
| **API keys** | - | At least one key for your chosen provider(s) |

Get your API keys here:
- **Gemini**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **Claude**: [https://console.anthropic.com/](https://console.anthropic.com/)
- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### For Docker / docker-compose deployment

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Docker Desktop** | 4.x+ | [Download](https://www.docker.com/products/docker-desktop) |
| **Docker Compose** | v2 (built-in) | Included with Docker Desktop |
| **Windows** (for setup.bat) | Windows 10/11 | Only needed for One-Click setup |

> **Tip:** On Linux/Mac use `docker compose up --build -d` directly instead of `setup.bat`.

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

## Docker Setup (One-Click)

### Windows — One-Click via `setup.bat`

1. Clone the repo and open the folder
2. Copy `.env.example` to `.env` and fill in your API keys
3. **Double-click `setup.bat`** — it will:
   - Check that Docker Desktop is installed and running
   - Verify Docker Compose v2 is available
   - Auto-create `.env` from `.env.example` if missing (and pause for you to fill it in)
   - **Auto-detect port conflicts** — tries `8765`, then `8766`, `8767`, `8768`, `8769`, `9000`+ as fallbacks
   - Build the Docker image and start the container in detached mode
   - Print a summary with container name, port, and useful commands

```
 [1/5] Checking Docker installation...  [OK]
 [2/5] Checking Docker Compose...       [OK]
 [3/5] Checking .env file...            [OK]
 [4/5] Checking port availability...
       [SKIP] Port 8765 is already in use. Trying next...
       [OK]   Port 8766 is available -- using it.
 [5/5] Building Docker image and starting container...

 Setup complete!
   Container : multi-llm-rotator
   Port      : 8766 (host) -> 8765 (container)
   Logs      : docker logs -f multi-llm-rotator
   Stop      : docker compose down
```

### Linux / macOS

```bash
# Copy and fill in your keys
cp .env.example .env
nano .env

# Override port if 8765 is taken
LLM_PORT=8766 docker compose up --build -d

# Or use the default port
docker compose up --build -d
```

### Useful Docker commands

```bash
# View logs
docker logs -f multi-llm-rotator

# Stop the container
docker compose down

# Rebuild after code changes
docker compose up --build -d

# Check health
docker ps --filter name=multi-llm-rotator
```

---

## Quick Start

### All providers (auto-detect from .env)

```python
from dotenv import load_dotenv
from multi_llm_rotator import get_llm_service

load_dotenv()  # loads GEMINI_KEY_1, CLAUDE_KEY_1, OPENAI_KEY_1, ...

# Uses all providers whose keys are set in .env
rotator = get_llm_service()
response = rotator.chat("gemini", [{"role": "user", "content": "Hello!"}])
```

### Single provider with multiple accounts

```python
from multi_llm_rotator import get_gemini_service, get_claude_service, get_openai_service

# Gemini only (loads GEMINI_KEY_1 .. GEMINI_KEY_N from env)
rotator = get_gemini_service()

# Claude only
rotator = get_claude_service()

# OpenAI only
rotator = get_openai_service()
```

### Mix and match providers

```python
from multi_llm_rotator import get_llm_service

# Gemini + OpenAI, but NOT Claude
rotator = get_llm_service(use_gemini=True, use_openai=True, use_claude=False)

# Claude + OpenAI only
rotator = get_llm_service(use_gemini=False)

# All three (explicit)
rotator = get_llm_service(use_gemini=True, use_claude=True, use_openai=True)
```

### Manual account management

```python
from multi_llm_rotator import LLMRotator

rotator = LLMRotator()
rotator.add_account("gemini", "g1", api_key="AIza...", model="gemini-2.0-flash")
rotator.add_account("gemini", "g2", api_key="AIza...", model="gemini-2.0-flash")
rotator.add_account("claude", "c1", api_key="sk-ant-...", model="claude-opus-4-5")
rotator.add_account("openai", "o1", api_key="sk-...", model="gpt-4o")

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
|----------|----------|
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

Environment variables for `get_llm_service()` / Docker:
```
GEMINI_KEY_1=AIza...    # Account 1
GEMINI_KEY_2=AIza...    # Account 2  (add as many as you have)
CLAUDE_KEY_1=sk-ant-...
CLAUDE_KEY_2=sk-ant-...
OPENAI_KEY_1=sk-...
OPENAI_KEY_2=sk-...
LLM_PORT=8765           # Docker host port (auto-detected by setup.bat)
```

---

## Supported Models

### Gemini
| Alias | Model ID |
|-------|----------|
| flash | `gemini-2.0-flash` |
| pro | `gemini-2.5-pro` |
| flash-thinking | `gemini-2.0-flash-thinking-exp` |

### Claude
| Alias | Model ID |
|-------|----------|
| haiku | `claude-haiku-4-5` |
| sonnet | `claude-sonnet-4-5` |
| opus | `claude-opus-4-5` |

### OpenAI / ChatGPT
| Alias | Model ID |
|-------|----------|
| gpt4o | `gpt-4o` |
| gpt4o-mini | `gpt-4o-mini` |
| o3 | `o3` |
| o4-mini | `o4-mini` |

---

## Integration into Existing Projects

```python
# trading_bot/llm.py
from multi_llm_rotator import get_llm_service

_rotator = None

def get_rotator():
    global _rotator
    if _rotator is None:
        # Only Gemini + Claude, no OpenAI
        _rotator = get_llm_service(use_openai=False)
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
    __init__.py           # Public API (LLMRotator, get_llm_service, ...)
    accounts.py           # Account storage (JSON)
    rotator.py            # Rotation engine + LLMRotator class
    service.py            # get_llm_service() + per-provider shortcuts
    cli.py                # mlr CLI
    providers/
      __init__.py
      gemini.py           # Google Gemini
      claude.py           # Anthropic Claude
      openai.py           # OpenAI / ChatGPT
  examples/
    basic_usage.py
    trading_bot_integration.py
  Dockerfile              # Production Docker image
  docker-compose.yml      # Docker Compose with dynamic port
  setup.bat               # Windows one-click setup (port detection + fallback)
  .env.example            # Template for API keys
  pyproject.toml
  requirements.txt
  README.md
```

---

## License

MIT
