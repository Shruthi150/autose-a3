"""LLM client interface wrapping Google Gemini for AutoSE agents."""
from __future__ import annotations

import os
import time
from typing import Any
from google import genai
from google.genai import types

def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required.")
    return genai.Client(api_key=api_key)

def call_gemini(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_retries: int = 3,
) -> str:
    """Call Google Gemini with retries and exponential backoff."""
    client = get_client()
    contents = f"{system_prompt}\n\n---\n\n{user_prompt}"

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                )
            )
            return response.text or ""
        except Exception as e:
            if attempt == max_retries:
                raise RuntimeError(f"Gemini API call failed after {max_retries} attempts: {e}") from e
            time.sleep(2 ** attempt)
    return ""
