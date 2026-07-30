"""
config.py
─────────
Central configuration loader for AI Job Matcher.

Reads settings from environment variables (via .env file loaded by python-dotenv).
All application code should import settings from here rather than reading os.environ directly.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env file ─────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent
load_dotenv(_ROOT / ".env", override=False)


# ── Helper ─────────────────────────────────────────────────────────────────────
def _require(key: str) -> str:
    """Return the value of a required env var; raise a clear error if missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in the value."
        )
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ── LLM Provider Configuration ─────────────────────────────────────────────────
# Supported providers: "ollama" (local), "gemini", "openai", "azure", "groq"
LLM_PROVIDER: str = _optional("LLM_PROVIDER", "ollama").lower()

# ── Local Ollama (Default for local LLM) ───────────────────────────────────────
OLLAMA_BASE_URL: str = _optional("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL: str = _optional("OLLAMA_MODEL", "llama3:latest")

# ── Google Gemini ──────────────────────────────────────────────────────────────
def get_gemini_api_key() -> str:
    """Return GEMINI_API_KEY, raising clearly if not set."""
    return _require("GEMINI_API_KEY")

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = _optional("GEMINI_MODEL", "gemini-2.0-flash-lite")

# ── OpenAI ─────────────────────────────────────────────────────────────────────
def get_openai_api_key() -> str:
    """Return OPENAI_API_KEY, raising clearly if not set."""
    return _require("OPENAI_API_KEY")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = _optional("OPENAI_MODEL", "gpt-4o-mini")

def get_openai_client():
    """Return a configured OpenAI client."""
    from openai import OpenAI

    return OpenAI(api_key=get_openai_api_key())

# ── Azure AI / Azure OpenAI ────────────────────────────────────────────────────
def get_azure_ai_api_key() -> str:
    """Return AZURE_AI_API_KEY, raising clearly if not set."""
    return _require("AZURE_AI_API_KEY")

AZURE_AI_ENDPOINT: str = os.getenv("AZURE_AI_ENDPOINT", "")
AZURE_AI_API_KEY: str = os.getenv("AZURE_AI_API_KEY", "")
AZURE_AI_MODEL: str = _optional("AZURE_AI_MODEL", "phi-4-mini-instruct")
AZURE_AI_API_VERSION: str = _optional("AZURE_AI_API_VERSION", "2024-05-01-preview")

def get_azure_openai_client():
    from openai import OpenAI

    endpoint = AZURE_AI_ENDPOINT.rstrip("/")
    if not endpoint:
        raise EnvironmentError("AZURE_AI_ENDPOINT is not set in environment.")

    if "/api/projects/" in endpoint:
        # Modern Azure AI Foundry project endpoint -> use /openai/v1 path and NO api-version
        if endpoint.endswith("/v1"):
            endpoint = endpoint[:-3].rstrip("/")
        if not endpoint.endswith("/openai/v1"):
            base_url = f"{endpoint}/openai/v1"
        else:
            base_url = endpoint

        return OpenAI(
            base_url=base_url,
            api_key=get_azure_ai_api_key(),
        )
    else:
        # Standard Azure OpenAI endpoint -> use /v1 path and require api-version
        if not endpoint.endswith("/v1"):
            base_url = f"{endpoint}/v1"
        else:
            base_url = endpoint

        return OpenAI(
            base_url=base_url,
            api_key=get_azure_ai_api_key(),
            default_query={"api-version": AZURE_AI_API_VERSION},
        )

# ── Groq ───────────────────────────────────────────────────────────────────────
def get_groq_api_key() -> str:
    """Return GROQ_API_KEY, raising clearly if not set."""
    return _require("GROQ_API_KEY")

GROQ_BASE_URL: str = _optional("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL: str = _optional("GROQ_MODEL", "llama-3.3-70b-versatile")

def get_groq_openai_client():
    from openai import OpenAI
    return OpenAI(
        base_url=GROQ_BASE_URL,
        api_key=get_groq_api_key(),
    )

# ── Job source API keys (optional — public APIs work without them) ─────────────
GREENHOUSE_API_KEY: str = _optional("GREENHOUSE_API_KEY")
LEVER_API_KEY: str = _optional("LEVER_API_KEY")

# ── App settings ───────────────────────────────────────────────────────────────
APP_ENV: str = _optional("APP_ENV", "development")
LOG_LEVEL: str = _optional("LOG_LEVEL", "INFO")
MAX_JOBS_TO_FETCH: int = int(_optional("MAX_JOBS_TO_FETCH", "100"))
TOP_MATCHES_TO_SHOW: int = int(_optional("TOP_MATCHES_TO_SHOW", "10"))

# ── Database ───────────────────────────────────────────────────────────────────
DATABASE_URL: str = _optional("DATABASE_URL", "sqlite:///./data/jobs.db")

# ── Sentence-Transformers embedding model ──────────────────────────────────────
EMBEDDING_MODEL: str = _optional("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT: Path = _ROOT
DATA_DIR: Path = _ROOT / "data"
PROMPTS_DIR: Path = _ROOT / "prompts"
UPLOADS_DIR: Path = _ROOT / "uploads"

# Ensure runtime directories exist
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
