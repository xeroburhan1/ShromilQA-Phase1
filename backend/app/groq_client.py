"""
Thin wrapper around Groq's OpenAI-compatible chat completions endpoint.

Kept dependency-free (plain httpx) and isolated in one module so the LLM
provider can be swapped later without touching routing or storage code.
Includes automatic retries for rate limits (HTTP 429) and fallback model support.
"""
from __future__ import annotations

import asyncio
import re
import httpx
from fastapi import HTTPException

from .config import settings


class GroqError(RuntimeError):
    pass


FALLBACK_MODELS = ["openai/gpt-oss-20b", "qwen/qwen3.6-27b", "groq/compound"]


async def get_chat_completion(messages: list[dict]) -> str:
    """
    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    Returns the assistant's reply text.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Server is missing GROQ_API_KEY. Add it to backend/.env and restart.",
        )

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    models_to_try = [settings.GROQ_MODEL] + [m for m in FALLBACK_MODELS if m != settings.GROQ_MODEL]

    last_error_detail = ""

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": settings.GROQ_TEMPERATURE,
            "max_tokens": settings.GROQ_MAX_TOKENS,
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(settings.GROQ_API_URL, json=payload, headers=headers)
            except httpx.RequestError as exc:
                last_error_detail = f"Could not reach Groq API: {exc}"
                break

            if resp.status_code == 200:
                data = resp.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError) as exc:
                    raise GroqError(f"Unexpected Groq response shape: {data}") from exc

            # Handle 429 (Rate Limit) with backoff retry
            if resp.status_code == 429:
                try:
                    err_msg = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    err_msg = resp.text
                last_error_detail = f"Groq API error (429): {err_msg}"

                match = re.search(r"try again in (\d+(?:\.\d+)?)s", err_msg, re.IGNORECASE)
                wait_time = float(match.group(1)) + 0.2 if match else 2.0

                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue

            try:
                last_error_detail = f"Groq API error ({resp.status_code}): " + resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                last_error_detail = f"Groq API error ({resp.status_code}): {resp.text}"
            break

    raise HTTPException(status_code=502, detail=last_error_detail)

