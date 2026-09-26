"""
Agent Factory
=============
Reads .env / environment variables and returns the correct backend.

Supported AGENT_BACKEND values:
  lmstudio    → LM Studio (Prism Bonsai, Llama, Mistral, etc.)
  ollama      → Ollama local server
  bob         → IBM Bob 2.0 local API
  openai      → OpenAI cloud
  groq        → Groq cloud (fast inference)
  anthropic   → Anthropic Claude (via openai-compat proxy or direct)
  custom      → Any URL you specify in AGENT_BASE_URL
"""

import os
from dotenv import load_dotenv

from src.agent.base import AgentConfig
from src.agent.openai_compatible import OpenAICompatibleBackend

load_dotenv()

# ─── Default endpoint map ────────────────────────────────────────────────────
BACKEND_DEFAULTS = {
    "lmstudio":  {"url": "http://localhost:1234/v1",         "key": "lm-studio"},
    "ollama":    {"url": "http://localhost:11434/v1",        "key": "ollama"},
    "bob":       {"url": "http://localhost:11435/v1",        "key": "bob"},
    "openai":    {"url": "https://api.openai.com/v1",        "key": None},
    "groq":      {"url": "https://api.groq.com/openai/v1",  "key": None},
    "custom":    {"url": None,                               "key": "none"},
}


def create_agent(
    backend: str = None,
    model: str = None,
    base_url: str = None,
    api_key: str = None,
) -> OpenAICompatibleBackend:
    """
    Factory function. Falls back to .env values if args not provided.

    Quick start examples:
      create_agent("lmstudio", "prism-bonsai-27b")
      create_agent("bob",      "bob-2.0")
      create_agent("openai",   "gpt-4o")
      create_agent("ollama",   "llama3.1")
    """
    # Resolve backend
    backend = (backend or os.getenv("AGENT_BACKEND", "lmstudio")).lower()
    defaults = BACKEND_DEFAULTS.get(backend, BACKEND_DEFAULTS["custom"])

    # Resolve URL
    resolved_url = (
        base_url
        or os.getenv("AGENT_BASE_URL")
        or defaults["url"]
    )
    if not resolved_url:
        raise ValueError(
            f"No base URL found for backend '{backend}'. "
            "Set AGENT_BASE_URL in your .env file."
        )

    # Resolve model
    resolved_model = (
        model
        or os.getenv("AGENT_MODEL", "prism-bonsai-27b")
    )

    # Resolve API key
    resolved_key = (
        api_key
        or os.getenv("AGENT_API_KEY")
        or defaults.get("key")
        or "none"
    )

    config = AgentConfig(
        backend=backend,
        model=resolved_model,
        base_url=resolved_url,
        api_key=resolved_key,
        temperature=float(os.getenv("AGENT_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
        timeout=int(os.getenv("AGENT_TIMEOUT", "120")),
    )

    # All supported backends use the OpenAI-compatible adapter
    # (LM Studio, Ollama, Bob 2.0, OpenAI, Groq all speak the same protocol)
    return OpenAICompatibleBackend(config)


def list_supported_backends() -> dict:
    """Returns the list of supported backends and their default URLs."""
    return {k: v["url"] for k, v in BACKEND_DEFAULTS.items()}
