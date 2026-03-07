"""Gemini API client — wraps generation and embedding calls."""

import json
import logging

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

_configured = False


def _ensure_configured() -> None:
    global _configured
    if not _configured:
        genai.configure(api_key=settings.gemini_api_key)
        _configured = True


async def generate_json(prompt: str) -> dict | list:
    """Send a prompt to Gemini and parse the response as JSON.

    The prompt should instruct the model to return valid JSON only.
    Handles markdown code fences in the response.
    """
    _ensure_configured()
    model = genai.GenerativeModel(settings.gemini_model)
    response = await model.generate_content_async(prompt)

    text = response.text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines)

    return json.loads(text)


async def generate_text(prompt: str) -> str:
    """Send a prompt to Gemini and return raw text."""
    _ensure_configured()
    model = genai.GenerativeModel(settings.gemini_model)
    response = await model.generate_content_async(prompt)
    return response.text.strip()
