"""
Centralised app configuration.

All secrets/config are read from environment variables (see .env.example).
Nothing here should ever hold a hardcoded API key.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # --- Groq API ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.4"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

    # --- App ---
    APP_NAME: str = "Shromik QA API"
    ASSISTANT_NAME: str = "Shromik QA"
    DB_PATH: Path = BASE_DIR / "data" / "sromo.db"

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")

    # How many previous turns to send back to the model as context
    MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "12"))


settings = Settings()

if not settings.GROQ_API_KEY:
    # Fail loudly and early rather than letting every chat request 500.
    import warnings

    warnings.warn(
        "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env "
        "and add your key before starting the server.",
        stacklevel=2,
    )
